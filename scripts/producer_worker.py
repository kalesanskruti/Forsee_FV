import sys
import os
import time
import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.events import ProducerFactory
from models.outbox import OutboxEvent, OutboxStatus
from db.base_class import Base

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OutboxWorker")

# Database Connection (Same as main app)
# Ideally import from core.config
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/forsee")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def process_outbox():
    """
    Polls Outbox table for PENDING events and publishes them.
    Attributes 'Transactional Outbox' pattern.
    """
    producer = ProducerFactory.get_producer()
    db = SessionLocal()
    
    try:
        # Fetch pending events (Limit 50 per batch)
        # SKIP LOCKED ensures multiple workers don't grab same rows
        events = db.query(OutboxEvent).filter(
            OutboxEvent.status == OutboxStatus.PENDING
        ).order_by(OutboxEvent.created_at).limit(50).with_for_update(skip_locked=True).all()
        
        if not events:
            # logger.debug("No pending events found.")
            return

        logger.info(f"Found {len(events)} pending events.")
        
        for event in events:
            try:
                # Publish to Kafka (or Mock)
                future = producer.send(event.topic, event.payload)
                # Wait for acknowledgment (sync for safety in worker)
                # future.get(timeout=10) 
                
                # Mark as published
                event.status = OutboxStatus.PUBLISHED
                event.processed_at = func.now() # handled by DB usually but explicit here
                
                logger.info(f"Published event {event.id} to {event.topic}")
                
            except Exception as e:
                logger.error(f"Failed to publish event {event.id}: {e}")
                event.status = OutboxStatus.FAILED
                event.error_message = str(e)
                event.retry_count += 1
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Worker Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting Outbox Worker...")
    while True:
        process_outbox()
        time.sleep(1) # Poll interval
