from .config_service import config_service
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from ollama import Client

llm_config = config_service.get_config()

class OpenAILLM:
    tools: list[dict] = []
    max_tokens: int = llm_config.get("openai", {}).get("max_tokens", 6140)
    client: AsyncOpenAI =  AsyncOpenAI(
        api_key=llm_config.get("openai", {}).get("api_key", ""),
    )
    api_key = llm_config.get("openai", {}).get("api_key", "")
    url = llm_config.get("openai", {}).get("url", "https://api.openai.com/v1").rstrip('/')

class AnthropicLLM:
    tools: list[dict] = []
    max_tokens: int = llm_config.get("anthropic", {}).get("max_tokens", 6140)
    client: AsyncAnthropic = AsyncAnthropic(
        api_key=llm_config.get("anthropic", {}).get("api_key", ""),
    )
    api_key = llm_config.get("anthropic", {}).get("api_key", "")
    url = llm_config.get("anthropic", {}).get("url", "https://api.anthropic.com/v1").rstrip('/')

class OllamaLLM:
    tools: list[dict] = []
    max_tokens: int = llm_config.get("ollama", {}).get("max_tokens", 6140)
    client: AsyncOpenAI = AsyncOpenAI(
        base_url = llm_config.get("ollama", {}).get("url", "http://localhost:11434").rstrip('/') + '/v1',
        api_key='ollama', # required, but unused
    )
    url = llm_config.get("ollama", {}).get("url", "http://localhost:11434").rstrip('/')
    # client: Client = Client(
    #     host='http://localhost:11434', 
    # )
    
openai_client = OpenAILLM()
anthropic_client = AnthropicLLM()
ollama_client = OllamaLLM()

def llm_reload_clients():
    global llm_config
    # refresh llm_config value
    llm_config = config_service.get_config()
    global openai_client
    global anthropic_client
    global ollama_client
    openai_client = OpenAILLM()
    anthropic_client = AnthropicLLM()
    ollama_client = OllamaLLM()
