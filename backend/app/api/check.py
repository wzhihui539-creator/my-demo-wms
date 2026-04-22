from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services import CheckService
from app.schemas import (
    CheckOrderCreate, CheckOrderUpdate, CheckOrderResponse,
    CheckItemCount, CheckItemAdjust, CheckItemResponse,
    PaginationParams
)

router = APIRouter(prefix="/check", tags=["盘点管理"])


@router.post("/orders", response_model=CheckOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_check_order(
    data: CheckOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建盘点单"""
    order = await CheckService.create_order(db, data)
    order = await CheckService.get_order_by_id(db, order.id)
    return order


@router.get("/orders", response_model=List[CheckOrderResponse])
async def list_check_orders(
    warehouse_id: Optional[UUID] = None,
    check_type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取盘点单列表"""
    orders = await CheckService.get_orders(
        db,
        warehouse_id=warehouse_id,
        check_type=check_type,
        status=status,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    return orders


@router.get("/orders/{order_id}", response_model=CheckOrderResponse)
async def get_check_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取盘点单详情"""
    order = await CheckService.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="盘点单不存在")
    return order


@router.post("/orders/{order_id}/start", response_model=CheckOrderResponse)
async def start_check(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """开始盘点"""
    order = await CheckService.start_check(db, order_id)
    if not order:
        raise HTTPException(status_code=400, detail="盘点单不存在或状态不允许开始")
    return order


@router.post("/items/{item_id}/count", response_model=CheckItemResponse)
async def count_item(
    item_id: UUID,
    data: CheckItemCount,
    db: AsyncSession = Depends(get_db)
):
    """盘点计数"""
    item = await CheckService.count_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=400, detail="盘点项不存在或状态不允许计数")
    return item


@router.post("/items/{item_id}/adjust", response_model=CheckItemResponse)
async def adjust_item(
    item_id: UUID,
    data: CheckItemAdjust,
    db: AsyncSession = Depends(get_db)
):
    """调整盘点差异"""
    item = await CheckService.adjust_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=400, detail="盘点项不存在或状态不允许调整")
    return item


@router.post("/orders/{order_id}/complete", response_model=CheckOrderResponse)
async def complete_check(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """完成盘点"""
    order = await CheckService.complete_check(db, order_id)
    if not order:
        raise HTTPException(status_code=400, detail="盘点单不存在或状态不允许完成")
    return order
