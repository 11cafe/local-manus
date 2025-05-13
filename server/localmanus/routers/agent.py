import asyncio
import base64
import subprocess
import json
import os
from pathlib import Path
import traceback
from typing import Optional
from fastapi import APIRouter, Request, WebSocket, Query, HTTPException
from fastapi.responses import FileResponse
import asyncio
import aiohttp
import requests
from localmanus.services.agent_service import openai_client, anthropic_client, ollama_client
from localmanus.services.mcp import MCPClient
from localmanus.services.config_service import config_service, app_config
from starlette.websockets import WebSocketDisconnect
from localmanus.services.db_service import db_service

llm_config = config_service.get_config()

wsrouter = APIRouter()
active_websockets = {}  # Changed to dictionary to store session_id -> websocket mapping
stream_tasks = {}

@wsrouter.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = Query(...)):
    await websocket.accept()
    active_websockets[session_id] = websocket
    try:
        # Keep the connection alive
        while True:
            # Wait for messages (optional, if you need to receive from client)
            data = await websocket.receive_text()
            # Process the message if needed
    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected: {e.code}, {e.reason}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        if session_id in active_websockets:
            del active_websockets[session_id]

class ToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.name = name
        self.arguments = arguments

SYSTEM_TOOLS_MAPPING = {
    'finish': ""
}
SYSTEM_TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "finish",
                "description": "You MUST call this tool when you think the task is finished or you think you can't do anything more. Otherwise, you will be continuously asked to do more about this task indefinitely. Calling this tool will end your turn on this task and hand it over to the user for further instructions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "The reason for calling this tool"
                        }
                    }
                },
            }
        }
    ]

