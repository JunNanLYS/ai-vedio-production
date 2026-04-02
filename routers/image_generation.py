import json
import base64
import asyncio
from typing import Optional, List
from pathlib import Path
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel
from database import get_session
from models.api_config import ApiConfig
from models.asset import Asset
from models.project import Project
from loguru import logger
from http_client import get_http_client

router = APIRouter(prefix="/api", tags=["image-generation"])

KIE_API_KEY = "kie_api_token"
KIE_API_ENDPOINT = "kie_api_endpoint"
KIE_TASK_STATUS_ENDPOINT = "https://api.kie.ai/api/v1/jobs/recordInfo"
KIE_FILE_UPLOAD_BASE64_ENDPOINT = "https://kieai.redpandaai.co/api/file-base64-upload"
KIE_FILE_UPLOAD_STREAM_ENDPOINT = "https://kieai.redpandaai.co/api/file-stream-upload"
FILE_SIZE_THRESHOLD = 10 * 1024 * 1024


class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "nano-banana-2"
    aspect_ratio: str = "auto"
    resolution: str = "2k"
    output_format: str = "png"
    image_input: List[str] = []


class ImageGenerationResponse(BaseModel):
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result_urls: List[str] = []
    error_message: str = ""
    progress: int = 0


class DownloadRequest(BaseModel):
    image_url: str
    project_id: int = 0


class DownloadResponse(BaseModel):
    asset_id: int
    file_path: str
    file_name: str


class UploadImageRequest(BaseModel):
    file_path: str = ""
    asset_id: int = 0


class UploadImageResponse(BaseModel):
    file_url: str
    file_name: str
    file_size: int


async def get_kie_config(session: AsyncSession) -> tuple:
    token_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_KEY)
    token_config = (await session.exec(token_statement)).first()
    
    endpoint_statement = select(ApiConfig).where(ApiConfig.config_key == KIE_API_ENDPOINT)
    endpoint_config = (await session.exec(endpoint_statement)).first()
    
    if not token_config or not token_config.config_value:
        raise HTTPException(status_code=400, detail="KIE API Token 未配置，请先在设置中配置 API Token")
    
    api_token = token_config.config_value
    api_endpoint = endpoint_config.config_value if endpoint_config else "https://api.kie.ai/api/v1/jobs/createTask"
    
    return api_token, api_endpoint


async def _async_post(url: str, headers: dict, data: dict) -> dict:
    response = await get_http_client().post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


async def _async_get_json(url: str, headers: dict) -> dict:
    response = await get_http_client().get(url, headers=headers)
    response.raise_for_status()
    return response.json()


async def _async_get_bytes(url: str, headers: dict) -> bytes:
    response = await get_http_client().get(url, headers=headers)
    response.raise_for_status()
    return response.content


