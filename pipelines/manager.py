from sqlalchemy.orm import Session
from models.ml import TrainingJob, JobStatus, Dataset, MLModel
from models.registry import TaskType
from pipelines.training import (
    RULRegressionPipeline, 
    PrecursorClassificationPipeline, 
    ScaniaCostPipeline, 
    MetroPTPredictivePipeline, 
    MIMIIAnomalyPipeline, 
    PHMFaultPipeline, 
    AwesomeRegressionPipeline,
    ClusteringPipeline, 
    DriftDetectionPipeline
)
from uuid import UUID
import traceback
import os

def run_training_pipeline(job_id: UUID, db: Session):
    # 1. Initial Fetch to get parameters
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        print(f"Job {job_id} not found")
        return
        
    dataset_id = job.dataset_id
    model_type_str = job.model_type
    
    # 2. Update Status to RUNNING
    try:
        print(f"Starting pipeline for Job {job_id}...")
        job.status = JobStatus.RUNNING
        db.commit()
    except Exception as e:
        print(f"Failed to start job: {e}")
        db.rollback()
        return

    # From here on, DO NOT USE 'job' instance. It might be expired/detached.
    
    try:
        # 3. Determine paths & Dataset info
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
            
        dataset_name_safe = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in dataset.name).strip()
        dataset_name_lower = dataset.name.lower()
        
        base_datasets_path = os.getenv("DATASETS_PATH", "datasets") # Use local path as default for demo
        dataset_path = os.path.join(base_datasets_path, dataset_name_safe)
        
        models_path = os.getenv("MODELS_PATH", "datasets/models")
        
        # 4. Select Pipeline
        model_type = model_type_str.lower()
        pipeline = None
        task_type = None
        
        if "nasa" in dataset_name_lower or "rul" in model_type:
            pipeline = RULRegressionPipeline(db, dataset_path, f"{models_path}/rul", {})
            task_type = TaskType.RUL
        elif "ai4i" in dataset_name_lower or "classification" in model_type:
            pipeline = PrecursorClassificationPipeline(db, dataset_path, f"{models_path}/precursor", {})
            task_type = TaskType.PRECURSOR
        elif "scania" in dataset_name_lower:
            pipeline = ScaniaCostPipeline(db, dataset_path, f"{models_path}/scania", {})
            task_type = TaskType.PRECURSOR
        elif "metro" in dataset_name_lower:
            pipeline = MetroPTPredictivePipeline(db, dataset_path, f"{models_path}/metro", {})
            task_type = TaskType.PRECURSOR
        elif "mimii" in dataset_name_lower:
            pipeline = MIMIIAnomalyPipeline(db, dataset_path, f"{models_path}/mimii", {})
            task_type = TaskType.CLUSTERING
        elif "phm" in dataset_name_lower:
            pipeline = PHMFaultPipeline(db, dataset_path, f"{models_path}/phm", {})
            task_type = TaskType.PRECURSOR
        elif "awesome" in dataset_name_lower:
            pipeline = AwesomeRegressionPipeline(db, dataset_path, f"{models_path}/awesome", {})
            task_type = TaskType.RUL
        elif "cluster" in model_type:
             pipeline = ClusteringPipeline(db, dataset_path, f"{models_path}/clustering", {})
             task_type = TaskType.CLUSTERING
        elif "drift" in model_type:
             pipeline = DriftDetectionPipeline(db, dataset_path, f"{models_path}/drift", {})
             task_type = TaskType.DRIFT
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # 5. Run Pipeline
        dataset_name = dataset.name
        metrics = pipeline.run(
            pipeline_name=f"{model_type}_model",
            version="v1.0.0", 
            task_type=task_type,
            dataset_name=dataset_name
        )
        
        # 6. Success: Re-fetch job to update status
        # Note: pipeline.run commits (via registry), so previous objects are expired.
        # We start a fresh transaction for status update.
        job_final = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if job_final:
            job_final.status = JobStatus.COMPLETED
            job_final.accuracy = float(metrics.get("accuracy") or metrics.get("r2_score") or metrics.get("mse") or 0.0)
            db.commit()
            print(f"Job {job_id} COMPLETED. Metrics: {metrics}")
        
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        traceback.print_exc()
        try:
            db.rollback() 
            # Re-fetch for error logging
            job_err = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if job_err:
                job_err.status = JobStatus.FAILED
                job_err.error_message = str(e)
                db.commit()
                print(f"Job {job_id} FAILED. Error saved.")
        except Exception as commit_err:
            print(f"CRITICAL: Failed to save error status: {commit_err}")
            traceback.print_exc()
