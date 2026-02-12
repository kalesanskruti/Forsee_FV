from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Enum as SqlEnum, JSON, DateTime, func, Integer, ARRAY, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from db.base_class import Base, AuditMixin, TenantMixin
from datetime import datetime

class CriticalityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MISSION_CRITICAL = "MISSION_CRITICAL"

class OperationMode(str, enum.Enum):
    CONTINUOUS = "CONTINUOUS"
    SHIFT_BASED = "SHIFT_BASED"
    INTERMITTENT = "INTERMITTENT"
    STANDBY = "STANDBY"

class AssetMetadata(Base, AuditMixin, TenantMixin):
    """
    Static and semi-static properties of an asset.
    """
    __tablename__ = "asset_metadata"
    
    asset_id = Column(UUID(as_uuid=True), ForeignKey("asset.id"), nullable=False, unique=True, index=True)
    
    __table_args__ = (
        Index("idx_meta_tenant_asset", "org_id", "asset_id"),
    )
    
    # Static Info
    asset_type = Column(String, nullable=True)
    industry_type = Column(String, nullable=True)
    installation_date = Column(DateTime, nullable=True)
    expected_design_life_hours = Column(Float, nullable=True)
    
    # Risk Profile
    criticality_level = Column(SqlEnum(CriticalityLevel), default=CriticalityLevel.MEDIUM)
    failure_impact_score = Column(Integer, default=5) # 1-10
    
    # Versioning
    version = Column(Integer, default=1)
    
    # Relationships
    # asset = relationship("Asset", back_populates="metadata_profile") # Be careful with back_populates on existing Asset model
    operation_profile = relationship("AssetOperationProfile", uselist=False, back_populates="asset_metadata_profile", cascade="all, delete-orphan")
    shift_schedule = relationship("AssetShiftSchedule", uselist=False, back_populates="asset_metadata_profile", cascade="all, delete-orphan")
    environment_profile = relationship("AssetEnvironmentProfile", uselist=False, back_populates="asset_metadata_profile", cascade="all, delete-orphan")

class AssetOperationProfile(Base, TenantMixin):
    """
    How the asset is operated.
    """
    __tablename__ = "asset_operation_profile"
    
    asset_metadata_id = Column(UUID(as_uuid=True), ForeignKey("asset_metadata.id"), nullable=False, unique=True)
    
    operation_mode = Column(SqlEnum(OperationMode), default=OperationMode.CONTINUOUS)
    rated_load = Column(Float, nullable=True)
    max_operating_load = Column(Float, nullable=True)
    duty_cycle_percentage = Column(Float, default=100.0)
    cycle_detection_enabled = Column(Boolean, default=False)
    
    asset_metadata_profile = relationship("AssetMetadata", back_populates="operation_profile")

class AssetShiftSchedule(Base, TenantMixin):
    """
    Shift configuration for SHIFT_BASED assets.
    """
    __tablename__ = "asset_shift_schedule"
    
    asset_metadata_id = Column(UUID(as_uuid=True), ForeignKey("asset_metadata.id"), nullable=False, unique=True)
    
    shift_start_time = Column(String, nullable=False) # HH:MM format (UTC normalized)
    shift_end_time = Column(String, nullable=False)   # HH:MM format
    active_days = Column(ARRAY(String), default=["MON","TUE","WED","THU","FRI"])
    timezone = Column(String, default="UTC")
    allowed_tolerance_minutes = Column(Integer, default=15)
    
    asset_metadata_profile = relationship("AssetMetadata", back_populates="shift_schedule")

class AssetEnvironmentProfile(Base, TenantMixin):
    """
    Environmental exposure factors.
    """
    __tablename__ = "asset_environment_profile"
    
    asset_metadata_id = Column(UUID(as_uuid=True), ForeignKey("asset_metadata.id"), nullable=False, unique=True)
    
    climate_zone = Column(String, nullable=True)
    humidity_risk_level = Column(String, default="LOW") # LOW, MEDIUM, HIGH
    corrosion_risk_level = Column(String, default="LOW")
    temperature_extreme_risk = Column(String, default="LOW")
    vibration_exposure_category = Column(String, default="LOW")
    dust_exposure_level = Column(String, default="LOW")
    
    asset_metadata_profile = relationship("AssetMetadata", back_populates="environment_profile")