async def chat_openai(messages: list, session_id: str, model: str, provider: str, url: str) -> list:
    await send_to_websocket(session_id, {
        'type': 'log',
        'messages': messages
    })
    payload = {
        "model": model,
        "messages": messages,
        "tools": SYSTEM_TOOLS + openai_client.tools,
        "stream": True
    }
    url = url.rstrip("/") + "/chat/completions"
    print('start chat session', model, provider, url)
    async with aiohttp.ClientSession() as session:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {app_config.get(provider, {}).get("api_key", "")}'
        }
        async with session.post(url, json=payload, headers=headers) as response:
            combine = ''
            cur_tool_calls:list[ToolCall] = []
            content_combine = ''
            async for line in response.content:
                if session_id in stream_tasks and stream_tasks[session_id].cancelled():
                    print(f"🛑Session {session_id} cancelled during stream")
                    break
                if line:
                    # Parse the JSON response
                    try:
                        # Decode bytes to string and strip whitespace
                        line_str = line.decode('utf-8').strip()
                        if not line_str:  # Skip empty lines
                            continue
                        print('👇raw line:', line_str)
                        # Handle SSE updates
                        if line_str.startswith('data: {'):
                            line_str = line_str[6:]  # Remove "data: " prefix
                            chunk = json.loads(line_str) # Parse the JSON
                            
                            # Extract content from the choices array
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                # print('👇delta', delta)
                                content = delta.get('content', '')
                                # text delta
                                if content:
                                    content_combine += content
                                    await send_to_websocket(session_id, {
                                        'type': 'delta',
                                        'text': content
                                    })
                                # tool calls
                                tool_calls = delta.get('tool_calls', [])
                                for tool_call in tool_calls:
                                    tool_call_id = tool_call.get('id')
                                    tool_call_name = tool_call.get('function', {}).get('name')
                                    if tool_call_id and tool_call_name:
                                        # tool call start
                                        cur_tool_calls.append(ToolCall(tool_call_id, tool_call_name, ''))
                                        print('🦄tool_call', tool_call_id, tool_call_name)

                                        await send_to_websocket(session_id, {
                                            'type': 'tool_call',
                                            'id': tool_call_id,
                                            'name': tool_call_name
                                        })
                                    elif tool_call.get('function', {}).get('arguments', '') and len(cur_tool_calls) > 0:
                                        delta = tool_call.get('function', {}).get('arguments', '')
                                        cur_tool_calls[-1].arguments += delta
                                        await send_to_websocket(session_id, {
                                            'type': 'tool_call_arguments',
                                            'id': cur_tool_calls[-1].id,
                                            'text': delta # delta
                                        })
                            elif chunk.get('error'):
                                raise Exception(chunk.get('error').get('message'))

                        # Handle [DONE] marker in SSE
                        elif line_str == 'data: [DONE]':
                            continue
                        else:
                            combine += line_str
                            

                    except Exception as e:
                        traceback.print_exc()
            print('👇combine', combine)
            print('👇content_combine', content_combine)
            if content_combine != '':
                msg = {
                    'role': 'assistant',
                    'content': [{
                        'type': 'text',
                        'text': content_combine
                    }]
                }
                messages.append(msg)
                await db_service.create_message(session_id, 'assistant', json.dumps(msg))
            else:
                # empty assistant message, we think it's finished
                messages.append({
                    'role': 'assistant',
                    'tool_calls': [{
                        'type': 'function',
                        'id': 'finish',
                        'function': {
                            'name': 'finish',
                            'arguments': '{}'
                        }
                    }]
                })
            if len(cur_tool_calls) > 0:
                for tool_call in cur_tool_calls:
                    # append tool call to messages of assistant
                    print('🕹️tool_call', tool_call)
                    msg = {
                        'role': 'assistant',
                        'tool_calls': [{
                        'type': 'function',
                        'id': tool_call.id,
                        'function': {
                            'name': tool_call.name,
                            'arguments': tool_call.arguments if tool_call.arguments else '{}'
                            }
                        }]
                    }
                    messages.append(msg)
                    await db_service.create_message(session_id, 'assistant', json.dumps(msg))
                    # tool call args complete, execute tool call
                    tool_result = await execute_tool(tool_call.id, tool_call.name, tool_call.arguments, session_id)
                    # append tool call result to messages of user
                    if tool_result is not None:
                        for r in tool_result:
                            messages.append(r)
                    await send_to_websocket(session_id, {
                        'type': 'all_messages',
                        'messages': messages
                    })
            # Has Error
            if combine != '':
                    data = None
                    try:
                        data = json.loads(combine)
                    except Exception as e:
                        pass
                    if data and data.get('error') and data.get('error').get('message'):
                        if data['error'].get('code') == 'rate_limit_error':
                            print('👇rate_limit_error, sleeping 10 seconds')
                            await send_to_websocket(session_id, {
                                'type': 'info', 
                                'info': f'Hit rate limit, waiting 10 seconds before continue. {data.get("error").get("message")} Please wait for 10 seconds...'
                            })
                            await asyncio.sleep(10)
                        else:
                            raise Exception(data.get('error').get('message'))
                    else:
                        # alert info
                        await send_to_websocket(session_id, {
                            'type': 'info', 
                            'info': combine
                        })
    return messages

def detect_image_type_from_base64(b64_data: str) -> str:
    # Only take the base64 part, not the "data:image/...," prefix
    if b64_data.startswith("data:"):
        b64_data = b64_data.split(",", 1)[1]

    # Decode just the first few bytes
    prefix_bytes = base64.b64decode(b64_data[:24])  # ~18 bytes is enough

    if prefix_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif prefix_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif prefix_bytes.startswith(b"GIF87a") or prefix_bytes.startswith(b"GIF89a"):
        return "image/gif"
    elif prefix_bytes.startswith(b"RIFF") and b"WEBP" in prefix_bytes:
        return "image/webp"
    else:
        return "application/octet-stream"

