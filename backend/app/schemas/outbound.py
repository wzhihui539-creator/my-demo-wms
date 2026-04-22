from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== 出库单 ====================

class OutboundItemCreate(BaseModel):
    """出库明细创建"""
    sku_id: UUID
    expected_qty: int = Field(..., gt=0, description="计划数量")
    lot_id: Optional[UUID] = None
    remark: Optional[str] = None


class OutboundItemResponse(BaseModel):
    """出库明细响应"""
    id: UUID
    sku_id: UUID
    sku_code: Optional[str]
    sku_name: Optional[str]
    lot_id: Optional[UUID]
    lot_no: Optional[str]
    expected_qty: int
    picked_qty: int
    shipped_qty: int
    status: str
    remark: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OutboundOrderCreate(BaseModel):
    """出库单创建"""
    order_type: str = Field(..., pattern="^(sales|return|transfer|other)$")
    warehouse_id: UUID
    customer_id: Optional[UUID] = None
    related_order_no: Optional[str] = None
    expected_date: Optional[datetime] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    remark: Optional[str] = None
    items: List[OutboundItemCreate] = Field(..., min_length=1)


class OutboundOrderUpdate(BaseModel):
    """出库单更新"""
    expected_date: Optional[datetime] = None
    priority: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|cancelled)$")


class OutboundOrderResponse(BaseModel):
    """出库单响应"""
    id: UUID
    order_no: str
    order_type: str
    warehouse_id: UUID
    customer_id: Optional[UUID]
    related_order_no: Optional[str]
    status: str
    total_qty: int
    picked_qty: int
    shipped_qty: int
    expected_date: Optional[datetime]
    picked_date: Optional[datetime]
    shipped_date: Optional[datetime]
    completed_date: Optional[datetime]
    remark: Optional[str]
    priority: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[OutboundItemResponse] = []
    
    class Config:
        from_attributes = True


# ==================== 拣货 ====================

class PickRequest(BaseModel):
    """拣货请求"""
    outbound_item_id: UUID
    quantity: int = Field(..., gt=0)
    from_location_id: UUID
    lot_id: Optional[UUID] = None
    operator: Optional[str] = None


class StartPickRequest(BaseModel):
    """开始拣货请求"""
    operator: Optional[str] = None


class PickTaskResponse(BaseModel):
    """拣货任务响应"""
    id: UUID
    task_no: str
    outbound_order_id: Optional[UUID]
    sku_id: UUID
    lot_id: Optional[UUID]
    quantity: int
    picked_qty: int
    from_location_id: Optional[UUID]
    status: str
    wave_id: Optional[UUID]
    operator: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 发货 ====================

class ShipRequest(BaseModel):
    """发货请求"""
    outbound_item_id: UUID
    quantity: int = Field(..., gt=0)
    tracking_no: Optional[str] = None
    carrier: Optional[str] = None
    operator: Optional[str] = None


class ShipRecordResponse(BaseModel):
    """发货记录响应"""
    id: UUID
    outbound_order_id: UUID
    outbound_item_id: UUID
    sku_id: UUID
    lot_id: Optional[UUID]
    quantity: int
    tracking_no: Optional[str]
    carrier: Optional[str]
    operator: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 波次 ====================

class WaveCreate(BaseModel):
    """波次创建"""
    warehouse_id: UUID
    wave_type: str = Field(default="order", pattern="^(order|batch|zone)$")
    order_ids: List[UUID]


class WaveResponse(BaseModel):
    """波次响应"""
    id: UUID
    wave_no: str
    warehouse_id: UUID
    wave_type: str
    status: str
    order_count: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
