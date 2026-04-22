from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.services import InboundService
from app.schemas import (
    InboundOrderCreate, InboundOrderUpdate, InboundOrderResponse,
    ReceiveRequest, ReceiveResponse,
    PutawayRequest, PutawayTaskResponse,
    InboundOrderQuery, PaginationParams
)

router = APIRouter(prefix="/inbound", tags=["入库管理"])


@router.post("/orders", response_model=InboundOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_inbound_order(
    data: InboundOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建入库单"""
    order = await InboundService.create_order(db, data)
    # 重新查询以加载 items 关系
    order = await InboundService.get_order_by_id(db, order.id)
    return order


@router.get("/orders", response_model=List[InboundOrderResponse])
async def list_inbound_orders(
    warehouse_id: Optional[UUID] = None,
    order_type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取入库单列表"""
    orders = await InboundService.get_orders(
        db,
        warehouse_id=warehouse_id,
        order_type=order_type,
        status=status,
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    return orders


@router.get("/orders/{order_id}", response_model=InboundOrderResponse)
async def get_inbound_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取入库单详情"""
    order = await InboundService.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    return order


@router.put("/orders/{order_id}", response_model=InboundOrderResponse)
async def update_inbound_order(
    order_id: UUID,
    data: InboundOrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新入库单（仅 pending 状态可编辑）"""
    order = await InboundService.update_order(db, order_id, data)
    if not order:
        raise HTTPException(status_code=400, detail="入库单不存在或状态不允许编辑")
    return order


@router.post("/orders/{order_id}/complete-receive", response_model=InboundOrderResponse)
async def complete_receive(
    order_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """完成收货 - 将状态从 receiving 改为 received"""
    try:
        order = await InboundService.complete_receive(db, order_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/receive", response_model=ReceiveResponse)
async def receive_goods(
    order_id: UUID,
    data: ReceiveRequest,
    db: AsyncSession = Depends(get_db)
):
    """收货操作"""
    try:
        record = await InboundService.receive(db, order_id, data)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/putaway-tasks", response_model=PutawayTaskResponse)
async def create_putaway_task(
    order_id: UUID,
    data: PutawayRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建上架任务"""
    try:
        task = await InboundService.create_putaway_task(
            db, order_id, data.receive_record_id, data.to_location_id, data.quantity, data.operator
        )
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/putaway-tasks/{task_id}/complete", response_model=PutawayTaskResponse)
async def complete_putaway(
    task_id: UUID,
    operator: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """完成上架 - 更新库存"""
    try:
        task = await InboundService.complete_putaway(db, task_id, operator)
        return task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
