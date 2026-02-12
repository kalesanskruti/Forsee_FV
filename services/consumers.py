import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from services.intelligence import IntelligenceService
from services.cache import CacheService
from core.events import InspectionSubmittedEvent, DegradationUpdatedEvent, RULUpdatedEvent
from models.outbox import OutboxEvent, OutboxStatus
from models.ml import Asset
from db.base_class import Base

logger = logging.getLogger(__name__)

class ConsumerService:
    """
    Handles processing of events consumed from Kafka.
    """
    
    @staticmethod
    def process_inspection_submitted_event(db: Session, payload: dict):
        """
        Consumer for 'inspection.submitted'.
        Triggered when an inspection is finalized and consumed.
        Action: Update degradation state.
        """
        logger.info(f"Processing inspection.submitted for asset {payload.get('asset_id')}")
        
        try:
            # 1. Update Degradation (Physics)
            # Payload keys match the event schema
            IntelligenceService.apply_inspection_impact(
                db, 
                asset_id=UUID(payload['asset_id']), 
                damage_step=payload.get('calculated_step_damage', 0.0),
                rate_modifier=payload.get('calculated_damage_modifier', 1.0),
                confidence_penalty=payload.get('confidence_adjustment', 0.0)
            )
            logger.info("Degradation state updated.")
            
            # 2. Trigger Downstream: RUL Calculation
            # In a pure event system, apply_inspection_impact might emit 'degradation.updated'
            # Here, we chain logic to simulate the next consumer reacting.
            ConsumerService.process_degradation_updated_event(db, {"asset_id": payload['asset_id']})
            
        except Exception as e:
            logger.error(f"Failed to process inspection event: {e}")
            raise e

    @staticmethod
    def process_sensor_batch_ingested_event(db: Session, payload: dict):
        """
        Consumer for 'sensor.batch.ingested'.
        Action: Compute Degradation (stress-normalized).
        """
        asset_id = payload.get('asset_id')
        data = payload.get('sensor_data', {})
        logger.info(f"Processing sensor batch for asset {asset_id}")
        
        try:
            # 1. Compute Degradation & Update Health State
            # This calls the heavy physics logic
            IntelligenceService.process_telemetry_window(db, UUID(asset_id), data)
            logger.info("Degradation state updated from telemetry.")
            
            # 2. Trigger Downstream: RUL Calculation
            ConsumerService.process_degradation_updated_event(db, {"asset_id": asset_id})
            
        except Exception as e:
            logger.error(f"Failed to process sensor batch: {e}")
            raise e

    @staticmethod
    def process_degradation_updated_event(db: Session, payload: dict):
        """
        Consumer for 'degradation.updated'.
        Action: Re-calculate RUL.
        """
        asset_id = payload.get('asset_id')
        logger.info(f"Processing degradation.updated for asset {asset_id}")
        
        try:
            # Re-run RUL probability engine
            rul_data = IntelligenceService.get_probabilistic_rul(db, UUID(asset_id))
            
            # Publish 'rul.updated' (Mock)
            logger.info(f"RUL Recalculated: {rul_data}")
            
            # Trigger Downstream: Alerts
            ConsumerService.process_rul_updated_event(db, {"asset_id": asset_id, "rul_data": rul_data})
            
        except Exception as e:
            logger.error(f"Failed to calculate RUL: {e}")
            raise e

    @staticmethod
    def process_rul_updated_event(db: Session, payload: dict):
        """
        Consumer for 'rul.updated'.
        Action: Check Alerts -> Publish 'alert.triggered'.
        """
        asset_id = payload.get('asset_id')
        logger.info(f"Checking alerts for asset {asset_id}")
        
        try:
            from services.alert_engine import alert_engine
            
            # Fetch current health state (it was updated by previous chain)
            health = IntelligenceService.get_asset_health_state(db, UUID(asset_id))
            
            # Check for Alerts
            # Passing empty dict for prediction_result as it's unused in logic
            alert = alert_engine.process_health_and_alert(db, UUID(asset_id), health, {})
            
            if alert:
                logger.warning(f"Alert Triggered for Asset {asset_id}: {alert.title}")
                # ... Alert logic ...
                # (Existing alert code)
            
            # --- REDIS CACHE UPDATE ---
            # Fetch asset for tenant_id (Required for key scoping)
            asset = db.query(Asset).filter(Asset.id == UUID(asset_id)).first()
            if asset:
                cache_data = {
                    "rul_data": payload.get('rul_data'),
                    "timestamp": datetime.utcnow().isoformat(),
                    "asset_id": str(asset_id),
                    "tenant_id": str(asset.org_id)
                }
                CacheService.set_json(str(asset.org_id), str(asset_id), "rul", cache_data, ttl_seconds=300)
                logger.info(f"RUL Cache updated for asset {asset_id}")
                
        except Exception as e:
            logger.error(f"Failed to process RUL update/Alerts: {e}")
            raise e
