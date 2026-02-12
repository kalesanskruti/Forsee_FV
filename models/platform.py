from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Boolean, JSON, Integer, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from db.base_class import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Plan(Base, AuditMixin):
    __tablename__ = "plan"
    
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    max_users = Column(Integer)
    max_models = Column(Integer)

class Alert(Base, AuditMixin, TenantMixin):
    __tablename__ = "alert"
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False)
    
    __table_args__ = (
        Index("idx_alert_tenant_asset", "org_id", "asset_id"),
    )
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="OPEN") # OPEN, ACKNOWLEDGED, RESOLVED
    category = Column(String, default="PREDICTIVE_FAILURE")
    
    # Economics (Linked for notification context)
    risk_score = Column(Float, nullable=False)
    
    # Audit logic
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    meta_data = Column(JSON, nullable=True) # { "probability": 0.8, "vector": "mechanical" }

class NotificationPreference(Base, TenantMixin):
    __tablename__ = "notification_preference"
    
    # Scope: If user_id is null, it's a tenant-wide default
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    
    websocket_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
    webhook_enabled = Column(Boolean, default=False)
    
    # Thresholds
    min_severity_threshold = Column(String, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    
    # Webhook Config (Encrypted in real app)
    webhook_url = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True) 
    
    # Digest Info
    digest_enabled = Column(Boolean, default=True)
    digest_frequency = Column(String, default="DAILY") # HOURLY, DAILY, WEEKLY

class EscalationPolicy(Base, TenantMixin):
    __tablename__ = "escalation_policy"
    
    alert_category = Column(String, nullable=False) # e.g. "PREDICTIVE_FAILURE"
    
    # Policy Steps: JSON array: [ {"delay_minutes": 60, "action": "EMAIL_ADMIN"}, ... ]
    steps = Column(JSON, nullable=False)

class NotificationLog(Base, TenantMixin):
    __tablename__ = "notification_log"
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alert.id"), nullable=True)
    
    channel = Column(String, nullable=False) # WEBSOCKET, EMAIL, WEBHOOK
    recipient = Column(String, nullable=False) # email or socket_id or url
    status = Column(String, nullable=False) # SENT, FAILED, RETRYING
    
    retry_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    
    payload_hash = Column(String, nullable=True) # For de-duplication
    timestamp = Column(DateTime, default=func.now())
    
class AuditLog(Base):
    __tablename__ = "audit_log"
    
    action = Column(String, nullable=False) # Login, Prediction, etc.
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    
    user_id = Column(UUID(as_uuid=True), nullable=True) # ID of user who performed action
    org_id = Column(UUID(as_uuid=True), nullable=True) 
    
    # Not using standard mixins because audit logs are immutable and shouldn't be soft deleted usually
