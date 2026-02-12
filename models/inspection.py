from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Enum as SqlEnum, JSON, DateTime, func, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from db.base_class import Base, AuditMixin, SoftDeleteMixin, TenantMixin
from datetime import datetime

class InspectionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ARCHIVED = "ARCHIVED"

class InspectionSeverity(str, enum.Enum):
    NONE = "NONE"
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"

class InspectionPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Inspection(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Main inspection record.
    """
    __tablename__ = "inspection"
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_insp_tenant_asset", "org_id", "asset_id"),
    )
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    
    status = Column(SqlEnum(InspectionStatus), default=InspectionStatus.DRAFT, nullable=False)
    
    # Shift Context - Captured at creation/submission
    shift_id = Column(String, nullable=True) # Optional link to external shift system
    is_in_shift = Column(Boolean, nullable=False)
    off_shift_activity_detected = Column(Boolean, default=False)
    
    # Aggregated Impact
    overall_severity = Column(SqlEnum(InspectionSeverity), default=InspectionSeverity.NONE)
    calculated_damage_modifier = Column(Float, default=1.0) # Applied to rate
    calculated_step_damage = Column(Float, default=0.0) # Immediate damage
    confidence_adjustment = Column(Float, default=0.0)
    
    submitted_at = Column(DateTime, nullable=True)
    
    # Relationships
    items = relationship("InspectionItem", back_populates="inspection", cascade="all, delete-orphan")
    # asset = relationship("Asset") # Avoid circular import if not strictly needed here, or handle carefully

class InspectionItem(Base, TenantMixin):
    """
    Granular observation per component.
    """
    __tablename__ = "inspection_item"
    
    inspection_id = Column(UUID(as_uuid=True), ForeignKey("inspection.id"), nullable=False)
    
    component_name = Column(String, nullable=False) # e.g. "Bearing", "Oil"
    severity = Column(SqlEnum(InspectionSeverity), default=InspectionSeverity.NONE)
    priority = Column(SqlEnum(InspectionPriority), default=InspectionPriority.LOW)
    
    comments = Column(String, nullable=True)
    value_numeric = Column(Float, nullable=True) # Measurement if applicable
    value_unit = Column(String, nullable=True)
    
    # Photo/Evidence (URL or path)
    evidence_url = Column(String, nullable=True)
    
    inspection = relationship("Inspection", back_populates="items")
