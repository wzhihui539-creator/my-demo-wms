from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.api import warehouses, skus, auth, inventory, inbound, outbound, check, alert, report


app = FastAPI(
    title="WMS 仓库管理系统",
    description="基于 FastAPI 的现代化仓库管理系统",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(warehouses.router)
app.include_router(skus.router)
app.include_router(inventory.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(check.router)
app.include_router(alert.router)
app.include_router(report.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 静态文件 - 前端构建产物（必须放在API路由之后）
repo_root = Path(__file__).resolve().parents[2]
frontend_dist = repo_root / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/static", StaticFiles(directory=frontend_dist), name="static")
    
    @app.get("/")
    async def serve_frontend():
        return FileResponse(frontend_dist / "index.html")
    
    # 前端页面路由 - 只匹配特定路径避免和API冲突
    @app.get("/favicon.ico")
    async def serve_favicon():
        return FileResponse(frontend_dist / "favicon.ico")
    
    @app.get("/assets/{path:path}")
    async def serve_assets(path: str):
        file_path = frontend_dist / "assets" / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # 前端路由页面 - 匹配常见前端路由路径
    frontend_routes = ["inbound", "outbound", "inventory", "check", "alerts", "reports", "settings", "login"]
    
    @app.get("/{route}")
    async def serve_frontend_route(route: str):
        if route in frontend_routes:
            return FileResponse(frontend_dist / "index.html")
        # 如果不是前端路由，返回404让其他路由处理
        raise HTTPException(status_code=404, detail="Not found")
    
    @app.get("/{route}/{subpath:path}")
    async def serve_frontend_subroute(route: str, subpath: str):
        if route in frontend_routes:
            return FileResponse(frontend_dist / "index.html")
        raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        return {
            "message": "WMS 仓库管理系统 API",
            "version": "1.0.0",
            "docs": "/docs"
        }
