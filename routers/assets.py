import os
import shutil
import hashlib
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from pydantic import BaseModel

import cv2
from database import get_session
from models import Asset, Project, SubCategory
from loguru import logger
from PIL import Image

router = APIRouter(prefix="/api", tags=["assets"])

PROJECTS_DIR = Path(__file__).parent.parent / "projects"
CURRENT_PROJECT_FILE = Path(__file__).parent.parent / "current_project.txt"
PREVIEW_CACHE_DIR = Path(__file__).parent.parent / "preview_cache"

PREVIEW_SIZE = (256, 256)

ALLOWED_EXTENSIONS = {
    "prompt": [".txt", ".md", ".json"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
    "audio": [".mp3", ".wav", ".ogg", ".m4a", ".flac"],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "document": [".ppt", ".pptx", ".doc", ".docx", ".pdf"]
}

CATEGORY_DIRS = {
    "prompt": "prompts",
    "image": "images",
    "audio": "audios",
    "video": "videos",
    "document": "documents"
}

DEFAULT_SUBCATEGORIES = {
    "prompt": [{"id": "script", "name": "脚本"}],
    "image": [{"id": "background", "name": "背景"}],
    "audio": [{"id": "bgm", "name": "BGM"}],
    "video": [{"id": "intro", "name": "片头"}],
    "document": [
        {"id": "ppt", "name": "PPT"},
        {"id": "word", "name": "Word"},
        {"id": "pdf", "name": "PDF"}
    ]
}


class AssetCreate(BaseModel):
    """创建资产的请求数据"""
    name: str
    category: str
    sub_category: str
    file_path: str
    file_type: str
    project_id: Optional[int] = None


class SubCategoryCreate(BaseModel):
    """创建子分类的请求数据"""
    category: str
    name: str
    project_id: Optional[int] = None


class ProjectCreate(BaseModel):
    """创建项目的请求数据"""
    project_name: str
    project_path: Optional[str] = None


class LoadProjectRequest(BaseModel):
    """加载项目的请求数据"""
    project_path: str


class UploadResponse(BaseModel):
    """上传文件响应数据"""
    file_path: str
    message: str


def ensure_projects_dir():
    """确保项目目录存在"""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def validate_file_extension(category: str, file_extension: str) -> bool:
    """验证文件扩展名是否匹配类别"""
    allowed = ALLOWED_EXTENSIONS.get(category, [])
    return file_extension.lower() in allowed


def get_current_project_id() -> Optional[int]:
    """获取当前项目ID"""
    if CURRENT_PROJECT_FILE.exists():
        try:
            return int(CURRENT_PROJECT_FILE.read_text().strip())
        except:
            return None
    return None


def set_current_project_id(project_id: int):
    """设置当前项目ID"""
    CURRENT_PROJECT_FILE.write_text(str(project_id))


# ==================== 项目管理 API ====================

@router.get("/projects")
def get_projects(session: Session = Depends(get_session)) -> List[Project]:
    """获取所有项目列表"""
    statement = select(Project).order_by(Project.created_at.desc())
    projects = session.exec(statement).all()
    logger.info(f"获取项目列表，共 {len(projects)} 个")
    return projects


@router.post("/projects")
def create_project(
    project_data: ProjectCreate,
    session: Session = Depends(get_session)
) -> Project:
    """创建新项目"""
    safe_project_name = project_data.project_name.replace("..", "").replace("/", "_").replace("\\", "_")
    
    if project_data.project_path:
        base_path = Path(project_data.project_path)
    else:
        ensure_projects_dir()
        base_path = PROJECTS_DIR
    
    project_path = base_path / safe_project_name
    
    if project_path.exists():
        logger.warning(f"项目目录已存在: {project_path}")
        raise HTTPException(status_code=400, detail="项目目录已存在")
    
    project_path.mkdir(parents=True, exist_ok=True)
    
    for category_dir_name in CATEGORY_DIRS.values():
        (project_path / category_dir_name).mkdir(exist_ok=True)
    
    project = Project(
        name=safe_project_name,
        path=str(project_path)
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    for category, subcats in DEFAULT_SUBCATEGORIES.items():
        for subcat in subcats:
            sub_category = SubCategory(
                category=category,
                name=subcat["name"],
                project_id=project.id
            )
            session.add(sub_category)
    session.commit()
    
    set_current_project_id(project.id)
    
    logger.info(f"创建项目: {project.name}, ID: {project.id}")
    return project


@router.get("/projects/current")
def get_current_project(session: Session = Depends(get_session)) -> dict:
    """获取当前项目"""
    project_id = get_current_project_id()
    if not project_id:
        return {"project": None}
    
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()
    
    if not project:
        return {"project": None}
    
    return {"project": project}


@router.post("/projects/switch/{project_id}")
def switch_project(project_id: int, session: Session = Depends(get_session)) -> dict:
    """切换当前项目"""
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    set_current_project_id(project_id)
    logger.info(f"切换到项目: {project.name}")
    return {"message": "切换成功", "project": project}


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)) -> dict:
    """删除项目"""
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    project_path = Path(project.path)
    if project_path.exists():
        shutil.rmtree(project_path)
    
    subcat_statement = select(SubCategory).where(SubCategory.project_id == project_id)
    subcats = session.exec(subcat_statement).all()
    for subcat in subcats:
        session.delete(subcat)
    
    session.delete(project)
    session.commit()
    
    if get_current_project_id() == project_id:
        CURRENT_PROJECT_FILE.unlink(missing_ok=True)
    
    logger.info(f"删除项目: {project.name}")
    return {"message": "项目已删除"}


