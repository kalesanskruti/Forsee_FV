import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models.registry import ModelRegistry, TaskType
from services.registry_service import ModelRegistryService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self):
        self.loaded_models: Dict[str, Any] = {}
        self.env = os.getenv("ENV", "development").lower()

    def load_active_models(self, db: Session):
        """
        Loads all active models from the registry into memory.
        """
        logger.info(f"Loading active models in {self.env} mode...")
        registry_service = ModelRegistryService(db)
        
        # Define tasks to load
        tasks = [TaskType.RUL, TaskType.PRECURSOR, TaskType.CLUSTERING, TaskType.DRIFT]
        
        for task in tasks:
            model_record = registry_service.get_active_model(task)
            
            if model_record:
                try:
                    self._load_model_from_record(model_record)
                except Exception as e:
                    logger.error(f"Failed to load model for {task}: {e}")
                    if self.env == "production":
                        raise RuntimeError(f"CRITICAL: Failed to load active model for {task} in PROD. {e}")
            else:
                msg = f"No active model found for {task}"
                logger.warning(msg)
                if self.env == "production":
                    raise RuntimeError(f"CRITICAL: {msg} in PROD. Application start aborted.")

    def _load_model_from_record(self, record: ModelRegistry):
        path = record.artifact_path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Artifact not found at {path}")
            
        logger.info(f"Loading {record.task_type} model from {path}")
        
        # Determine how to load based on extension or metadata
        if path.endswith(".pkl"):
            model = joblib.load(path)
        elif path.endswith(".pt") or path.endswith(".pth"):
            # Assuming simple torch load for now, distinct from specific model class wrapper
            # In a real app, might need to instantiate the class first if saving state_dict
            import torch
            model = torch.load(path)
            model.eval() # Set to eval mode
        else:
            # Fallback to joblib
            model = joblib.load(path)
            
        self.loaded_models[record.task_type] = model

    def predict(self, task_type: TaskType, data: Any) -> Dict[str, Any]:
        if task_type not in self.loaded_models:
             # Try lazy load or fail
             raise ValueError(f"No loaded model for task: {task_type}")
             
        model = self.loaded_models[task_type]
        
        try:
            # Data preprocessing should ideally happen here or using a saved pipeline
            # For this implementations, we assume 'data' is compatible or simple numpy/df
            
            result = {}
            
            if task_type == TaskType.RUL:
                # Expecting sequence data or converting generic features
                # Simplified: assume data is a list/array of features matching model input
                import torch
                if isinstance(data, list):
                    import numpy as np
                    input_data = torch.FloatTensor([data]) # Batch dim
                else:
                    input_data = torch.FloatTensor(data)
                    
                with torch.no_grad():
                    prediction = model(input_data).numpy().item()
                result = {"rul": float(prediction)}

            elif task_type == TaskType.PRECURSOR:
                # Sklearn model
                prediction = model.predict([data])[0]
                probs = model.predict_proba([data])[0].tolist() if hasattr(model, "predict_proba") else []
                result = {"class": int(prediction), "probabilities": probs}

            elif task_type == TaskType.CLUSTERING:
                cluster = model.predict([data])[0]
                result = {"cluster": int(cluster)}
                
            elif task_type == TaskType.DRIFT:
                 # KS Test logic in pipeline, but here we might just predict if it matches ref
                 # Actually drift is usually batch, but individual point check:
                 # compare point to distribution? 
                 # For simplicity, returning "check_pipeline" 
                 result = {"status": "Drift detection requires batch analysis via pipeline"}

            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for {task_type}: {e}")
            raise e

# specific singleton or factory
inference_engine = InferenceEngine()
