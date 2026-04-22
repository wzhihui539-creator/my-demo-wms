from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class OutboundOrder(Base):
    """出库单"""
    __tablename__ = "outbound_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(50), unique=True, nullable=False, comment="出库单号")
    order_type = Column(String(20), nullable=False, comment="类型: sales/return/transfer/other")
    
    # 关联信息
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, comment="出库仓库")
    customer_id = Column(UUID(as_uuid=True), nullable=True, comment="客户ID")
    related_order_no = Column(String(50), comment="关联单号(销售单号/退货单号)")
    
    # 状态流程: pending -> picking -> picked -> shipped -> completed -> cancelled
    status = Column(String(20), default="pending", comment="状态")
    
    # 数量统计
    total_qty = Column(Integer, default=0, comment="计划数量")
    picked_qty = Column(Integer, default=0, comment="已拣数量")
    shipped_qty = Column(Integer, default=0, comment="已发数量")
    
    # 时间记录
    expected_date = Column(DateTime, comment="预计出库日期")
    picked_date = Column(DateTime, comment="实际拣货日期")
    shipped_date = Column(DateTime, comment="实际发货日期")
    completed_date = Column(DateTime, comment="完成日期")
    
    # 其他
    remark = Column(Text, comment="备注")
    priority = Column(String(10), default="normal", comment="优先级: low/normal/high/urgent")
    created_by = Column(String(50), comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    items = relationship("OutboundItem", back_populates="order", cascade="all, delete-orphan")


class OutboundItem(Base):
    """出库明细"""
    __tablename__ = "outbound_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("outbound_orders.id"), nullable=False)
    
    # 商品信息
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    sku_code = Column(String(50), comment="SKU编码(冗余)")
    sku_name = Column(String(200), comment="SKU名称(冗余)")
    
    # 批次信息
    lot_id = Column(UUID(as_uuid=True), ForeignKey("lots.id"), comment="批次ID")
    lot_no = Column(String(50), comment="批次号(冗余)")
    
    # 数量
    expected_qty = Column(Integer, nullable=False, comment="计划数量")
    picked_qty = Column(Integer, default=0, comment="已拣数量")
    shipped_qty = Column(Integer, default=0, comment="已发数量")
    
    # 状态: pending -> picking -> picked -> shipped -> completed
    status = Column(String(20), default="pending")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    order = relationship("OutboundOrder", back_populates="items")
    sku = relationship("SKU")
    lot = relationship("Lot")


class PickTask(Base):
    """拣货任务"""
    __tablename__ = "pick_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_no = Column(String(50), unique=True, nullable=False, comment="任务号")
    
    # 关联
    outbound_order_id = Column(UUID(as_uuid=True), ForeignKey("outbound_orders.id"))
    outbound_item_id = Column(UUID(as_uuid=True), ForeignKey("outbound_items.id"))
    
    # 商品信息
    sku_id = Column(UUID(as_uuid=True), nullable=False)
    lot_id = Column(UUID(as_uuid=True), nullable=True)
    quantity = Column(Integer, nullable=False, comment="计划拣货数量")
    picked_qty = Column(Integer, default=0, comment="实际拣货数量")
    
    # 库位
    from_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), comment="来源库位")
    
    # 状态: pending -> in_progress -> completed -> cancelled
    status = Column(String(20), default="pending")
    
    # 波次
    wave_id = Column(UUID(as_uuid=True), comment="波次ID")
    
    # 操作人
    operator = Column(String(50))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Wave(Base):
    """波次"""
    __tablename__ = "waves"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wave_no = Column(String(50), unique=True, nullable=False, comment="波次号")
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    # 波次类型: order(按单)/batch(批量)/zone(分区)
    wave_type = Column(String(20), default="order")
    
    # 状态: pending -> picking -> completed -> cancelled
    status = Column(String(20), default="pending")
    
    # 包含的订单
    order_count = Column(Integer, default=0)
    
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class ShipRecord(Base):
    """发货记录"""
    __tablename__ = "ship_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    outbound_order_id = Column(UUID(as_uuid=True), ForeignKey("outbound_orders.id"), nullable=False)
    outbound_item_id = Column(UUID(as_uuid=True), ForeignKey("outbound_items.id"), nullable=False)
    
    # 发货信息
    sku_id = Column(UUID(as_uuid=True), nullable=False)
    lot_id = Column(UUID(as_uuid=True), nullable=True)
    quantity = Column(Integer, nullable=False, comment="发货数量")
    
    # 物流信息
    tracking_no = Column(String(50), comment="快递单号")
    carrier = Column(String(50), comment="承运商")
    
    # 操作人
    operator = Column(String(50), comment="发货人")
    created_at = Column(DateTime, default=datetime.utcnow)
