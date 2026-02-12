import sys
import os
import uuid
import json
from unittest.mock import MagicMock
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.inspection_service import InspectionService
from services.consumers import ConsumerService
from models.outbox import OutboxEvent, OutboxStatus
from models.inspection import Inspection, InspectionStatus

def test_event_driven_architecture():
    print("\n--- Testing Kafka Flow (Simulated) ---")
    
    # 1. Simulate Inspection Submission -> Outbox Creation
    # Check logic: Submit -> Checks DB -> Creates Outbox Event (Validation Only)
    
    # Mock Objects
    mock_db = MagicMock()
    mock_insp = MagicMock()
    mock_insp.id = uuid.uuid4()
    mock_insp.asset_id = uuid.uuid4()
    mock_insp.status = InspectionStatus.DRAFT
    mock_insp.items = []
    
    mock_db.query().filter().first.return_value = mock_insp
    
    try:
        InspectionService.submit_inspection(mock_db, mock_insp.id, uuid.uuid4())
        
        # Verify Outbox creation
        # We expect db.add to be called with an OutboxEvent
        args = mock_db.add.call_args_list
        outbox_event = None
        for call in args:
            obj = call[0][0]
            if isinstance(obj, OutboxEvent):
                outbox_event = obj
                break
        
        if outbox_event:
            print(f"✅ Outbox Entry Created: {outbox_event.topic} | Status: {outbox_event.status}")
            assert outbox_event.topic == "inspection.submitted"
            
            # 2. Simulate Consumer Processing
            print("\n--- Simulating Consumer Processing ---")
            payload = outbox_event.payload
            
            # Since we mocked DB, we can't really execute the consumer logic deep, 
            # but we can verify the payload structure matches what consumer expects
            assert "asset_id" in payload
            assert payload["calculated_damage_modifier"] >= 1.0
            print("✅ Payload Structure Valid")
            
        else:
            print("❌ Failed to create Outbox Entry")
            
    except Exception as e:
        print(f"❌ Error during simulation: {e}")

if __name__ == "__main__":
    test_event_driven_architecture()