@router.post("/projects/load")
def load_project(
    data: LoadProjectRequest,
    session: Session = Depends(get_session)
) -> dict:
    """加载已有项目目录"""
    project_path = Path(data.project_path)
    
    if not project_path.exists():
        raise HTTPException(status_code=400, detail="项目目录不存在")
    
    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail="指定路径不是目录")
    
    existing_statement = select(Project).where(Project.path == str(project_path))
    existing_project = session.exec(existing_statement).first()
    if existing_project:
        raise HTTPException(
            status_code=400, 
            detail=f"项目已存在，名称: {existing_project.name}"
        )
    
    project_name = project_path.name
    
    for category_dir_name in CATEGORY_DIRS.values():
        category_dir = project_path / category_dir_name
        if not category_dir.exists():
            category_dir.mkdir(exist_ok=True)
    
    project = Project(
        name=project_name,
        path=str(project_path)
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    
    for category, subcats in DEFAULT_SUBCATEGORIES.items():
        for subcat in subcats:
            existing_subcat = session.exec(
                select(SubCategory).where(
                    SubCategory.category == category,
                    SubCategory.name == subcat["name"],
                    SubCategory.project_id == project.id
                )
            ).first()
            if not existing_subcat:
                sub_category = SubCategory(
                    category=category,
                    name=subcat["name"],
                    project_id=project.id
                )
                session.add(sub_category)
    session.commit()
    
    loaded_assets = scan_and_import_assets(project, session)
    
    set_current_project_id(project.id)
    
    logger.info(f"加载项目: {project.name}, 导入资产: {loaded_assets} 个")
    return {
        "message": "项目加载成功",
        "project": project,
        "loaded_assets": loaded_assets
    }


def scan_and_import_assets(project: Project, session: Session) -> int:
    """扫描项目目录并导入资产"""
    project_path = Path(project.path)
    loaded_count = 0
    
    for category, dir_name in CATEGORY_DIRS.items():
        category_path = project_path / dir_name
        if not category_path.exists():
            continue
        
        allowed_exts = ALLOWED_EXTENSIONS.get(category, [])
        
        for file_path in category_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            file_ext = file_path.suffix.lower()
            if file_ext not in allowed_exts:
                continue
            
            relative_path = str(file_path.relative_to(project_path))
            
            existing = session.exec(
                select(Asset).where(
                    Asset.project_id == project.id,
                    Asset.file_path == relative_path
                )
            ).first()
            if existing:
                continue
            
            parent_dir = file_path.parent.name
            category_dir_name = CATEGORY_DIRS[category]
            sub_category = parent_dir if parent_dir != category_dir_name else ""
            
            if sub_category:
                existing_subcat = session.exec(
                    select(SubCategory).where(
                        SubCategory.category == category,
                        SubCategory.name == sub_category,
                        SubCategory.project_id == project.id
                    )
                ).first()
                if not existing_subcat:
                    new_subcat = SubCategory(
                        category=category,
                        name=sub_category,
                        project_id=project.id
                    )
                    session.add(new_subcat)
            
            asset = Asset(
                name=file_path.name,
                category=category,
                sub_category=sub_category,
                file_path=relative_path,
                file_type=file_ext.lstrip("."),
                project_id=project.id
            )
            session.add(asset)
            loaded_count += 1
    
    if loaded_count > 0:
        session.commit()
    
    return loaded_count


# ==================== 子分类管理 API ====================

@router.get("/subcategories")
def get_subcategories(
    category: Optional[str] = None,
    project_id: Optional[int] = None,
    session: Session = Depends(get_session)
) -> List[SubCategory]:
    """获取子分类列表，自动补充缺失的默认子分类"""
    effective_project_id = project_id or get_current_project_id()
    
    if not effective_project_id:
        return []
    
    statement = select(SubCategory).where(SubCategory.project_id == effective_project_id)
    
    if category:
        statement = statement.where(SubCategory.category == category)
    
    subcategories = session.exec(statement).all()
    
    categories_to_check = [category] if category else list(DEFAULT_SUBCATEGORIES.keys())
    
    for cat in categories_to_check:
        existing_names = {sc.name for sc in subcategories if sc.category == cat}
        default_subcats = DEFAULT_SUBCATEGORIES.get(cat, [])
        
        for default_subcat in default_subcats:
            if default_subcat["name"] not in existing_names:
                new_subcat = SubCategory(
                    category=cat,
                    name=default_subcat["name"],
                    project_id=effective_project_id
                )
                session.add(new_subcat)
    
    session.commit()
    
    statement = select(SubCategory).where(SubCategory.project_id == effective_project_id)
    if category:
        statement = statement.where(SubCategory.category == category)
    subcategories = session.exec(statement).all()
    
    return subcategories


@router.post("/subcategories")
def create_subcategory(
    data: SubCategoryCreate,
    session: Session = Depends(get_session)
) -> SubCategory:
    """创建子分类"""
    if data.category not in CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"无效的资产类别，允许的类别: {list(CATEGORY_DIRS.keys())}")
    
    project_id = data.project_id or get_current_project_id()
    
    statement = select(SubCategory).where(
        SubCategory.category == data.category,
        SubCategory.name == data.name,
        SubCategory.project_id == project_id
    )
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="该子分类已存在")
    
    subcategory = SubCategory(
        category=data.category,
        name=data.name,
        project_id=project_id
    )
    session.add(subcategory)
    session.commit()
    session.refresh(subcategory)
    
    if project_id:
        project_statement = select(Project).where(Project.id == project_id)
        project = session.exec(project_statement).first()
        if project:
            category_dir_name = CATEGORY_DIRS[data.category]
            category_path = Path(project.path) / category_dir_name / data.name
            category_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"创建子分类: {data.name} ({data.category})")
    return subcategory


