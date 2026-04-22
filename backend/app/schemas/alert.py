from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ============= 预警规则 =============

class InventoryAlertCreate(BaseModel):
    """创建预警规则"""
    sku_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    category: Optional[str] = None
    alert_type: str = Field(..., pattern="^(low_stock|high_stock|expired|stagnant)$")
    threshold_min: Optional[int] = None
    threshold_max: Optional[int] = None
    days_before_expire: Optional[int] = None
    stagnant_days: Optional[int] = None
    is_active: bool = True
    notify_emails: Optional[str] = None
    notify_phones: Optional[str] = None


class InventoryAlertUpdate(BaseModel):
    """更新预警规则"""
    sku_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    category: Optional[str] = None
    alert_type: Optional[str] = Field(None, pattern="^(low_stock|high_stock|expired|stagnant)$")
    threshold_min: Optional[int] = None
    threshold_max: Optional[int] = None
    days_before_expire: Optional[int] = None
    stagnant_days: Optional[int] = None
    is_active: Optional[bool] = None
    notify_emails: Optional[str] = None
    notify_phones: Optional[str] = None


class InventoryAlertResponse(BaseModel):
    """预警规则响应"""
    id: UUID
    sku_id: Optional[UUID]
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    category: Optional[str]
    alert_type: str
    threshold_min: Optional[int]
    threshold_max: Optional[int]
    days_before_expire: Optional[int]
    stagnant_days: Optional[int]
    is_active: bool
    notify_emails: Optional[str]
    notify_phones: Optional[str]
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= 预警记录 =============

class AlertRecordResponse(BaseModel):
    """预警记录响应"""
    id: UUID
    alert_id: Optional[UUID]
    sku_id: UUID
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    alert_type: str
    alert_level: str
    title: str
    content: Optional[str]
    current_qty: Optional[int]
    threshold_value: Optional[int]
    status: str
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    resolve_note: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AlertRecordResolve(BaseModel):
    """处理预警记录"""
    resolve_note: Optional[str] = None


# ============= 预警统计 =============

class AlertStats(BaseModel):
    """预警统计"""
    total_alerts: int
    unread_count: int
    warning_count: int
    critical_count: int
    low_stock_count: int
    high_stock_count: int
    expired_count: int
    stagnant_count: int


# ============= 库存预警检查请求 =============

class CheckAlertRequest(BaseModel):
    """检查库存预警请求"""
    warehouse_id: Optional[UUID] = None
    sku_id: Optional[UUID] = None
