from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== 入库单 ====================

class InboundItemCreate(BaseModel):
    """入库明细创建"""
    sku_id: UUID
    expected_qty: int = Field(..., gt=0, description="计划数量")
    lot_no: Optional[str] = None
    produced_date: Optional[datetime] = None
    expired_date: Optional[datetime] = None
    remark: Optional[str] = None


class InboundItemResponse(BaseModel):
    """入库明细响应"""
    id: UUID
    sku_id: UUID
    sku_code: Optional[str]
    sku_name: Optional[str]
    lot_no: Optional[str]
    produced_date: Optional[datetime]
    expired_date: Optional[datetime]
    expected_qty: int
    received_qty: int
    putaway_qty: int
    status: str
    location_id: Optional[UUID]
    remark: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class InboundOrderCreate(BaseModel):
    """入库单创建"""
    order_type: str = Field(..., pattern="^(purchase|return|transfer|other)$")
    warehouse_id: UUID
    supplier_id: Optional[UUID] = None
    related_order_no: Optional[str] = None
    expected_date: Optional[datetime] = None
    remark: Optional[str] = None
    items: List[InboundItemCreate] = Field(..., min_length=1)


class InboundOrderUpdate(BaseModel):
    """入库单更新"""
    expected_date: Optional[datetime] = None
    remark: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|cancelled)$")


class InboundOrderResponse(BaseModel):
    """入库单响应"""
    id: UUID
    order_no: str
    order_type: str
    warehouse_id: UUID
    supplier_id: Optional[UUID]
    related_order_no: Optional[str]
    status: str
    total_qty: int
    received_qty: int
    putaway_qty: int
    expected_date: Optional[datetime]
    received_date: Optional[datetime]
    completed_date: Optional[datetime]
    remark: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[InboundItemResponse] = []
    
    class Config:
        from_attributes = True


# ==================== 收货 ====================

class ReceiveRequest(BaseModel):
    """收货请求"""
    inbound_item_id: UUID
    quantity: int = Field(..., gt=0)
    lot_no: Optional[str] = None
    produced_date: Optional[datetime] = None
    expired_date: Optional[datetime] = None
    location_id: Optional[UUID] = None  # 暂存库位
    quality_status: str = Field(default="pass", pattern="^(pass|reject)$")
    reject_reason: Optional[str] = None
    operator: Optional[str] = None


class ReceiveResponse(BaseModel):
    """收货响应"""
    id: UUID
    inbound_order_id: UUID
    inbound_item_id: UUID
    sku_id: UUID
    lot_no: Optional[str]
    quantity: int
    location_id: Optional[UUID]
    quality_status: str
    operator: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 上架 ====================

class PutawayRequest(BaseModel):
    """上架请求"""
    receive_record_id: UUID
    to_location_id: UUID
    quantity: int = Field(..., gt=0)
    operator: Optional[str] = None


class PutawayTaskResponse(BaseModel):
    """上架任务响应"""
    id: UUID
    task_no: str
    inbound_order_id: Optional[UUID]
    sku_id: UUID
    lot_no: Optional[str]
    quantity: int
    from_location_id: Optional[UUID]
    to_location_id: Optional[UUID]
    status: str
    operator: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 查询参数 ====================

class InboundOrderQuery(BaseModel):
    """入库单查询"""
    order_type: Optional[str] = None
    status: Optional[str] = None
    warehouse_id: Optional[UUID] = None
    order_no: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
