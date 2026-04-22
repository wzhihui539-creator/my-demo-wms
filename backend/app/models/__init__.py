from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class Warehouse(Base):
    """仓库"""
    __tablename__ = "warehouses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, comment="仓库编码")
    name = Column(String(100), nullable=False, comment="仓库名称")
    address = Column(String(255), comment="地址")
    contact = Column(String(50), comment="联系人")
    phone = Column(String(20), comment="电话")
    status = Column(String(20), default="active", comment="状态: active/inactive")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    zones = relationship("Zone", back_populates="warehouse")


class Zone(Base):
    """库区"""
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    code = Column(String(50), nullable=False, comment="库区编码")
    name = Column(String(100), nullable=False, comment="库区名称")
    zone_type = Column(String(20), default="storage", comment="类型: storage/pickup/temp/receive/ship")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    warehouse = relationship("Warehouse", back_populates="zones")
    locations = relationship("Location", back_populates="zone")


class Location(Base):
    """库位"""
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=False)
    code = Column(String(50), nullable=False, comment="库位编码")
    barcode = Column(String(100), unique=True, comment="条码")
    location_type = Column(String(20), default="shelf", comment="类型: shelf/floor/cold")
    max_weight = Column(Integer, comment="最大承重(kg)")
    max_volume = Column(Integer, comment="最大容积(m³)")
    status = Column(String(20), default="empty", comment="状态: empty/occupied/full/blocked")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    zone = relationship("Zone", back_populates="locations")
    inventories = relationship("Inventory", back_populates="location")


class SKU(Base):
    """商品/SKU"""
    __tablename__ = "skus"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, comment="SKU编码")
    name = Column(String(200), nullable=False, comment="商品名称")
    barcode = Column(String(100), comment="条码")
    spec = Column(String(100), comment="规格")
    unit = Column(String(20), default="件", comment="单位")
    category = Column(String(50), comment="分类")
    brand = Column(String(50), comment="品牌")
    weight = Column(Integer, comment="重量(g)")
    volume = Column(Integer, comment="体积(cm³)")
    shelf_life_days = Column(Integer, comment="保质期(天)")
    is_batch_managed = Column(Boolean, default=False, comment="是否批次管理")
    is_sn_managed = Column(Boolean, default=False, comment="是否序列号管理")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    inventories = relationship("Inventory", back_populates="sku")
    alerts = relationship("InventoryAlert", back_populates="sku")


class Inventory(Base):
    """库存记录"""
    __tablename__ = "inventories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=True)
    quantity = Column(Integer, default=0, comment="数量")
    available_qty = Column(Integer, default=0, comment="可用数量")
    locked_qty = Column(Integer, default=0, comment="锁定数量")
    status = Column(String(20), default="normal", comment="状态")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    sku = relationship("SKU", back_populates="inventories")
    location = relationship("Location", back_populates="inventories")
    lot = relationship("Lot", back_populates="inventories")


class Lot(Base):
    """批次"""
    __tablename__ = "lots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    lot_no = Column(String(50), nullable=False, comment="批次号")
    produced_date = Column(DateTime, comment="生产日期")
    expired_date = Column(DateTime, comment="有效期至")
    supplier_id = Column(UUID(as_uuid=True), comment="供应商ID")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    inventories = relationship("Inventory", back_populates="lot")


class User(Base):
    """用户"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50), comment="真实姓名")
    phone = Column(String(20), comment="电话")
    email = Column(String(100), comment="邮箱")
    role = Column(String(20), default="operator", comment="角色: admin/manager/operator")
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# 导入入库模块
from app.models.check import CheckOrder, CheckItem
from app.models.outbound import OutboundOrder, OutboundItem, PickTask, Wave, ShipRecord
from app.models.inbound import InboundOrder, InboundItem, ReceiveRecord, PutawayTask
from app.models.alert import InventoryAlert, AlertRecord

__all__ = [
    "Warehouse", "Zone", "Location", "SKU", "Inventory", "Lot", "User",
    "InboundOrder", "InboundItem", "ReceiveRecord", "PutawayTask",
    "OutboundOrder", "OutboundItem", "PickTask", "Wave", "ShipRecord",
    "CheckOrder", "CheckItem",
    "InventoryAlert", "AlertRecord"
]
