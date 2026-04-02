import json
import urllib.request
import urllib.error
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel
from database import get_session
from models.api_config import ApiConfig
from loguru import logger
from cache import cache_manager, clear_cache

router = APIRouter(prefix="/api", tags=["settings"])

KIE_API_KEY = "kie_api_token"
KIE_API_ENDPOINT = "kie_api_endpoint"

_executor = ThreadPoolExecutor(max_workers=4)


class KieConfigRequest(BaseModel):
    api_token: str
    api_endpoint: Optional[str] = "https://api.kie.ai/api/v1/jobs/createTask"


class KieConfigResponse(BaseModel):
    api_token: str
    api_endpoint: str
    is_configured: bool


class ApiConfigResponse(BaseModel):
    id: int
    config_key: str
    config_value: str
    description: Optional[str]
    created_at: str
    updated_at: str


@router.get("/settings/kie", response_model=KieConfigResponse)
async def get_kie_config(session: AsyncSession = Depends(get_session)) -> KieConfigResponse:
    cache_key_token = f"kie_config:{KIE_API_KEY}"
    cache_key_endpoint = f"kie_config:{KIE_API_ENDPOINT}"
    
    cached_token = cache_manager.get(cache_key_token)
    cached_endpoint = cache_manager.get(cache_key_endpoint)
    
    if cached_token is not None and cached_endpoint is not None:
        return KieConfigResponse(
            api_token=cached_token,
            api_endpoint=cached_endpoint,
            is_configured=bool(cached_token)
        )
    
    token_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_KEY)
    token_config = (await session.exec(token_statement)).first()
    
    endpoint_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_ENDPOINT)
    endpoint_config = (await session.exec(endpoint_statement)).first()
    
    api_token = token_config.config_value if token_config else ""
    api_endpoint = endpoint_config.config_value if endpoint_config else "https://api.kie.ai/api/v1/jobs/createTask"
    
    cache_manager.set(cache_key_token, api_token)
    cache_manager.set(cache_key_endpoint, api_endpoint)
    
    return KieConfigResponse(
        api_token=api_token,
        api_endpoint=api_endpoint,
        is_configured=bool(api_token)
    )


@router.post("/settings/kie")
async def save_kie_config(
    config_data: KieConfigRequest,
    session: AsyncSession = Depends(get_session)
) -> dict:
    token_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_KEY)
    token_config = (await session.exec(token_statement)).first()
    
    if token_config:
        token_config.config_value = config_data.api_token
        token_config.updated_at = datetime.utcnow()
        session.add(token_config)
    else:
        token_config = ApiConfig(
            config_key=KIE_API_KEY,
            config_value=config_data.api_token,
            description="KIE API Token"
        )
        session.add(token_config)
    
    endpoint_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_ENDPOINT)
    endpoint_config = (await session.exec(endpoint_statement)).first()
    
    if endpoint_config:
        endpoint_config.config_value = config_data.api_endpoint
        endpoint_config.updated_at = datetime.utcnow()
        session.add(endpoint_config)
    else:
        endpoint_config = ApiConfig(
            config_key=KIE_API_ENDPOINT,
            config_value=config_data.api_endpoint,
            description="KIE API Endpoint"
        )
        session.add(endpoint_config)
    
    await session.commit()
    
    clear_cache("kie_config:*")
    logger.info("KIE API 配置已保存")
    
    return {"message": "配置保存成功"}


@router.delete("/settings/kie")
async def delete_kie_config(session: AsyncSession = Depends(get_session)) -> dict:
    token_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_KEY)
    token_config = (await session.exec(token_statement)).first()
    
    if token_config:
        await session.delete(token_config)
    
    endpoint_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_ENDPOINT)
    endpoint_config = (await session.exec(endpoint_statement)).first()
    
    if endpoint_config:
        await session.delete(endpoint_config)
    
    await session.commit()
    
    clear_cache("kie_config:*")
    logger.info("KIE API 配置已删除")
    
    return {"message": "配置已删除"}


def _sync_test_api(url: str, headers: dict, data: dict, timeout: float = 30.0) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


@router.post("/settings/kie/test")
async def test_kie_config(session: AsyncSession = Depends(get_session)) -> dict:
    token_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_KEY)
    token_config = (await session.exec(token_statement)).first()
    
    endpoint_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_ENDPOINT)
    endpoint_config = (await session.exec(endpoint_statement)).first()
    
    if not token_config or not token_config.config_value:
        raise HTTPException(status_code=400, detail="KIE API Token 未配置")
    
    api_token = token_config.config_value
    api_endpoint = endpoint_config.config_value if endpoint_config else "https://api.kie.ai/api/v1/jobs/createTask"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "nano-banana-2",
        "input": {
            "prompt": "test",
            "aspect_ratio": "1:1",
            "resolution": "1K",
            "output_format": "jpg",
            "image_input": []
        }
    }
    
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            _executor,
            lambda: _sync_test_api(api_endpoint, headers, payload, 30.0)
        )
        
        if data.get("code") == 200:
            return {"success": True, "message": "API 连接成功"}
        else:
            return {"success": False, "message": f"API 返回错误: {data.get('msg', '未知错误')}"}
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"success": False, "message": "API Token 无效"}
        else:
            return {"success": False, "message": f"API 请求失败: HTTP {e.code}"}
    except urllib.error.URLError as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
    except asyncio.TimeoutError:
        return {"success": False, "message": "API 请求超时"}
    except Exception as e:
        logger.error(f"测试 KIE API 失败: {e}")
        return {"success": False, "message": f"连接失败: {str(e)}"}
