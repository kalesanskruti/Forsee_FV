from sqlalchemy.orm import Session
from models.registry import ModelRegistry, TaskType
from typing import Dict, Any, Optional

class ModelRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def register_model(
        self,
        name: str,
        version: str,
        task_type: TaskType,
        dataset_name: str,
        artifact_path: str,
        metrics: Optional[Dict[str, Any]] = None,
        is_active: bool = False
    ) -> ModelRegistry:
        """
        Registers a new model in the registry.
        """
        # If this checks as active, deactivate other models for same task
        if is_active:
            self.deactivate_models_for_task(task_type)

        model = ModelRegistry(
            name=name,
            version=version,
            task_type=task_type,
            dataset_name=dataset_name,
            artifact_path=artifact_path,
            metrics=metrics or {},
            is_active=is_active
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_active_model(self, task_type: str) -> Optional[ModelRegistry]:
        """
        Retrieves the currently active model for a specific task.
        """
        return self.db.query(ModelRegistry).filter(
            ModelRegistry.task_type == task_type,
            ModelRegistry.is_active == True
        ).first()

    def deactivate_models_for_task(self, task_type: str):
        """
        Deactivates all models for a specific task.
        """
        self.db.query(ModelRegistry).filter(
            ModelRegistry.task_type == task_type,
            ModelRegistry.is_active == True
        ).update({"is_active": False})
        self.db.commit()

    def activate_model(self, model_id: str) -> Optional[ModelRegistry]:
        """
        Activates a specific model and deactivates others for the same task.
        """
        model = self.db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
        if not model:
            return None

        # Deactivate others
        self.deactivate_models_for_task(model.task_type)

        # Activate this one
        model.is_active = True
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_model_history(self, task_type: str, limit: int = 10):
        """
        Get history of models for a task type.
        """
        return self.db.query(ModelRegistry).filter(
            ModelRegistry.task_type == task_type
        ).order_by(ModelRegistry.created_at.desc()).limit(limit).all()