@router.delete("/subcategories/{subcategory_id}")
def delete_subcategory(subcategory_id: int, session: Session = Depends(get_session)) -> dict:
    """删除子分类"""
    statement = select(SubCategory).where(SubCategory.id == subcategory_id)
    subcategory = session.exec(statement).first()
    
    if not subcategory:
        raise HTTPException(status_code=404, detail="子分类不存在")
    
    session.delete(subcategory)
    session.commit()
    
    logger.info(f"删除子分类: {subcategory.name}")
    return {"message": "子分类已删除"}


# ==================== 资产管理 API ====================

@router.get("/assets")
def get_assets(
    category: Optional[str] = None,
    project_id: Optional[int] = None,
    session: Session = Depends(get_session)
) -> List[Asset]:
    """获取资产列表"""
    effective_project_id = project_id or get_current_project_id()
    
    if not effective_project_id:
        return []
    
    statement = select(Asset).where(Asset.project_id == effective_project_id)
    
    if category:
        statement = statement.where(Asset.category == category)
    
    assets = session.exec(statement).all()
    return assets


@router.post("/assets")
def create_asset(
    asset_data: AssetCreate,
    session: Session = Depends(get_session)
) -> Asset:
    """创建资产记录"""
    logger.info(f"创建资产请求: {asset_data}")
    if asset_data.category not in CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"无效的资产类别，允许的类别: {list(CATEGORY_DIRS.keys())}")
    
    project_id = asset_data.project_id or get_current_project_id()
    
    asset = Asset(
        name=asset_data.name,
        category=asset_data.category,
        sub_category=asset_data.sub_category,
        file_path=asset_data.file_path,
        file_type=asset_data.file_type,
        project_id=project_id
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    logger.info(f"创建资产记录: {asset.name}, ID: {asset.id}")
    return asset


@router.post("/assets/upload", response_model=UploadResponse)
async def upload_asset(
    file: UploadFile = File(...),
    category: str = Form(...),
    sub_category: str = Form(...),
    project_id: Optional[int] = Form(None),
    session: Session = Depends(get_session)
) -> UploadResponse:
    """上传资产文件"""
    if category not in CATEGORY_DIRS:
        raise HTTPException(status_code=400, detail=f"无效的资产类别，允许的类别: {list(CATEGORY_DIRS.keys())}")
    
    file_extension = Path(file.filename).suffix
    if not validate_file_extension(category, file_extension):
        allowed = ALLOWED_EXTENSIONS.get(category, [])
        raise HTTPException(
            status_code=400, 
            detail=f"文件类型不匹配，类别 {category} 允许的扩展名: {allowed}"
        )
    
    effective_project_id = project_id or get_current_project_id()
    
    if effective_project_id:
        project_statement = select(Project).where(Project.id == effective_project_id)
        project = session.exec(project_statement).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        base_path = Path(project.path)
    else:
        ensure_projects_dir()
        base_path = PROJECTS_DIR / "assets"
    
    category_dir_name = CATEGORY_DIRS[category]
    target_dir = base_path / category_dir_name / sub_category
    target_dir.mkdir(parents=True, exist_ok=True)
    
    safe_filename = file.filename.replace("..", "").replace("/", "_").replace("\\", "_")
    target_path = target_dir / safe_filename
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    relative_path = str(target_path.relative_to(base_path))
    
    logger.info(f"上传文件成功: {relative_path}")
    return UploadResponse(
        file_path=relative_path,
        message="文件上传成功"
    )


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, session: Session = Depends(get_session)) -> dict:
    """删除资产"""
    statement = select(Asset).where(Asset.id == asset_id)
    asset = session.exec(statement).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    file_path = Path(asset.file_path)
    if not file_path.is_absolute():
        effective_project_id = asset.project_id or get_current_project_id()
        if effective_project_id:
            project_statement = select(Project).where(Project.id == effective_project_id)
            project = session.exec(project_statement).first()
            if project:
                file_path = Path(project.path) / asset.file_path
        else:
            file_path = PROJECTS_DIR / "assets" / asset.file_path
    
    if file_path.exists():
        file_path.unlink()
        logger.info(f"删除资产文件: {file_path}")
    else:
        logger.warning(f"资产文件不存在: {file_path}")
    
    session.delete(asset)
    session.commit()
    
    logger.info(f"删除资产记录: {asset.name}")
    return {"message": "资产已删除"}


