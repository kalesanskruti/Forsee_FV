import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from uuid import UUID

# Import models
from models.platform import Alert, NotificationPreference, NotificationLog
from models.intelligence import AssetHealthState
from models.ml import Asset
from models.outbox import OutboxEvent, OutboxStatus

# Import services
from services.alert_engine import alert_engine
from services.reminder_service import ReminderService
from notification_service.main import process_event
from notification_service.websocket_manager import ws_manager
from notification_service.delivery_engine import DeliveryEngine

async def run_final_test():
    print("--- Notification System Final Test ---")
    tenant_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    
    db = MagicMock()
    asset = MagicMock(spec=Asset)
    asset.id = asset_id
    asset.org_id = tenant_id
    asset.name = "Test-Asset-001"
    
    health = AssetHealthState(
        asset_id=asset_id,
        operational_health_score=30.0,
        mechanical_health_score=100.0,
        thermal_health_score=100.0,
        electrical_health_score=100.0,
        confidence_score=0.9,
        damage_rate_history=[0.01, 0.01, 0.01, 0.01, 0.5]
    )

    def mock_query(model):
        q = MagicMock()
        if model == Alert: q.filter.return_value.first.return_value = None
        elif model == Asset: q.filter.return_value.first.return_value = asset
        elif model == AssetHealthState: q.filter.return_value.first.return_value = health
        elif model == NotificationPreference:
            pref = NotificationPreference(
                org_id=tenant_id,
                email_enabled=True,
                websocket_enabled=True,
                webhook_enabled=True,
                webhook_url="http://webhook.site"
            )
            q.filter.return_value.first.return_value = pref
        return q

    db.query.side_effect = mock_query

    print("Step 1: Alert Engine Event Emission")
    with patch('models.outbox.OutboxEvent', spec=OutboxEvent):
        alert = alert_engine.process_health_and_alert(db, asset_id, health, {})
        if alert:
            print(f"OK: Alert Triggered: {alert.title}")
        else:
            print("ERR: Alert NOT Triggered")

    print("\nStep 2: Notification Service Processing")
    payload = {"asset_id": str(asset_id), "title": "Test Alert", "severity": "HIGH"}
    
    with patch.object(ws_manager, 'broadcast_to_tenant', new_callable=AsyncMock) as ws, \
         patch.object(DeliveryEngine, 'send_email_async', new_callable=AsyncMock) as email, \
         patch.object(DeliveryEngine, 'trigger_webhook_async', new_callable=AsyncMock) as webhook, \
         patch('services.cache.CacheService.get_json', return_value=None), \
         patch('services.cache.CacheService.set_json'):
         
        try:
            await process_event(db, "alert.triggered", payload, tenant_id)
            print("OK: process_event finished")
            print(f"OK: WebSocket broadcast: {ws.called}")
            print(f"OK: Email sent: {email.called}")
            print(f"OK: Webhook triggered: {webhook.called}")
        except Exception as e:
            print(f"ERR: process_event failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n--- Final Test Complete ---")

if __name__ == "__main__":
    asyncio.run(run_final_test())
