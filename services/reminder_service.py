from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from models.ml import Asset
from models.intelligence import AssetHealthState
from models.outbox import OutboxEvent, OutboxStatus

class ReminderService:
    @staticmethod
    def check_for_stale_devices(db: Session, org_id: UUID):
        """
        Detect devices that haven't sent telemetry in over 24 hours.
        """
        threshold = datetime.utcnow() - timedelta(hours=24)
        
        # This is a simplified query. In product, we'd check raw telemetry timestamps.
        # Here we check the last_updated in health state as a proxy.
        stale_assets = db.query(Asset).join(AssetHealthState).filter(
            Asset.org_id == org_id,
            AssetHealthState.last_updated < threshold
        ).all()
        
        for asset in stale_assets:
            payload = {
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "last_seen": asset.health_state.last_updated.isoformat(),
                "reminder_type": "DEVICE_STALE",
                "message": f"Device '{asset.name}' has not reported data in over 24 hours. Please check connectivity.",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            event = OutboxEvent(
                topic="device.health.reminder",
                payload=payload,
                status=OutboxStatus.PENDING,
                org_id=org_id
            )
            db.add(event)
            
        db.commit()

    @staticmethod
    def trigger_routine_health_prompt(db: Session, asset_id: UUID):
        """
        Triggered by scheduler or manual request to remind admin to check health.
        """
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset: return

        payload = {
            "asset_id": str(asset_id),
            "asset_name": asset.name,
            "reminder_type": "ROUTINE_CHECK",
            "message": f"Routine health check reminder: Please review the operational status of {asset.name}.",
            "timestamp": datetime.utcnow().isoformat()
        }

        event = OutboxEvent(
            topic="device.health.reminder",
            payload=payload,
            status=OutboxStatus.PENDING,
            org_id=asset.org_id
        )
        db.add(event)
        db.commit()
