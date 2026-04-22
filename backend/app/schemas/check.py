from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== 盘点单 ====================

class CheckItemCreate(BaseModel):
    """盘点明细创建"""
    sku_id: UUID
    location_id: UUID
    lot_id: Optional[UUID] = None
    book_qty: int = Field(..., ge=0, description="账面数量")
    remark: Optional[str] = None


class CheckItemCount(BaseModel):
    """盘点计数请求"""
    actual_qty: int = Field(..., ge=0, description="实盘数量")
    checker: Optional[str] = None
    remark: Optional[str] = None


class CheckItemAdjust(BaseModel):
    """盘点调整请求"""
    adjusted_qty: int = Field(..., ge=0, description="调整后数量")
    adjust_reason: str = Field(..., min_length=1, description="调整原因")
    adjusted_by: Optional[str] = None


class CheckItemResponse(BaseModel):
    """盘点明细响应"""
    id: UUID
    check_order_id: UUID
    sku_id: UUID
    sku_code: Optional[str]
    sku_name: Optional[str]
    location_id: UUID
    location_code: Optional[str]
    lot_id: Optional[UUID]
    lot_no: Optional[str]
    book_qty: int
    actual_qty: Optional[int]
    diff_qty: int
    status: str
    checker: Optional[str]
    counted_at: Optional[datetime]
    adjusted_qty: Optional[int]
    adjust_reason: Optional[str]
    adjusted_by: Optional[str]
    adjusted_at: Optional[datetime]
    remark: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CheckOrderCreate(BaseModel):
    """盘点单创建"""
    check_type: str = Field(..., pattern="^(full|partial|cycle)$")
    warehouse_id: UUID
    zone_id: Optional[UUID] = None
    remark: Optional[str] = None
    items: Optional[List[CheckItemCreate]] = None


class CheckOrderUpdate(BaseModel):
    """盘点单更新"""
    remark: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|cancelled)$")


class CheckOrderResponse(BaseModel):
    """盘点单响应"""
    id: UUID
    order_no: str
    check_type: str
    warehouse_id: UUID
    zone_id: Optional[UUID]
    status: str
    total_items: int
    matched_items: int
    diff_items: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    remark: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[CheckItemResponse] = []
    
    class Config:
        from_attributes = True


class CheckOrderQuery(BaseModel):
    """盘点单查询"""
    check_type: Optional[str] = None
    status: Optional[str] = None
    warehouse_id: Optional[UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