async def execute_tool(tool_call_id: str, tool_name: str, args_str: str, session_id: str):
    res = []
    try:
        if tool_name in SYSTEM_TOOLS_MAPPING:
            return res
        args_json = {}
        try:
            args_json = json.loads(args_str)
        except Exception as e:
            pass
        print('🦄executing tool', tool_name, args_json)
        mcp_client = mcp_tool_to_server_mapping[tool_name]
        if mcp_client.session is None:
            raise Exception(f"MCP client not found for tool {tool_name}")
        result = await mcp_client.session.call_tool(tool_name, args_json)
        content_dict = [content.model_dump() for content in result.content]
        await send_to_websocket(session_id, {
            'type': 'tool_call_result',
            'id': tool_call_id,
            'content': content_dict
        })

        text_contents = [c.text if c.type == 'text' else "Image result, view user attached image below for detailed result" if c.type == 'image' else json.dumps(c.model_dump()) for c in result.content ]
        text_contents = ''.join(text_contents)
        print('👇tool result text_content length', len(text_contents))
        if len(text_contents) > 10000:
            text_contents = text_contents[:10000] + "...Content truncated to 10000 characters due to length limit"

        res.append({
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'content': text_contents # here only accept text string in anthropic, otherwise will throw error
        })
        for content in result.content:
            if content.type == 'image':
                image_type = detect_image_type_from_base64(content.data)
                res.append({
                    'role': 'user',
                    # 'is_tool': True,
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{content.data}",
                            },
                        },
                    ],
                })
        return res

    except Exception as e:
        print(f"Error calling tool {tool_name}: {e}")
        traceback.print_exc()
        await send_to_websocket(session_id, {
            'type': 'error',
            'error': f'Error calling tool {tool_name} with inputs {args_str} - {e}'
        })
    return res


router = APIRouter(prefix="/api")
@router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    messages = data.get('messages')
    session_id = data.get('session_id')
    provider = data.get('provider')
    url = data.get('url')
    if provider == 'ollama' and not url.endswith('/v1'):
        # openai compatible url
        url = url.rstrip("/") + "/v1"
    model = data.get('model')
    if model is None:
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="model is required"
        )
    if provider is None:
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="provider is required"
        )
    if session_id is None:
        raise HTTPException(
            status_code=400,  # Bad Request
            detail="session_id is required"
        )
    if len(messages) == 1:
        # create new session
        prompt = messages[0].get('content', '')
        await db_service.create_chat_session(session_id, model, provider, prompt if isinstance(prompt, str) else '')
    # Create and store the chat task
    async def chat_loop():
        cur_messages = messages
        # while True:
        while True:
            try:
                if cur_messages[-1].get('role') == 'assistant' and cur_messages[-1].get('tool_calls') and \
                cur_messages[-1]['tool_calls'][-1].get('function', {}).get('name') == 'finish':
                    print('👇finish!')
                    cur_messages.pop()
                    await send_to_websocket(session_id, {
                        'type': 'all_messages', 
                        'messages': cur_messages
                    })
                    break
                else:
                    cur_messages = await chat_openai(cur_messages, session_id, model, provider, url)
            except Exception as e:
                print(f"Error in chat_loop: {e}")
                traceback.print_exc()
                await send_to_websocket(session_id, {
                    'type': 'error',
                    'error': str(e)
                })
                break
        await send_to_websocket(session_id, {
            'type': 'done'
        })

    task = asyncio.create_task(chat_loop())
    stream_tasks[session_id] = task
    try:
        await task
    except asyncio.exceptions.CancelledError:
        print(f"🛑Session {session_id} cancelled during stream")
    finally:
        stream_tasks.pop(session_id, None)

    return {"status": "done"}

async def send_to_websocket(session_id: str, event:dict):
    ws = active_websockets.get(session_id)
    if ws:
        try:
            await ws.send_text(json.dumps(event))
        except Exception as e:
            print(f"Error sending to websocket: {e}")
            traceback.print_exc()

@router.post("/cancel/{session_id}")
async def cancel_chat(session_id: str):
    task = stream_tasks.get(session_id)
    if task and not task.done():
        task.cancel()
        return {"status": "cancelled"}
    return {"status": "not_found_or_done"}

# @router.get("/workspace_list")
# async def workspace_list():
#     return [{"name": entry.name, "is_dir": entry.is_dir(), "path": str(entry)} for entry in Path(WORKSPACE_ROOT).iterdir()]

@router.get("/workspace_download")
async def workspace_download(path: str):
    file_path = Path(path)
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return {"error": "File not found"}

