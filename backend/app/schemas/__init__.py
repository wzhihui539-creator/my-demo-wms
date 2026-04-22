from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class WarehouseBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    remark: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class WarehouseResponse(WarehouseBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ZoneBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    zone_type: str = Field(default="storage", pattern="^(storage|pickup|temp|receive|ship)$")


class ZoneCreate(ZoneBase):
    warehouse_id: Optional[UUID] = None


class ZoneResponse(ZoneBase):
    id: UUID
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class LocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    barcode: Optional[str] = None
    location_type: str = Field(default="shelf", pattern="^(shelf|floor|cold)$")
    max_weight: Optional[int] = None
    max_volume: Optional[int] = None


class LocationCreate(LocationBase):
    zone_id: Optional[UUID] = None


class LocationResponse(LocationBase):
    id: UUID
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SKUBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    barcode: Optional[str] = None
    spec: Optional[str] = None
    unit: str = Field(default="件", max_length=20)
    category: Optional[str] = None
    brand: Optional[str] = None
    weight: Optional[int] = None
    volume: Optional[int] = None
    shelf_life_days: Optional[int] = None
    is_batch_managed: bool = False
    is_sn_managed: bool = False


class SKUCreate(SKUBase):
    pass


class SKUUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    weight: Optional[int] = None
    volume: Optional[int] = None
    shelf_life_days: Optional[int] = None
    is_batch_managed: Optional[bool] = None
    is_sn_managed: Optional[bool] = None
    status: Optional[str] = None


class SKUResponse(SKUBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    sku_id: UUID
    location_id: UUID
    lot_id: Optional[UUID] = None
    quantity: int = Field(default=0, ge=0)


class InventoryResponse(InventoryBase):
    id: UUID
    available_qty: int
    locked_qty: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    sku: Optional[SKUResponse] = None
    location: Optional[LocationResponse] = None
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = Field(default="operator", pattern="^(admin|manager|operator)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=50)


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: List


# 导入盘点模块schema
from app.schemas.check import (
    CheckOrderCreate, CheckOrderUpdate, CheckOrderResponse,
    CheckItemCreate, CheckItemCount, CheckItemAdjust, CheckItemResponse,
    CheckOrderQuery
)

# 导入出库模块schema
from app.schemas.outbound import (
    OutboundOrderCreate, OutboundOrderUpdate, OutboundOrderResponse,
    OutboundItemCreate, OutboundItemResponse,
    PickRequest, StartPickRequest, PickTaskResponse,
    ShipRequest, ShipRecordResponse,
    WaveCreate, WaveResponse
)

# 导入入库模块schema
from app.schemas.inbound import (
    InboundOrderCreate, InboundOrderUpdate, InboundOrderResponse,
    InboundItemCreate, InboundItemResponse,
    ReceiveRequest, ReceiveResponse,
    PutawayRequest, PutawayTaskResponse,
    InboundOrderQuery
)

# 导入预警模块schema
from app.schemas.alert import (
    InventoryAlertCreate, InventoryAlertUpdate, InventoryAlertResponse,
    AlertRecordResponse, AlertRecordResolve, AlertStats, CheckAlertRequest
)
