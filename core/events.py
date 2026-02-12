from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
import json
import os
import logging

# Check for Kafka library (graceful fallback for dev)
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)

# --- Event Schemas ---

class BaseEvent(BaseModel):
    event_id: str
    tenant_id: Optional[str] = "default" # Multi-tenant support
    timestamp: datetime
    schema_version: str = "1.0"

class InspectionSubmittedEvent(BaseEvent):
    asset_id: str
    inspection_id: str
    overall_severity: str
    calculated_damage_modifier: float
    calculated_step_damage: float
    confidence_adjustment: float

class SensorBatchIngestedEvent(BaseEvent):
    asset_id: str
    batch_id: str
    row_count: int

class DegradationUpdatedEvent(BaseEvent):
    asset_id: str
    new_health_score: float
    total_damage: float

class RULUpdatedEvent(BaseEvent):
    asset_id: str
    rul_mean: float
    confidence: float

class MetadataUpdatedEvent(BaseEvent):
    asset_id: str
    metadata_version: int
    change_type: str # "CREATED", "UPDATED"

class AlertTriggeredEvent(BaseEvent):
    asset_id: str
    alert_id: str
    severity: str
    message: str

# --- Producer Abstraction ---

class ProducerFactory:
    _instance = None
    
    @staticmethod
    def get_producer():
        if ProducerFactory._instance is None:
            bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
            if KAFKA_AVAILABLE and bootstrap:
                logger.info(f"Connecting to Kafka at {bootstrap}")
                ProducerFactory._instance = KafkaProducer(
                    bootstrap_servers=bootstrap,
                    value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
                )
            else:
                logger.warning("Kafka not available or configured. Using MockProducer.")
                ProducerFactory._instance = MockProducer()
        return ProducerFactory._instance

class MockProducer:
    def send(self, topic, value):
        logger.info(f"[MOCK KAFKA] Topic: {topic} | Payload: {value}")
        # Return a dummy future-like object if needed, or just pass
        class MockFuture:
            def get(self, timeout=None): return True
        return MockFuture()
    
    def flush(self):
        pass