class RenameRequest(BaseModel):
    """重命名请求"""
    new_name: str


@router.put("/assets/{asset_id}/rename")
def rename_asset(
    asset_id: int,
    data: RenameRequest,
    session: Session = Depends(get_session)
) -> Asset:
    """重命名资产"""
    statement = select(Asset).where(Asset.id == asset_id)
    asset = session.exec(statement).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    old_file_path = Path(asset.file_path)
    if not old_file_path.is_absolute():
        effective_project_id = get_current_project_id()
        if effective_project_id:
            project_statement = select(Project).where(Project.id == effective_project_id)
            project = session.exec(project_statement).first()
            if project:
                old_file_path = Path(project.path) / asset.file_path
    
    if old_file_path.exists():
        safe_new_name = data.new_name.replace("..", "").replace("/", "_").replace("\\", "_")
        if not Path(safe_new_name).suffix:
            safe_new_name = f"{safe_new_name}{old_file_path.suffix}"
        
        new_file_path = old_file_path.parent / safe_new_name
        old_file_path.rename(new_file_path)
        
        relative_path = str(new_file_path.relative_to(new_file_path.parent.parent.parent))
        asset.file_path = relative_path
    
    asset.name = data.new_name
    session.add(asset)
    session.commit()
    session.refresh(asset)
    
    logger.info(f"重命名资产: {asset.name}")
    return asset


