import uuid
from uuid import UUID
from datetime import datetime
from core import context
from services.intelligence import IntelligenceService
from models.metadata import AssetMetadata, AssetOperationProfile, AssetShiftSchedule, OperationMode
from models.intelligence import AssetHealthState
from unittest.mock import MagicMock
from ml.models.degradation_model import DegradationModel

def verify_shift_violation():
    print("--- Verifying Shift Violation Detection Engine ---")
    
    asset_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    
    # 1. Setup Mock DB and context
    db = MagicMock()
    context.set_context(context.RequestContext(org_id=tenant_id))
    
    # Mock Metadata
    meta = AssetMetadata(asset_id=asset_id)
    op_profile = AssetOperationProfile(operation_mode=OperationMode.SHIFT_BASED)
    # Shift: 09:00 - 17:00 UTC
    schedule = AssetShiftSchedule(
        shift_start_time="09:00",
        shift_end_time="17:00",
        active_days=["MON","TUE","WED","THU","FRI"],
        timezone="UTC",
        allowed_tolerance_minutes=15
    )
    meta.operation_profile = op_profile
    meta.shift_schedule = schedule
    
    db.query().filter().first.side_effect = [
        MagicMock(id=asset_id, org_id=tenant_id, meta_data={}), # Asset
        meta, # AssetMetadata in ShiftService
        AssetHealthState(asset_id=asset_id) # Health State
    ]

    # 2. Test OFF-SHIFT Running
    print("\n1. Testing Off-Shift Operation Penalty...")
    # Telemetry at 02:00 AM (Outside 09:00-17:00)
    # Using a fake "telemetry" timestamp by mocking datetime.utcnow in ShiftService or passing it
    # For simplicity, let's assume the current time is 02:00 AM for the test
    
    sensor_data = {
        "rpm": 1500, # Running
        "load": 0.5,
        "vibration": 0.2,
        "temperature": 70.0
    }
    
    # We'll just manually call the logic to verify the modifier
    from services.shift_service import ShiftService
    # Mocking now to be 02:00 UTC
    test_now = datetime.strptime("2026-02-12 02:00:00", "%Y-%m-%d %H:%M:%S")
    
    modifier = ShiftService.calculate_shift_modifier(db, asset_id, True, test_now)
    print(f"Calculated Shift Modifier: {modifier}")
    
    if modifier > 1.0:
        print(f"✅ Correctly applied penalty for off-shift operation: {modifier}")
    else:
        print("❌ FAILED: No penalty applied for off-shift operation")

    # 3. Test Damage Integration
    print("\n2. Testing Damage Integration...")
    ctx = {"dt_hours": 1.0, "shift_modifier": modifier}
    inc = DegradationModel.compute_damage_proxy(sensor_data, {}, ctx)
    print(f"Total Damage Increment (with shift penalty): {inc.total}")
    
    # 4. Test RUL Confidence Decay
    print("\n3. Testing RUL Confidence Decay...")
    # High anomaly score should reduce confidence
    result_clean = DegradationModel.estimate_rul_bounds(0.9, [0.001]*10, shift_violation_penalty=0.0)
    result_violation = DegradationModel.estimate_rul_bounds(0.9, [0.001]*10, shift_violation_penalty=0.3)
    
    print(f"Clean Confidence: {result_clean['confidence']}")
    print(f"Violation Confidence: {result_violation['confidence']}")
    
    if result_violation['confidence'] < result_clean['confidence']:
        print("✅ Correctly reduced RUL confidence due to shift violations")
    else:
        print("❌ FAILED: Confidence did not decay")

    print("\n--- Shift Violation Verification Complete ---")

if __name__ == "__main__":
    verify_shift_violation()
