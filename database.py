from sqlmodel import SQLModel, create_engine, Session, text
from typing import Generator
from loguru import logger
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_video_production.db")

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def migrate_database():
    """执行数据库迁移"""
    with Session(engine) as session:
        try:
            result = session.exec(text("PRAGMA table_info(asset)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "project_id" not in columns:
                logger.info("正在添加 asset.project_id 列...")
                session.exec(text("ALTER TABLE asset ADD COLUMN project_id INTEGER"))
                session.commit()
                logger.info("asset.project_id 列添加成功")
        except Exception as e:
            logger.warning(f"迁移检查失败: {e}")
        
        try:
            result = session.exec(text("SELECT name FROM sqlite_master WHERE type='table' AND name='project'"))
            if not result.fetchone():
                logger.info("正在创建 project 表...")
                session.exec(text("""
                    CREATE TABLE project (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        path TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                session.commit()
                logger.info("project 表创建成功")
        except Exception as e:
            logger.warning(f"创建 project 表失败: {e}")
        
        try:
            result = session.exec(text("SELECT name FROM sqlite_master WHERE type='table' AND name='subcategory'"))
            if not result.fetchone():
                logger.info("正在创建 subcategory 表...")
                session.exec(text("""
                    CREATE TABLE subcategory (
                        id INTEGER PRIMARY KEY,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        project_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                session.commit()
                logger.info("subcategory 表创建成功")
        except Exception as e:
            logger.warning(f"创建 subcategory 表失败: {e}")


def create_db_and_tables():
    """创建数据库和所有表"""    
    migrate_database()
    
    SQLModel.metadata.create_all(engine)
    logger.info("数据库表创建完成")


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话的依赖函数"""
    with Session(engine) as session:
        yield session


def init_db():
    """初始化数据库"""
    create_db_and_tables()
    logger.info("数据库初始化完成")
