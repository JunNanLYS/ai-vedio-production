from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from models.project import Project


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="资产名称")
    category: str = Field(description="大类: prompt/image/audio/video")
    sub_category: str = Field(default="", description="子分类")
    file_path: str = Field(description="文件路径")
    file_type: str = Field(description="文件类型")
    project_id: Optional[int] = Field(default=None, foreign_key="project.id", description="所属项目ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
