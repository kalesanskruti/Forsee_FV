# Verification Script for Forsee Intelligence Software
import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath("d:/Forsee_Final/Forsee"))

from models.registry import TaskType
from models.ml import TrainingJob, JobStatus, Dataset
from pipelines.manager import run_training_pipeline
from services.registry_service import ModelRegistryService
from ml.inference import inference_engine
from db.timescaledb import init_timescaledb

# Force unbuffered output
sys.stdout.reconfigure(encoding='utf-8')

# Setup DB Connection (Assuming default docker creds)
DATABASE_URL = "postgresql://postgres:securepassword@localhost:5432/forsee"
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("Connected to Database")
except Exception as e:
    print(f"Failed to connect to DB: {e}")
    sys.exit(1)

def verify_flow():
    db = SessionLocal()
    try:
        # Init Schema
        try:
            init_timescaledb(db)
            print("DB Schema Initialized")
        except Exception as e:
            print(f"Schema Init Warning: {e}")

        print("\n--- 1. Setup Mock Data ---")
        # Ensure a dataset exists
        dataset = db.query(Dataset).filter(Dataset.name == "VerificationDataset").first()
        if not dataset:
            dataset = Dataset(
                name="VerificationDataset",
                source_path="/datasets/verification",
                domain="Test",
                active=True
            )
            db.add(dataset)
            db.commit()
            print(f"Created dataset: {dataset.id}")
        else:
            print(f"Using existing dataset: {dataset.id}")

        # Run for specific types to debug
        model_types = ["CLUSTERING", "DRIFT"]
        # model_types = ["PRECURSOR"]
        
        with open("d:/Forsee_Final/Forsee/verify_debug.log", "w", encoding="utf-8") as log_file:
            def log(msg):
                print(msg)
                log_file.write(msg + "\n")
                log_file.flush()

            for m_type in model_types:
                log(f"\n--- Testing Pipeline: {m_type} ---")
                job = TrainingJob(
                    dataset_id=dataset.id,
                    model_type=m_type,
                    status=JobStatus.PENDING
                )
                db.add(job)
                db.commit()
                log(f"Created Job: {job.id}")
        
                # Run Pipeline with distinct session (Simulating Worker)
                log("Spawning worker session...")
                worker_db = SessionLocal()
                try:
                    run_training_pipeline(job.id, worker_db)
                except Exception as e:
                    log(f"Worker session failed for {m_type}: {e}")
                    import traceback
                    traceback.print_exc(file=log_file)
                finally:
                    worker_db.close()
                    
                # Re-fetch fresh with main session
                db.expire_all()
                job = db.query(TrainingJob).filter(TrainingJob.id == job.id).first()
                
                if job.status == JobStatus.COMPLETED:
                    log(f"Pipeline {m_type} SUCCESS")
                else:
                    log(f"Pipeline {m_type} FAILED. Status: {job.status}. Error: {job.error_message}")
                
        print("\n--- 4. Verify Registry & Inference ---")
        registry = ModelRegistryService(db)
        # Just check RUL for brevity
        active_model = registry.get_active_model(TaskType.RUL)
        if active_model:
            print(f"Found active model: {active_model.name} (Version: {active_model.version})")
            print(f"Artifact Path: {active_model.artifact_path}")
        else:
            print("ERROR: No active model found in registry!")
            return

        print("\n--- 5. Verify Inference Engine ---")
        # Load models explicitly
        inference_engine.load_active_models(db)
        
        # Predict
        print("Testing Prediction...")
        test_data = [[0.5, 0.5], [0.6, 0.6]] # Batch of 2 (seq len 2, features 2) - Wait, pipeline used seq len 5
        # RUL Regressor mocks simple logic, checking implementation:
        # It expects List[List[float]] or just List[float]. 
        # RUL pipeline mock expects `sensor1` etc.
        # "input_data = torch.FloatTensor([data])" -> Adds batch dim if list passed.
        # If I pass [0.1, 0.2], it becomes [[0.1, 0.2]] (Batch=1, Features=2?)
        # SimpleLSTM input_size=2.
        
        try:
            result = inference_engine.predict(TaskType.RUL, [0.1, 0.2])
            print(f"Prediction Result: {result}")
        except Exception as e:
            print(f"Prediction Failed: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    verify_flow()
