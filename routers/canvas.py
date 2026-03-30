import json
from typing import List, Optional, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime

from database import get_session
from models import CanvasAsset, Asset, Project
from loguru import logger

router = APIRouter(prefix="/api", tags=["canvas"])


class CanvasSaveRequest(BaseModel):
    name: str
    nodes: List[Any]
    connections: List[Any]
    viewport: dict
    project_id: Optional[int] = None
    asset_id: Optional[int] = None


class CanvasUpdateRequest(BaseModel):
    name: Optional[str] = None
    nodes: Optional[List[Any]] = None
    connections: Optional[List[Any]] = None
    viewport: Optional[dict] = None


class CanvasAssetResponse(BaseModel):
    id: int
    name: str
    nodes: List[Any]
    connections: List[Any]
    viewport: dict
    project_id: Optional[int]
    asset_id: Optional[int]
    created_at: str
    updated_at: str


def get_current_project_id() -> Optional[int]:
    """获取当前项目ID"""
    CURRENT_PROJECT_FILE = Path(__file__).parent.parent / "current_project.txt"
    if CURRENT_PROJECT_FILE.exists():
        try:
            return int(CURRENT_PROJECT_FILE.read_text().strip())
        except:
            return None
    return None


@router.get("/canvas")
def get_canvas_list(
    project_id: Optional[int] = None,
    session: Session = Depends(get_session)
) -> List[CanvasAssetResponse]:
    """获取画布列表"""
    effective_project_id = project_id or get_current_project_id()
    
    if not effective_project_id:
        return []
    
    statement = select(CanvasAsset).where(CanvasAsset.project_id == effective_project_id)
    canvas_list = session.exec(statement).all()
    
    return [
        CanvasAssetResponse(
            id=c.id,
            name=c.name,
            nodes=c.nodes or [],
            connections=c.connections or [],
            viewport=c.viewport or {"x": 0, "y": 0, "scale": 1},
            project_id=c.project_id,
            asset_id=c.asset_id,
            created_at=c.created_at.isoformat() if c.created_at else "",
            updated_at=c.updated_at.isoformat() if c.updated_at else ""
        )
        for c in canvas_list
    ]


@router.post("/canvas")
def save_canvas(
    data: CanvasSaveRequest,
    session: Session = Depends(get_session)
) -> CanvasAssetResponse:
    """保存画布"""
    effective_project_id = data.project_id or get_current_project_id()
    
    if not effective_project_id:
        raise HTTPException(status_code=400, detail="请先选择一个项目")
    
    project = session.get(Project, effective_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    canvas_dir = Path(project.path) / "canvases"
    canvas_dir.mkdir(parents=True, exist_ok=True)
    
    canvas_file = canvas_dir / f"{data.name}.json"
    
    canvas_data = {
        "name": data.name,
        "nodes": data.nodes,
        "connections": data.connections,
        "viewport": data.viewport
    }
    
    with open(canvas_file, "w", encoding="utf-8") as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)
    
    relative_path = f"canvases/{data.name}.json"
    
    asset = None
    if data.asset_id:
        asset = session.get(Asset, data.asset_id)
    
    if not asset:
        existing_asset = session.exec(
            select(Asset).where(
                Asset.project_id == effective_project_id,
                Asset.category == "canvas",
                Asset.name == f"{data.name}.json"
            )
        ).first()
        
        if existing_asset:
            asset = existing_asset
        else:
            asset = Asset(
                name=f"{data.name}.json",
                category="canvas",
                sub_category="",
                file_path=relative_path,
                file_type="json",
                project_id=effective_project_id
            )
            session.add(asset)
            session.commit()
            session.refresh(asset)
    
    existing_canvas = session.exec(
        select(CanvasAsset).where(CanvasAsset.asset_id == asset.id)
    ).first()
    
    if existing_canvas:
        existing_canvas.name = data.name
        existing_canvas.nodes = data.nodes
        existing_canvas.connections = data.connections
        existing_canvas.viewport = data.viewport
        existing_canvas.updated_at = datetime.utcnow()
        session.add(existing_canvas)
        session.commit()
        session.refresh(existing_canvas)
        canvas = existing_canvas
    else:
        canvas = CanvasAsset(
            name=data.name,
            nodes=data.nodes,
            connections=data.connections,
            viewport=data.viewport,
            project_id=effective_project_id,
            asset_id=asset.id
        )
        session.add(canvas)
        session.commit()
        session.refresh(canvas)
    
    logger.info(f"保存画布: {data.name}, 项目ID: {effective_project_id}")
    
    return CanvasAssetResponse(
        id=canvas.id,
        name=canvas.name,
        nodes=canvas.nodes or [],
        connections=canvas.connections or [],
        viewport=canvas.viewport or {"x": 0, "y": 0, "scale": 1},
        project_id=canvas.project_id,
        asset_id=canvas.asset_id,
        created_at=canvas.created_at.isoformat() if canvas.created_at else "",
        updated_at=canvas.updated_at.isoformat() if canvas.updated_at else ""
    )


