import socket
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from database import init_db
from loguru import logger
from http_client import init_http_client, close_http_client
from routers import workflows_router, assets_router, dashboard_router, orders_router, canvas_router, settings_router, image_generation_router
import sys
import os


def setup_logging():
    """配置日志输出到文件和控制台"""
    log_dir = os.environ.get('LOG_DIR', os.path.join(os.path.dirname(__file__), 'logs'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'backend_{time:YYYY-MM-DD}.log')
    
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )
    
    logger.add(
        log_file,
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    logger.info(f"日志文件目录: {log_dir}")


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    await init_http_client()
    yield
    await close_http_client()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """捕获验证错误并打印详细信息"""
    logger.error(f"验证错误: {exc.errors()}")
    logger.error(f"请求体: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows_router)
app.include_router(assets_router)
app.include_router(dashboard_router)
app.include_router(orders_router)
app.include_router(canvas_router)
app.include_router(settings_router)
app.include_router(image_generation_router)


@app.get("/status")
def get_status():
    return {"status": "ok"}


def find_free_port(start_port: int = 8001, max_attempts: int = 100) -> int:
    """查找空闲端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"无法找到空闲端口 (尝试范围: {start_port}-{start_port + max_attempts})")


if __name__ == "__main__":
    port = find_free_port()
    print(f"SERVER_PORT:{port}", flush=True)
    
    uvicorn_config = {
        "app": app,
        "host": "127.0.0.1",
        "port": port,
        "limit_concurrency": 100,
        "timeout_keep_alive": 30,
    }
    
    uvicorn.run(**uvicorn_config)
