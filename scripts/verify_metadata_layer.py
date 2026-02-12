import sys
import os
import uuid
import json
from unittest.mock import MagicMock
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.metadata_service import MetadataService
from schemas.metadata import AssetMetadataCreate, AssetOperationProfileBase, AssetShiftScheduleBase, OperationMode
from models.outbox import OutboxEvent

def test_metadata_layer():
    print("\n--- Testing Metadata Layer (Simulated) ---")
    
    asset_id = uuid.uuid4()
    mock_db = MagicMock()
    
    # 1. Test Validation (Shift Schedule Required)
    print("1. Testing Validation Rules...")
    try:
        AssetMetadataCreate(
            asset_id=asset_id,
            operation_profile=AssetOperationProfileBase(operation_mode=OperationMode.SHIFT_BASED)
            # Missing shift_schedule
        )
        print("❌ Validation Failed: Should have raised ValueError for missing shift schedule")
    except ValueError as e:
        print(f"✅ Validation Passed: Caught missing shift schedule ({e})")

    # 2. Test Creation & Outbox Event
    print("\n2. Testing Metadata Creation & Event...")
    
    valid_schema = AssetMetadataCreate(
        asset_id=asset_id,
        operation_profile=AssetOperationProfileBase(operation_mode=OperationMode.CONTINUOUS),
        criticality_level="HIGH"
    )
    
    # Mock DB Query to return None (New Metadata)
    mock_db.query().filter().first.return_value = None
    
    MetadataService.create_or_update_metadata(mock_db, asset_id, valid_schema)
    
    # Verify DB Add (Metadata + Profile + Outbox)
    add_calls = mock_db.add.call_args_list
    outbox_event = None
    metadata_obj = None
    
    for call in add_calls:
        obj = call[0][0]
        if hasattr(obj, 'topic') and obj.topic == "metadata.updated":
            outbox_event = obj
        if hasattr(obj, 'criticality_level'):
            metadata_obj = obj
            
    if metadata_obj:
        print(f"✅ Metadata Object Created: Criticality={metadata_obj.criticality_level}")
    else:
        print("❌ Metadata Object NOT created")
        
    if outbox_event:
        print(f"✅ Outbox Event Published: {outbox_event.topic} | Version: {outbox_event.payload['metadata_version']}")
    else:
        print("❌ Outbox Event NOT published")

if __name__ == "__main__":
    test_metadata_layer()
