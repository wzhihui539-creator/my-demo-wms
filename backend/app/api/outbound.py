from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services import OutboundService
from app.schemas import (
    OutboundOrderCreate, OutboundOrderUpdate, OutboundOrderResponse,
    PickRequest, StartPickRequest, PickTaskResponse,
    ShipRequest, ShipRecordResponse,
    WaveCreate, WaveResponse,
    PaginationParams
)

router = APIRouter(prefix="/outbound", tags=["出库管理"])


@router.post("/orders", response_model=OutboundOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_outbound_order(
    data: OutboundOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建出库单"""
    order = await OutboundService.create_order(db, data)
    order = await OutboundService.get_order_by_id(db, order.id)
    return order


@router.get("/orders", response_model=List[OutboundOrderResponse])
async def list_outbound_orders(
    warehouse_id: Optional[UUID] = None,
    order_type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取出库单列表"""
    orders = await OutboundService.get_orders(
        db,
        warehouse_id=warehouse_id,
        order_type=order_type,
        status=status,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    return orders


@router.get("/orders/{order_id}", response_model=OutboundOrderResponse)
async def get_outbound_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取出库单详情"""
    order = await OutboundService.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    return order


@router.post("/orders/{order_id}/pick", response_model=PickTaskResponse)
async def pick_goods(
    order_id: UUID,
    data: PickRequest,
    db: AsyncSession = Depends(get_db)
):
    """拣货操作 - 扣减库存"""
    try:
        task = await OutboundService.pick(db, order_id, data)
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/start-pick", response_model=OutboundOrderResponse)
async def start_pick_order(
    order_id: UUID,
    data: StartPickRequest,
    db: AsyncSession = Depends(get_db)
):
    """开始拣货"""
    try:
        order = await OutboundService.start_pick(db, order_id, data)
        order = await OutboundService.get_order_by_id(db, order.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/ship", response_model=ShipRecordResponse)
async def ship_goods(
    order_id: UUID,
    data: ShipRequest,
    db: AsyncSession = Depends(get_db)
):
    """发货操作"""
    try:
        record = await OutboundService.ship(db, order_id, data)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 波次管理
@router.post("/waves", response_model=WaveResponse)
async def create_wave(
    data: WaveCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建波次"""
    wave = await OutboundService.create_wave(db, data.warehouse_id, data.order_ids)
    return wave
