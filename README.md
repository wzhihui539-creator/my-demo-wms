# WMS 仓库管理系统

基于 FastAPI + PostgreSQL + Redis 的现代化仓库管理系统。

## 技术栈

- **后端**: FastAPI + SQLAlchemy 2.0 (异步)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **任务队列**: Celery + Redis
- **部署**: Docker Compose

## 快速开始

### 1. 环境要求

- Docker & Docker Compose
- Python 3.11+ (本地开发)

### 2. 启动服务

```bash
# 克隆项目后进入目录
cd wms

# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 3. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| API | http://localhost:8000 | 主接口 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 数据库 | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | 缓存/队列 |

### 4. 创建管理员用户

```bash
# 进入后端容器
docker-compose exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.services import UserService
from app.schemas import UserCreate

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = await UserService.create(db, UserCreate(
            username='admin',
            password='admin123',
            real_name='管理员',
            role='admin'
        ))
        print(f'管理员创建成功: {user.username}')

asyncio.run(create_admin())
"
```

## 项目结构

```
wms/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 配置、数据库、安全
│   │   ├── models/      # SQLAlchemy 模型
│   │   ├── schemas/     # Pydantic 校验
│   │   ├── services/    # 业务逻辑
│   │   ├── tasks/       # Celery 异步任务
│   │   └── main.py      # 应用入口
│   ├── alembic/         # 数据库迁移
│   ├── tests/           # 测试
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/            # Vue3 前端 (待开发)
├── mobile/              # 移动端 (待开发)
└── docker-compose.yml   # 编排配置
```

## API 模块

- **认证** `/auth` - 登录/注册
- **仓库** `/warehouses` - 仓库/库区/库位管理
- **商品** `/skus` - SKU 管理
- **库存** `/inventory` - 库存查询
- **入库/出库** (待实现)
- **盘点** (待实现)

## 开发计划

- [x] 基础框架搭建
- [x] 数据库模型设计
- [x] 仓库/库区/库位 CRUD
- [x] 商品管理
- [x] 用户认证
- [ ] 入库流程
- [ ] 出库流程
- [ ] 库存盘点
- [ ] 波次拣货
- [ ] 报表统计
- [ ] 前端界面
- [ ] PDA 扫码

## 许可证

MIT
