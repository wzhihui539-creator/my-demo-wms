from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class CheckOrder(Base):
    """盘点单"""
    __tablename__ = "check_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(50), unique=True, nullable=False, comment="盘点单号")
    
    # 盘点类型: full(全盘)/partial(抽盘)/cycle(循环盘点)
    check_type = Column(String(20), nullable=False, comment="盘点类型")
    
    # 关联
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zones.id"), nullable=True, comment="指定库区")
    
    # 状态: pending -> counting -> completed -> cancelled
    status = Column(String(20), default="pending", comment="状态")
    
    # 统计
    total_items = Column(Integer, default=0, comment="盘点项数")
    matched_items = Column(Integer, default=0, comment="匹配项数")
    diff_items = Column(Integer, default=0, comment="差异项数")
    
    # 时间
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 其他
    remark = Column(Text, comment="备注")
    created_by = Column(String(50), comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    items = relationship("CheckItem", back_populates="order", cascade="all, delete-orphan")


class CheckItem(Base):
    """盘点明细"""
    __tablename__ = "check_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_order_id = Column(UUID(as_uuid=True), ForeignKey("check_orders.id"), nullable=False)
    
    # 商品信息
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    sku_code = Column(String(50), comment="SKU编码(冗余)")
    sku_name = Column(String(200), comment="SKU名称(冗余)")
    
    # 库位
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    location_code = Column(String(50), comment="库位编码(冗余)")
    
    # 批次
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), nullable=True)
    lot_no = Column(String(50), comment="批次号(冗余)")
    
    # 数量
    book_qty = Column(Integer, nullable=False, comment="账面数量")
    actual_qty = Column(Integer, nullable=True, comment="实盘数量")
    diff_qty = Column(Integer, default=0, comment="差异数量")
    
    # 状态: pending -> counted -> adjusted -> confirmed
    status = Column(String(20), default="pending")
    
    # 操作人
    checker = Column(String(50), comment="盘点人")
    counted_at = Column(DateTime, comment="盘点时间")
    
    # 调整信息
    adjusted_qty = Column(Integer, comment="调整数量")
    adjust_reason = Column(Text, comment="调整原因")
    adjusted_by = Column(String(50), comment="调整人")
    adjusted_at = Column(DateTime, comment="调整时间")
    
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    order = relationship("CheckOrder", back_populates="items")
    sku = relationship("SKU")
    location = relationship("Location")
    lot = relationship("Lot")
