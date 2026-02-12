import sys
import os
import uuid
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.intelligence import IntelligenceService
from services.consumers import ConsumerService
from models.outbox import OutboxEvent, OutboxStatus
from models.platform import Alert

def test_sensor_ingestion_flow():
    print("\n--- Testing Sensor Ingestion Flow (Simulated) ---")
    
    # Mock DB
    mock_db = MagicMock()
    asset_id = uuid.uuid4()
    sensor_data = {"temp": 100, "vibration": 0.5}
    
    # 1. Test Ingestion (Outbox Creation)
    print("1. Testing ingest_sensor_data...")
    IntelligenceService.ingest_sensor_data(mock_db, asset_id, sensor_data)
    
    # Verify Outbox Event
    # We expect db.add to be called with OutboxEvent(topic='sensor.batch.ingested')
    ingest_event_call = [call for call in mock_db.add.call_args_list if isinstance(call[0][0], OutboxEvent) and call[0][0].topic == "sensor.batch.ingested"]
    assert len(ingest_event_call) > 0, "Sensor Ingestion failed to create Outbox event"
    ingest_event = ingest_event_call[0][0][0]
    print(f"✅ Ingestion Event Created: ID={ingest_event.payload['event_id']}")
    
    # 2. Test Consumer Processing (Sensor Batch -> Degradation)
    print("\n2. Testing process_sensor_batch_ingested_event...")
    
    # Mock process_telemetry_window to avoid real DB/Physics
    with patch.object(IntelligenceService, 'process_telemetry_window') as mock_process:
        with patch.object(ConsumerService, 'process_degradation_updated_event') as mock_chain:
            
            ConsumerService.process_sensor_batch_ingested_event(mock_db, ingest_event.payload)
            
            # Verify Physics Called
            mock_process.assert_called_once()
            print("✅ Physics Engine Called")
            
            # Verify Chain to RUL
            mock_chain.assert_called_once()
            print("✅ Chained to Degradation Updated")

    # 3. Test Alert Logic (RUL -> Alert)
    print("\n3. Testing process_rul_updated_event (Alerts)...")
    
    # Mock Health State
    mock_health = MagicMock()
    mock_health.operational_health_score = 60 # Low score to trigger assumption
    
    with patch.object(IntelligenceService, 'get_asset_health_state', return_value=mock_health):
        # Mock Alert Object
        mock_alert = MagicMock()
        mock_alert.id = uuid.uuid4()
        mock_alert.title = "Test Alert"
        mock_alert.severity = "HIGH"
        mock_alert.description = "Test Description"
        
        # We need to patch the import inside the method or the module it comes from
        # services.consumers imports 'alert_engine' inside the method
        # Easier to patch sys.modules or use patch.dict if possible, but let's try patching the class method if we can reach it.
        # Since it imports 'from services.alert_engine import alert_engine', we patch that instance.
        
        with patch('services.alert_engine.alert_engine.process_health_and_alert', return_value=mock_alert) as mock_alert_engine:
             
             payload = {"asset_id": str(asset_id), "rul_data": {"mean": 100}}
             ConsumerService.process_rul_updated_event(mock_db, payload)
             
             # Verify Alert Engine Called
             mock_alert_engine.assert_called_once()
             print("✅ Alert Engine Called")
             
             # Verify Outbox Event for Alert
             # We expect a NEW db.add call for 'alert.triggered'
             alert_event_calls = [call for call in mock_db.add.call_args_list if isinstance(call[0][0], OutboxEvent) and call[0][0].topic == "alert.triggered"]
             assert len(alert_event_calls) > 0, "Alert Trigger failed to create Outbox event"
             print(f"✅ Alert Triggered Event Created: {alert_event_calls[0][0][0].topic}")

if __name__ == "__main__":
    test_sensor_ingestion_flow()