@router.get("/assets/{asset_id}/path")
def get_asset_path(asset_id: int, session: Session = Depends(get_session)) -> dict:
    """获取资产文件绝对路径"""
    statement = select(Asset).where(Asset.id == asset_id)
    asset = session.exec(statement).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    file_path = Path(asset.file_path)
    if not file_path.is_absolute():
        effective_project_id = get_current_project_id()
        if effective_project_id:
            project_statement = select(Project).where(Project.id == effective_project_id)
            project = session.exec(project_statement).first()
            if project:
                file_path = Path(project.path) / asset.file_path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {"path": str(file_path)}


@router.get("/assets/{asset_id}/preview")
def get_asset_preview(asset_id: int, session: Session = Depends(get_session)) -> FileResponse:
    """获取资产预览（图片/视频）"""
    statement = select(Asset).where(Asset.id == asset_id)
    asset = session.exec(statement).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    if asset.category not in ["image", "video"]:
        raise HTTPException(status_code=400, detail="只有图片和视频资产支持预览")
    
    file_path = Path(asset.file_path)
    if not file_path.is_absolute():
        effective_project_id = asset.project_id or get_current_project_id()
        if effective_project_id:
            project_statement = select(Project).where(Project.id == effective_project_id)
            project = session.exec(project_statement).first()
            if project:
                file_path = Path(project.path) / asset.file_path
        else:
            file_path = PROJECTS_DIR / "assets" / asset.file_path
    
    if not file_path.exists():
        logger.error(f"预览文件不存在: {file_path}")
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    
    PREVIEW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
    cache_path = PREVIEW_CACHE_DIR / f"{file_hash}.jpg"
    
    if cache_path.exists():
        logger.info(f"使用缓存的预览图: {cache_path}")
        return FileResponse(
            path=cache_path,
            media_type="image/jpeg",
            filename=f"{asset.name}_preview.jpg"
        )
    
    if asset.category == "image":
        try:
            with Image.open(file_path) as img:
                img.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(cache_path, "JPEG", quality=85)
                logger.info(f"生成图片预览成功: {cache_path}")
        except Exception as e:
            logger.error(f"生成图片预览失败: {e}")
            raise HTTPException(status_code=500, detail=f"生成预览失败: {str(e)}")
    
    elif asset.category == "video":
        try:
            cap = cv2.VideoCapture(str(file_path))
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                raise ValueError("无法读取视频帧")
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
            img.save(cache_path, "JPEG", quality=85)
            logger.info(f"生成视频预览成功: {cache_path}")
        except Exception as e:
            logger.error(f"生成视频预览失败: {e}")
            raise HTTPException(status_code=500, detail=f"生成视频预览失败: {str(e)}")
    
    return FileResponse(
        path=cache_path,
        media_type="image/jpeg",
        filename=f"{asset.name}_preview.jpg"
    )


# ==================== 兼容旧API ====================

@router.get("/projects/path")
def get_projects_path() -> dict:
    """获取项目路径（兼容旧API）"""
    ensure_projects_dir()
    return {
        "projects_path": str(PROJECTS_DIR),
        "exists": PROJECTS_DIR.exists()
    }
