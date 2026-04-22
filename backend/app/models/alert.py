from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid
from datetime import datetime

from app.core.database import Base


class InventoryAlert(Base):
    """库存预警规则"""
    __tablename__ = "inventory_alerts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 预警对象
    sku_id = Column(PGUUID(as_uuid=True), ForeignKey("skus.id"), nullable=True)  # 特定商品
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)  # 特定仓库
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)  # 特定库位
    category = Column(String(50), nullable=True)  # 商品分类
    
    # 预警类型
    alert_type = Column(String(20), nullable=False)  # low_stock: 低库存, high_stock: 高库存, expired: 临期, stagnant: 呆滞
    
    # 预警阈值
    threshold_min = Column(Integer, nullable=True)  # 最小阈值（低库存）
    threshold_max = Column(Integer, nullable=True)  # 最大阈值（高库存）
    days_before_expire = Column(Integer, nullable=True)  # 临期天数
    stagnant_days = Column(Integer, nullable=True)  # 呆滞天数
    
    # 预警设置
    is_active = Column(Boolean, default=True)  # 是否启用
    notify_emails = Column(Text, nullable=True)  # 通知邮箱，逗号分隔
    notify_phones = Column(Text, nullable=True)  # 通知手机号，逗号分隔
    
    # 统计
    trigger_count = Column(Integer, default=0)  # 触发次数
    last_triggered_at = Column(DateTime, nullable=True)  # 最后触发时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    sku = relationship("SKU", back_populates="alerts")
    warehouse = relationship("Warehouse")
    location = relationship("Location")
    
    def __repr__(self):
        return f"<InventoryAlert(id={self.id}, type={self.alert_type})>"


class AlertRecord(Base):
    """预警记录"""
    __tablename__ = "alert_records"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联预警规则
    alert_id = Column(PGUUID(as_uuid=True), ForeignKey("inventory_alerts.id"), nullable=True)
    
    # 预警对象
    sku_id = Column(PGUUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    
    # 预警信息
    alert_type = Column(String(20), nullable=False)  # low_stock, high_stock, expired, stagnant
    alert_level = Column(String(10), default="warning")  # warning: 警告, critical: 严重
    
    # 预警内容
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    
    # 当前值
    current_qty = Column(Integer, nullable=True)
    threshold_value = Column(Integer, nullable=True)
    
    # 状态
    status = Column(String(20), default="unread")  # unread: 未读, read: 已读, resolved: 已处理
    resolved_by = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolve_note = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # 关联
    sku = relationship("SKU")
    warehouse = relationship("Warehouse")
    location = relationship("Location")
    alert = relationship("InventoryAlert")
    
    def __repr__(self):
        return f"<AlertRecord(id={self.id}, type={self.alert_type}, status={self.status})>"