@router.get("/canvas/{canvas_id}")
def get_canvas(
    canvas_id: int,
    session: Session = Depends(get_session)
) -> CanvasAssetResponse:
    """获取单个画布"""
    canvas = session.get(CanvasAsset, canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="画布不存在")
    
    return CanvasAssetResponse(
        id=canvas.id,
        name=canvas.name,
        nodes=canvas.nodes or [],
        connections=canvas.connections or [],
        viewport=canvas.viewport or {"x": 0, "y": 0, "scale": 1},
        project_id=canvas.project_id,
        asset_id=canvas.asset_id,
        created_at=canvas.created_at.isoformat() if canvas.created_at else "",
        updated_at=canvas.updated_at.isoformat() if canvas.updated_at else ""
    )


@router.put("/canvas/{canvas_id}")
def update_canvas(
    canvas_id: int,
    data: CanvasUpdateRequest,
    session: Session = Depends(get_session)
) -> CanvasAssetResponse:
    """更新画布"""
    canvas = session.get(CanvasAsset, canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="画布不存在")
    
    if data.name is not None:
        old_name = canvas.name
        canvas.name = data.name
        
        if canvas.project_id:
            project = session.get(Project, canvas.project_id)
            if project:
                old_file = Path(project.path) / "canvases" / f"{old_name}.json"
                new_file = Path(project.path) / "canvases" / f"{data.name}.json"
                if old_file.exists():
                    old_file.rename(new_file)
                
                if canvas.asset_id:
                    asset = session.get(Asset, canvas.asset_id)
                    if asset:
                        asset.name = f"{data.name}.json"
                        asset.file_path = f"canvases/{data.name}.json"
                        session.add(asset)
    
    if data.nodes is not None:
        canvas.nodes = data.nodes
    if data.connections is not None:
        canvas.connections = data.connections
    if data.viewport is not None:
        canvas.viewport = data.viewport
    
    canvas.updated_at = datetime.utcnow()
    session.add(canvas)
    session.commit()
    session.refresh(canvas)
    
    if canvas.project_id and canvas.name:
        project = session.get(Project, canvas.project_id)
        if project:
            canvas_file = Path(project.path) / "canvases" / f"{canvas.name}.json"
            canvas_data = {
                "name": canvas.name,
                "nodes": canvas.nodes or [],
                "connections": canvas.connections or [],
                "viewport": canvas.viewport or {"x": 0, "y": 0, "scale": 1}
            }
            with open(canvas_file, "w", encoding="utf-8") as f:
                json.dump(canvas_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"更新画布: {canvas.name}")
    
    return CanvasAssetResponse(
        id=canvas.id,
        name=canvas.name,
        nodes=canvas.nodes or [],
        connections=canvas.connections or [],
        viewport=canvas.viewport or {"x": 0, "y": 0, "scale": 1},
        project_id=canvas.project_id,
        asset_id=canvas.asset_id,
        created_at=canvas.created_at.isoformat() if canvas.created_at else "",
        updated_at=canvas.updated_at.isoformat() if canvas.updated_at else ""
    )


@router.delete("/canvas/{canvas_id}")
def delete_canvas(
    canvas_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """删除画布"""
    canvas = session.get(CanvasAsset, canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="画布不存在")
    
    if canvas.project_id:
        project = session.get(Project, canvas.project_id)
        if project:
            canvas_file = Path(project.path) / "canvases" / f"{canvas.name}.json"
            if canvas_file.exists():
                canvas_file.unlink()
    
    if canvas.asset_id:
        asset = session.get(Asset, canvas.asset_id)
        if asset:
            session.delete(asset)
    
    session.delete(canvas)
    session.commit()
    
    logger.info(f"删除画布: {canvas.name}")
    return {"message": "画布已删除"}


@router.get("/canvas/default-project")
def get_default_canvas_project(
    session: Session = Depends(get_session)
) -> dict:
    """获取默认画布保存项目"""
    project_id = get_current_project_id()
    
    if project_id:
        project = session.get(Project, project_id)
        if project:
            return {"project_id": project_id, "project_name": project.name}
    
    return {"project_id": None, "project_name": None}


@router.post("/canvas/set-default-project/{project_id}")
def set_default_canvas_project(
    project_id: int,
    session: Session = Depends(get_session)
) -> dict:
    """设置默认画布保存项目"""
    project = session.get(Project, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    CURRENT_PROJECT_FILE = Path(__file__).parent.parent / "current_project.txt"
    CURRENT_PROJECT_FILE.write_text(str(project_id))
    
    logger.info(f"设置默认画布项目: {project.name}")
    return {"message": "设置成功", "project_id": project_id, "project_name": project.name}
