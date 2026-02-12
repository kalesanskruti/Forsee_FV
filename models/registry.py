from sqlalchemy import Column, String, Boolean, JSON, Enum, Float
import enum
from db.base_class import Base, AuditMixin

class TaskType(str, enum.Enum):
    RUL = "rul"
    PRECURSOR = "precursor"
    CLUSTERING = "clustering"
    DRIFT = "drift"
    HEALTH_INDEX = "health_index"

class ModelRegistry(Base, AuditMixin):
    __tablename__ = "model_registry"

    name = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)
    task_type = Column(Enum(TaskType), nullable=False, index=True)
    dataset_name = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)  # Stores accuracy, f1, mse, etc.
    artifact_path = Column(String, nullable=False)  # Path to the .pkl/.pt file
    is_active = Column(Boolean, default=False, index=True)
    
    # Optional: Link to a specific training run or user if needed
    # training_run_id = Column(UUID(as_uuid=True), ForeignKey("training_run.id"), nullable=True)

    def __repr__(self):
        return f"<ModelRegistry(name={self.name}, version={self.version}, task={self.task_type}, active={self.is_active})>"
