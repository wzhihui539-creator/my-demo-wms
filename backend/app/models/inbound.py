from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid


class InboundOrder(Base):
    """入库单"""
    __tablename__ = "inbound_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(50), unique=True, nullable=False, comment="入库单号")
    order_type = Column(String(20), nullable=False, comment="类型: purchase/return/transfer/other")
    
    # 关联信息
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, comment="入库仓库")
    supplier_id = Column(UUID(as_uuid=True), nullable=True, comment="供应商ID")
    related_order_no = Column(String(50), comment="关联单号(采购单号/退货单号)")
    
    # 状态流程: pending -> receiving -> received -> putaway -> completed -> cancelled
    status = Column(String(20), default="pending", comment="状态")
    
    # 数量统计
    total_qty = Column(Integer, default=0, comment="计划数量")
    received_qty = Column(Integer, default=0, comment="已收数量")
    putaway_qty = Column(Integer, default=0, comment="已上架数量")
    
    # 时间记录
    expected_date = Column(DateTime, comment="预计到货日期")
    received_date = Column(DateTime, comment="实际收货日期")
    completed_date = Column(DateTime, comment="完成日期")
    
    # 其他
    remark = Column(Text, comment="备注")
    created_by = Column(String(50), comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    items = relationship("InboundItem", back_populates="order", cascade="all, delete-orphan")


class InboundItem(Base):
    """入库明细"""
    __tablename__ = "inbound_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("inbound_orders.id"), nullable=False)
    
    # 商品信息
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    sku_code = Column(String(50), comment="SKU编码(冗余)")
    sku_name = Column(String(200), comment="SKU名称(冗余)")
    
    # 批次信息
    lot_no = Column(String(50), comment="批次号")
    produced_date = Column(DateTime, comment="生产日期")
    expired_date = Column(DateTime, comment="有效期至")
    
    # 数量
    expected_qty = Column(Integer, nullable=False, comment="计划数量")
    received_qty = Column(Integer, default=0, comment="已收数量")
    putaway_qty = Column(Integer, default=0, comment="已上架数量")
    
    # 上架库位
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), comment="上架库位")
    
    # 状态: pending -> receiving -> received -> putaway -> completed
    status = Column(String(20), default="pending")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    order = relationship("InboundOrder", back_populates="items")
    sku = relationship("SKU")
    location = relationship("Location")


class ReceiveRecord(Base):
    """收货记录"""
    __tablename__ = "receive_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inbound_order_id = Column(UUID(as_uuid=True), ForeignKey("inbound_orders.id"), nullable=False)
    inbound_item_id = Column(UUID(as_uuid=True), ForeignKey("inbound_items.id"), nullable=False)
    
    # 收货信息
    sku_id = Column(UUID(as_uuid=True), nullable=False)
    lot_no = Column(String(50), comment="批次号")
    quantity = Column(Integer, nullable=False, comment="收货数量")
    location_id = Column(UUID(as_uuid=True), comment="暂存库位")
    
    # 质检信息
    quality_status = Column(String(20), default="pending", comment="质检状态: pending/pass/reject")
    reject_reason = Column(Text, comment="拒收原因")
    
    # 操作人
    operator = Column(String(50), comment="收货人")
    created_at = Column(DateTime, default=datetime.utcnow)


class PutawayTask(Base):
    """上架任务"""
    __tablename__ = "putaway_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_no = Column(String(50), unique=True, nullable=False, comment="任务号")
    
    # 关联
    inbound_order_id = Column(UUID(as_uuid=True), ForeignKey("inbound_orders.id"))
    receive_record_id = Column(UUID(as_uuid=True), ForeignKey("receive_records.id"))
    
    # 商品信息
    sku_id = Column(UUID(as_uuid=True), nullable=False)
    lot_no = Column(String(50))
    quantity = Column(Integer, nullable=False)
    
    # 库位
    from_location_id = Column(UUID(as_uuid=True), comment="来源库位(暂存区)")
    to_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), comment="目标库位")
    
    # 状态: pending -> in_progress -> completed -> cancelled
    status = Column(String(20), default="pending")
    
    # 操作人
    operator = Column(String(50))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