def get_ollama_model_list():
    base_url = config_service.get_config().get('ollama', {}).get('url', os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
    try:
        response = requests.get(f'{base_url}/api/tags', timeout=5)
        response.raise_for_status()
        data = response.json()
        return [model['name'] for model in data.get('models', [])]
    except requests.RequestException as e:
        print(f"Error querying Ollama: {e}")
        return []

@router.get("/list_models")
async def get_models():
    config = app_config
    res = []
    ollama_models = get_ollama_model_list()
    ollama_url = config_service.get_config().get('ollama', {}).get('url', os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
    print('👇ollama_models', ollama_models)
    for ollama_model in ollama_models:
        res.append({
            'provider': 'ollama',
            'model': ollama_model,
            'url': ollama_url
        })
    for provider in config.keys():
        models = config[provider].get('models', [])
        for model in models:
            if provider != 'ollama' and config[provider].get('api_key', '') == '':
                continue
            res.append({
                'provider': provider,
                'model': model,
                'url': config[provider].get('url', '')
            })
    return res

USER_DATA_DIR = os.getenv("USER_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "user_data"))

mcp_clients: dict[str, MCPClient] = {}
mcp_clients_status = {}
mcp_tool_to_server_mapping: dict[str, MCPClient] = {}

async def initialize():
    await initialize_mcp()
    for session_id in active_websockets:
        await send_to_websocket(session_id, {
            'type': 'init_done'
        })

async def initialize_mcp():
    print('👇initializing mcp')
    mcp_config_path = os.path.join(USER_DATA_DIR, "mcp.json")
    if not os.path.exists(mcp_config_path):
        return {}
    with open(mcp_config_path, "r") as f:
        json_data = json.load(f)
    global mcp_clients
    global mcp_clients_status
    global mcp_tool_to_server_mapping
    mcp_clients_json: dict[str, dict] = json_data.get('mcpServers', {})
    
    for server_name, server in list(mcp_clients_json.items()):
        if server.get('command') is None:
            continue
        if server.get('args') is None:
            server['args'] = []
        
        mcp_client = MCPClient()
        mcp_clients_status[server_name] = {
            'status': 'initializing'
        }
        try:
            await mcp_client.connect_to_server(server["command"], server["args"], server.get('env'))
            mcp_clients_status[server_name] = {
                'status': 'connected',
                'tools': mcp_client.tools
            }
            print('👇mcp_client connected', server_name, 'tools', len(mcp_client.tools))
            for tool in mcp_client.tools:
                mcp_tool_to_server_mapping[tool['name']] = mcp_client
                print('tool', tool)
                openai_client.tools.append({
                    'type': 'function',
                    'function': {
                        'name': tool['name'],
                        'description': tool['description'],
                        'parameters': tool['input_schema']
                    }
                })
                anthropic_client.tools.append(tool)
                ollama_client.tools.append({
                    'type': 'function',
                    'function': {
                        'name': tool['name'],
                        'description': tool['description'],
                        'parameters': tool['input_schema']
                    }
                })

            mcp_clients[server_name] = mcp_client
        except Exception as e:
            print(f"Error connecting to MCP server {server_name}: {e}")
            traceback.print_exc()
            mcp_clients_status[server_name] = {
                'status': 'error',
                'error': str(e)
            }

@router.get("/list_mcp_servers")
async def list_mcp_servers():
    if mcp_clients is None:
        return {}
    mcp_config_path = os.path.join(USER_DATA_DIR, "mcp.json")
    if not os.path.exists(mcp_config_path):
        return {}
    with open(mcp_config_path, "r") as f:
        json_data = json.load(f)
    mcp_servers = json_data.get('mcpServers', {})
    for server_name, server in mcp_servers.items():
        mcp_servers[server_name]['tools'] = mcp_clients_status[server_name].get('tools', [])
        mcp_servers[server_name]['status'] = mcp_clients_status[server_name].get('status', 'error')
    return mcp_servers

@router.get("/list_chat_sessions")
async def list_chat_sessions():
    return await db_service.list_sessions()

@router.get("/get_chat_history")
async def get_chat_history(session_id: str):
    return await db_service.get_chat_history(session_id)