@router.post("/image-generation/create", response_model=ImageGenerationResponse)
async def create_image_task(
    request: ImageGenerationRequest,
    session: AsyncSession = Depends(get_session)
) -> ImageGenerationResponse:
    api_token, api_endpoint = await get_kie_config(session)
    
    payload = {
        "model": request.model,
        "input": {
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
            "resolution": request.resolution.upper(),
            "output_format": request.output_format,
            "image_input": request.image_input
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        data = await _async_post(api_endpoint, headers, payload)
        
        if data.get("code") != 200:
            logger.error(f"KIE API 返回错误: {data}")
            raise HTTPException(
                status_code=400,
                detail=f"KIE API 错误: {data.get('msg', '未知错误')}"
            )
        
        task_id = data.get("data", {}).get("taskId")
        if not task_id:
            raise HTTPException(status_code=500, detail="未获取到任务 ID")
        
        logger.info(f"创建图片生成任务成功: {task_id}")
        
        return ImageGenerationResponse(
            task_id=task_id,
            message="任务创建成功"
        )
        
    except httpx.HTTPStatusError as e:
        error_body = e.response.text
        logger.error(f"KIE API 请求失败: {e.response.status_code} - {error_body}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"KIE API 请求失败: {error_body}"
        )
    except httpx.RequestError as e:
        logger.error(f"KIE API 连接错误: {e}")
        raise HTTPException(status_code=503, detail=f"KIE API 连接失败: {str(e)}")


@router.get("/image-generation/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    session: AsyncSession = Depends(get_session)
) -> TaskStatusResponse:
    api_token, _ = await get_kie_config(session)
    
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    url = f"{KIE_TASK_STATUS_ENDPOINT}?taskId={task_id}"
    
    try:
        data = await _async_get_json(url, headers)
        
        if data.get("code") != 200:
            return TaskStatusResponse(
                task_id=task_id,
                status="error",
                error_message=data.get("msg", "获取状态失败")
            )
        
        task_data = data.get("data", {})
        state = task_data.get("state", "unknown")
        
        result_urls = []
        if state == "success":
            result_json = task_data.get("resultJson", "{}")
            try:
                result_data = json.loads(result_json)
                result_urls = result_data.get("resultUrls", [])
            except json.JSONDecodeError:
                logger.warning(f"解析结果 JSON 失败: {result_json}")
        
        progress = 0
        if state == "waiting":
            progress = 5
        elif state == "queuing":
            progress = 10
        elif state == "generating":
            progress = 50
        elif state == "success":
            progress = 100
        
        return TaskStatusResponse(
            task_id=task_id,
            status=state,
            result_urls=result_urls,
            error_message=task_data.get("failMsg") or "",
            progress=progress
        )
        
    except httpx.HTTPStatusError as e:
        error_body = e.response.text
        logger.error(f"获取任务状态失败: {e.response.status_code} - {error_body}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"获取任务状态失败: {error_body}"
        )
    except httpx.RequestError as e:
        logger.error(f"获取任务状态错误: {e}")
        raise HTTPException(status_code=503, detail=f"连接失败: {str(e)}")


@router.post("/image-generation/download", response_model=DownloadResponse)
async def download_generated_image(
    request: DownloadRequest,
    session: AsyncSession = Depends(get_session)
) -> DownloadResponse:
    import uuid
    from pathlib import Path
    from models.project import Project
    from models.asset import Asset
    
    api_token, _ = await get_kie_config(session)
    
    if request.project_id > 0:
        project_statement = select(Project).where(Project.id == request.project_id)
    else:
        project_statement = select(Project).order_by(Project.created_at.desc())
    
    project = (await session.exec(project_statement)).first()
    
    if not project:
        raise HTTPException(status_code=400, detail="没有可用的项目")
    
    images_dir = Path(project.path) / "images" / "generated"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    file_name = f"generated_{uuid.uuid4().hex[:8]}.png"
    file_path = images_dir / file_name
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        image_data = await _async_get_bytes(request.image_url, headers)
        
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        relative_path = str(file_path.relative_to(Path(project.path)))
        
        asset = Asset(
            name=file_name,
            category="image",
            sub_category="generated",
            file_path=relative_path,
            file_type="png",
            project_id=project.id
        )
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        
        logger.info(f"下载生成图片成功: {file_path} (项目: {project.name})")
        
        return DownloadResponse(
            asset_id=asset.id,
            file_path=relative_path,
            file_name=file_name
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"下载图片失败: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"下载图片失败: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"下载图片错误: {e}")
        raise HTTPException(status_code=503, detail=f"下载图片连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"下载图片错误: {e}")
        raise HTTPException(status_code=500, detail=f"下载图片失败: {str(e)}")


async def _async_upload_file_base64(api_token: str, file_path: str, upload_path: str = "reference-images") -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(path, "rb") as f:
        file_data = f.read()
    
    file_ext = path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif"
    }
    mime_type = mime_types.get(file_ext, "image/png")
    
    base64_data = base64.b64encode(file_data).decode('utf-8')
    data_url = f"data:{mime_type};base64,{base64_data}"
    
    payload = {
        "base64Data": data_url,
        "uploadPath": upload_path,
        "fileName": path.name
    }
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    response = await get_http_client().post(
        KIE_FILE_UPLOAD_BASE64_ENDPOINT,
        json=payload,
        headers=headers
    )
    response.raise_for_status()
    return response.json()


async def _async_upload_file_stream(api_token: str, file_path: str, upload_path: str = "reference-images") -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_ext = path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif"
    }
    mime_type = mime_types.get(file_ext, "image/png")
    
    with open(path, "rb") as f:
        file_data = f.read()
    
    files = {
        "file": (path.name, file_data, mime_type)
    }
    data = {
        "uploadPath": upload_path,
        "fileName": path.name
    }
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    response = await get_http_client().post(
        KIE_FILE_UPLOAD_STREAM_ENDPOINT,
        files=files,
        data=data,
        headers=headers
    )
    response.raise_for_status()
    return response.json()


async def _async_upload_file(api_token: str, file_path: str, upload_path: str = "reference-images") -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_size = path.stat().st_size
    
    if file_size < FILE_SIZE_THRESHOLD:
        logger.info(f"文件大小 {file_size / 1024 / 1024:.2f}MB < 10MB，使用 Base64 上传")
        return await _async_upload_file_base64(api_token, file_path, upload_path)
    else:
        logger.info(f"文件大小 {file_size / 1024 / 1024:.2f}MB >= 10MB，使用文件流上传")
        return await _async_upload_file_stream(api_token, file_path, upload_path)


@router.post("/image-generation/upload", response_model=UploadImageResponse)
async def upload_reference_image(
    request: UploadImageRequest,
    session: AsyncSession = Depends(get_session)
) -> UploadImageResponse:
    api_token, _ = await get_kie_config(session)
    
    file_path = request.file_path
    
    if request.asset_id > 0:
        asset_statement = select(Asset).where(Asset.id == request.asset_id)
        asset = (await session.exec(asset_statement)).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        if not asset.project_id:
            raise HTTPException(status_code=400, detail="资产未关联项目")
        
        project_statement = select(Project).where(Project.id == asset.project_id)
        project = (await session.exec(project_statement)).first()
        
        if not project:
            raise HTTPException(status_code=400, detail="资产所属项目不存在")
        
        asset_path = Path(asset.file_path)
        if not asset_path.is_absolute():
            asset_path = Path(project.path) / asset.file_path
        
        file_path = str(asset_path)
        logger.info(f"通过 asset_id={request.asset_id} 获取原图路径: {file_path} (项目: {project.name})")
    
    if not file_path:
        raise HTTPException(status_code=400, detail="请提供 file_path 或 asset_id")
    
    try:
        result = await _async_upload_file(api_token, file_path, "reference-images")
        
        if not result.get("success") and result.get("code") != 200:
            logger.error(f"上传图片失败: {result}")
            raise HTTPException(
                status_code=400,
                detail=f"上传图片失败: {result.get('msg', '未知错误')}"
            )
        
        data = result.get("data", {})
        file_url = data.get("downloadUrl") or data.get("fileUrl")
        
        if not file_url:
            raise HTTPException(status_code=500, detail="未获取到上传文件 URL")
        
        logger.info(f"上传参考图片成功: {file_url}")
        
        return UploadImageResponse(
            file_url=file_url,
            file_name=data.get("fileName", ""),
            file_size=data.get("fileSize", 0)
        )
        
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except httpx.HTTPStatusError as e:
        error_body = e.response.text
        logger.error(f"上传图片失败: {e.response.status_code} - {error_body}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"上传图片失败: {error_body}"
        )
    except httpx.RequestError as e:
        logger.error(f"上传图片连接错误: {e}")
        raise HTTPException(status_code=503, detail=f"上传图片连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"上传图片错误: {e}")
        raise HTTPException(status_code=500, detail=f"上传图片失败: {str(e)}")
