from fastapi import APIRouter, Request
from services.config_service import config_service
from services.agent_service import llm_reload_clients

router = APIRouter(prefix="/api/config")

@router.get("/exists")
async def config_exists():
    return {"exists": await config_service.exists_config()}

@router.get("")
async def get_config():
    return config_service.get_config()

@router.post("")
async def update_config(request: Request):
    data = await request.json()
    res = await config_service.update_config(data) 
    llm_reload_clients()
    return res
