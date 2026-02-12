from sqlalchemy import Column, String, JSON, DateTime, func, Integer, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from db.base_class import Base, TenantMixin

class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class OutboxEvent(Base, TenantMixin):
    """
    Transactional Outbox Table.
    Events are written here in the same transaction as the business data.
    A separate worker polls this table and creates Kafka messages.
    """
    __tablename__ = "outbox_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(SqlEnum(OutboxStatus), default=OutboxStatus.PENDING, index=True)
    
    retry_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
