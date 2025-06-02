import base64
from fastapi.responses import FileResponse
import requests
from services.config_service import app_config
import traceback
import time
from services.config_service import USER_DATA_DIR, FILES_DIR
from routers.websocket import send_to_websocket
from PIL import Image
from io import BytesIO
import os
from nanoid import generate
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
import httpx
import aiofiles
from mimetypes import guess_type

router = APIRouter(prefix="/api")

os.makedirs(FILES_DIR, exist_ok=True)

def generate_file_id():
    return 'im_' + generate(size=8)

@router.post("/upload_image")
async def upload_image(session_id: str = Form(...), file: UploadFile = File(...)):
    print('🦄upload_image session_id', session_id)
    print('🦄upload_image file', file.filename)
    file_id = generate_file_id()
    filename = file.filename or ''

    # Determine the file extension
    mime_type, _ = guess_type(filename)
    extension = mime_type.split('/')[-1] if mime_type else ''  # default to 'bin' if unknown

    file_path = os.path.join(FILES_DIR, f'{file_id}.{extension}')
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()  # Read the file content
        await f.write(content)
    print('🦄upload_image file_path', file_path)
    return {
        'file_id': f'{file_id}.{extension}',
    }

@router.get("/file/{file_id}")
async def get_file(file_id: str):
    file_path = os.path.join(FILES_DIR, f'{file_id}')
    print('🦄get_file file_path', file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

async def generate_image(args_json: dict, ctx: dict):
    session_id = ctx.get('session_id', '')
    image_model = ctx.get('model_info', {}).get('image', {})
    if image_model is None:
        raise ValueError("Image model is not selected")
    model = image_model.get('model', '')
    provider = image_model.get('provider', 'replicate')
    prompt: str = args_json.get('prompt', '')
    aspect_ratio: str = args_json.get('aspect_ratio', '1:1')
    input_image: str = args_json.get('input_image', '')
    
    if prompt == '':
        raise ValueError("Image generation failed: text prompt is required")
    if model == '':
        raise ValueError("Image generation failed: model is not selected")

    if input_image:
        # hardcode kontext model for image editing for now
        model = 'black-forest-labs/flux-kontext-pro'
        image_path = os.path.join(FILES_DIR, f'{input_image}')
        async with aiofiles.open(image_path, 'rb') as f:
            image_data = await f.read()
        b64 = base64.b64encode(image_data).decode('utf-8')

        mime_type, _ = guess_type(image_path)
        if not mime_type:
            mime_type = "image/png"  # default fallback
        input_image = f"data:{mime_type};base64,{b64}"
    mime_type, width, height, filename = await generate_image_replicate(prompt, model, aspect_ratio, input_image)
    await send_to_websocket(session_id, {
        'type': 'image_generated',
        'image_data': {
            'mime_type': mime_type,
            'url': f'/api/file/{filename}',
            'width': width,
            'height': height,
        }
    })
    return [
        {
            'role': 'tool',
            'content': f'Image generation successful: ![image filename: {filename}](/api/file/{filename})',
        }
    ]
async def generate_image_replicate(prompt, model, aspect_ratio, input_image):
    api_key = app_config.get('replicate', {}).get('api_key', '')
    if not api_key:
        raise ValueError("Image generation failed: Replicate API key is not set")
    url = f"https://api.replicate.com/v1/models/{model}/predictions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }
    data = {
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }
    }
    if input_image:
        data['input']['input_image'] = input_image
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, headers=headers, json=data)
    res = response.json()
    print('🦄image generation response', res)
    output = res.get('output', '')
    image_id = 'im_' + generate(size=8)
    # image_id = int(time.time() * 1000)
    if output == '':
        if res.get('detail', '') != '':
            raise Exception(f'Replicate image generation failed: {res.get("detail", "")}')
        else:
            raise Exception('Replicate image generation failed: no output url found')
    print('🦄image generation image_id', image_id)
    # get image dimensions
    mime_type, width, height, extension = await get_image_info_and_save(output, os.path.join(FILES_DIR, f'{image_id}'))
    filename = f'{image_id}.{extension}'
    return mime_type, width, height, filename

async def generate_image_huggingface(args_json: dict, ctx: dict):
    from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image
    import torch

    pipe_txt2img = AutoPipelineForText2Image.from_pretrained(
        "dreamlike-art/dreamlike-photoreal-2.0", torch_dtype=torch.float16, use_safetensors=True
    ).to("cuda")

    prompt = "cinematic photo of Godzilla eating sushi with a cat in a izakaya, 35mm photograph, film, professional, 4k, highly detailed"
    generator = torch.Generator(device="cpu").manual_seed(37)
    image = pipe_txt2img(prompt, generator=generator).images[0]

async def get_image_info_and_save(url, file_path_without_extension):
    # Fetch the image asynchronously
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Open the image
    image = Image.open(BytesIO(response.content))

    # Get MIME type
    mime_type = Image.MIME.get(image.format if image.format else 'PNG')

    # Get dimensions
    width, height = image.size

    # Determine the file extension
    extension = image.format.lower() if image.format else 'png'
    file_path = f"{file_path_without_extension}.{extension}"

    # Save the image to a local file with the correct extension asynchronously
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(response.content)
    print('🦄image saved to file_path', file_path)

    return mime_type, width, height, extension

        
