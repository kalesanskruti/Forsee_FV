from typing import List, Optional
from pydantic import BaseModel, model_validator, field_validator
from datetime import datetime, time
from uuid import UUID
from enum import Enum

# Enums
class CriticalityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MISSION_CRITICAL = "MISSION_CRITICAL"

class OperationMode(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    SHIFT_BASED = "SHIFT_BASED"
    INTERMITTENT = "INTERMITTENT"
    STANDBY = "STANDBY"

# --- Sub-Schemas ---

class AssetOperationProfileBase(BaseModel):
    operation_mode: OperationMode = OperationMode.CONTINUOUS
    rated_load: Optional[float] = None
    max_operating_load: Optional[float] = None
    duty_cycle_percentage: float = 100.0
    cycle_detection_enabled: bool = False

class AssetShiftScheduleBase(BaseModel):
    shift_start_time: str # HH:MM
    shift_end_time: str   # HH:MM
    active_days: List[str] = ["MON","TUE","WED","THU","FRI"]
    timezone: str = "UTC"
    allowed_tolerance_minutes: int = 15

    @field_validator('shift_start_time', 'shift_end_time')
    @classmethod
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM format")

class AssetEnvironmentProfileBase(BaseModel):
    climate_zone: Optional[str] = None
    humidity_risk_level: str = "LOW"
    corrosion_risk_level: str = "LOW"
    temperature_extreme_risk: str = "LOW"
    vibration_exposure_category: str = "LOW"
    dust_exposure_level: str = "LOW"

# --- Main Metadata Schema ---

class AssetMetadataBase(BaseModel):
    asset_type: Optional[str] = None
    industry_type: Optional[str] = None
    installation_date: Optional[datetime] = None
    expected_design_life_hours: Optional[float] = None
    criticality_level: CriticalityLevel = CriticalityLevel.MEDIUM
    failure_impact_score: int = 5

class AssetMetadataCreate(AssetMetadataBase):
    asset_id: UUID
    operation_profile: AssetOperationProfileBase
    shift_schedule: Optional[AssetShiftScheduleBase] = None
    environment_profile: Optional[AssetEnvironmentProfileBase] = None

    @model_validator(mode='after')
    def validate_shift_requirement(self):
        op_profile = self.operation_profile
        shift_schedule = self.shift_schedule
        
        if op_profile and op_profile.operation_mode == OperationMode.SHIFT_BASED:
            if not shift_schedule:
                raise ValueError("Shift schedule is mandatory for SHIFT_BASED operation info.")
        return self

class AssetMetadataUpdate(BaseModel):
    criticality_level: Optional[CriticalityLevel] = None
    failure_impact_score: Optional[int] = None
    
    operation_profile: Optional[AssetOperationProfileBase] = None
    shift_schedule: Optional[AssetShiftScheduleBase] = None
    environment_profile: Optional[AssetEnvironmentProfileBase] = None

class AssetMetadataResponse(AssetMetadataBase):
    id: UUID
    asset_id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    
    operation_profile: Optional[AssetOperationProfileBase]
    shift_schedule: Optional[AssetShiftScheduleBase]
    environment_profile: Optional[AssetEnvironmentProfileBase]

    class Config:
        from_attributes = True # V2 Config
