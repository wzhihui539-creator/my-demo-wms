from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services import SKUService
from app.schemas import SKUCreate, SKUUpdate, SKUResponse, PaginationParams

router = APIRouter(prefix="/skus", tags=["商品管理"])


@router.post("", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    data: SKUCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建商品"""
    sku = await SKUService.create(db, data)
    return sku


@router.get("", response_model=List[SKUResponse])
async def list_skus(
    category: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取商品列表"""
    skus = await SKUService.get_list(
        db,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size,
        category=category
    )
    return skus


@router.get("/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取商品详情"""
    sku = await SKUService.get_by_id(db, sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="商品不存在")
    return sku


@router.put("/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: UUID,
    data: SKUUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新商品"""
    sku = await SKUService.update(db, sku_id, data)
    if not sku:
        raise HTTPException(status_code=404, detail="商品不存在")
    return sku
