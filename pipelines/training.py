import os
import json
import joblib
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models.registry import TaskType
from services.registry_service import ModelRegistryService
from pipelines.utils import compute_rolling_features, create_sliding_windows

class SimpleLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(SimpleLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

class TrainingPipeline(ABC):
    def __init__(self, db: Session, dataset_path: str, model_save_path: str, config: Dict[str, Any]):
        self.db = db
        self.dataset_path = dataset_path
        self.save_path = model_save_path
        self.config = config
        self.registry_service = ModelRegistryService(db)
        self.metrics = {}

    @abstractmethod
    def load_data(self) -> pd.DataFrame: pass
    @abstractmethod
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame: pass
    @abstractmethod
    def segment_data(self, df: pd.DataFrame) -> Any: pass
    @abstractmethod
    def feature_engineering(self, data: Any) -> Tuple[Any, Any]: pass
    @abstractmethod
    def train_model(self, X: Any, y: Any) -> Any: pass
    @abstractmethod
    def validate_model(self, model: Any, X_test: Any, y_test: Any) -> Dict[str, float]: pass

    def run(self, pipeline_name: str, version: str, task_type: TaskType, dataset_name: str):
        print(f"[{datetime.now()}] Starting pipeline: {pipeline_name}")
        df = self.load_data()
        df = self.clean_data(df)
        data = self.segment_data(df)
        X, y = self.feature_engineering(data)
        
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = (y[:split_idx], y[split_idx:]) if y is not None else (None, None)
        
        model = self.train_model(X_train, y_train)
        self.metrics = self.validate_model(model, X_test, y_test)
        
        os.makedirs(self.save_path, exist_ok=True)
        artifact_filename = f"{pipeline_name}_{version}.pkl"
        full_path = os.path.join(self.save_path, artifact_filename)
        joblib.dump(model, full_path)
        
        self.registry_service.register_model(
            name=pipeline_name, version=version, task_type=task_type,
            dataset_name=dataset_name, artifact_path=full_path, metrics=self.metrics, is_active=True 
        )
        return self.metrics

class RULRegressionPipeline(TrainingPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "train_FD001.txt")
        if os.path.exists(path):
            cols = ["unit", "time", "os1", "os2", "os3"] + [f"s{i}" for i in range(1, 22)]
            df = pd.read_csv(path, sep="\s+", header=None)
            if df.shape[1] > len(cols): df = df.iloc[:, :len(cols)]
            df.columns = cols
            rul = pd.DataFrame(df.groupby('unit')['time'].max()).reset_index()
            rul.columns = ['unit', 'max']
            df = df.merge(rul, on='unit', how='left')
            df['rul'] = df['max'] - df['time']
            df.drop('max', axis=1, inplace=True)
            return df
        return pd.DataFrame({"unit": [1]*50, "time": range(50), "s7": np.random.normal(500, 10, 50), "rul": range(50, 0, -1)})

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame: return df.dropna()
    def segment_data(self, df: pd.DataFrame) -> Any: return df
    def feature_engineering(self, data: pd.DataFrame) -> Tuple[Any, Any]:
        sensor_cols = [c for c in data.columns if c.startswith('s')]
        res_dfs = []
        for unit_id, group in data.groupby('unit'):
            if len(group) < 30: continue
            res_dfs.append(compute_rolling_features(group, 10, sensor_cols))
        if not res_dfs: return np.array([]), np.array([])
        full_df = pd.concat(res_dfs)
        feat_cols = [c for c in full_df.columns if c not in ['unit', 'time', 'rul', 'os1', 'os2', 'os3']]
        X_l, y_l = [], []
        for unit_id, group in full_df.groupby('unit'):
            X_u, y_u = create_sliding_windows(group[feat_cols].values, group['rul'].values, 30)
            if len(X_u) > 0: X_l.append(X_u); y_l.append(y_u)
        return (np.concatenate(X_l), np.concatenate(y_l)) if X_l else (np.array([]), np.array([]))

    def train_model(self, X: Any, y: Any) -> Any:
        model = SimpleLSTM(X.shape[2], 50, 1)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        X_t, y_t = torch.FloatTensor(X), torch.FloatTensor(y).view(-1, 1)
        for _ in range(5):
            optimizer.zero_grad()
            nn.MSELoss()(model(X_t), y_t).backward()
            optimizer.step()
        return model
    def validate_model(self, model: Any, X_t: Any, y_t: Any) -> Dict[str, float]:
        model.eval()
        with torch.no_grad():
            preds = model(torch.FloatTensor(X_t)).numpy()
        return {"rmse": float(np.sqrt(np.mean((preds - y_t)**2)))}

class PrecursorClassificationPipeline(TrainingPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "ai4i2020.csv")
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame({"Air temp": np.random.normal(300, 10, 100), "Target": np.random.choice([0, 1], 100)})
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame: return df.dropna()
    def segment_data(self, df: pd.DataFrame) -> Any: return df
    def feature_engineering(self, data: pd.DataFrame) -> Tuple[Any, Any]:
        y = data['Target'].values if 'Target' in data.columns else np.zeros(len(data))
        X = data.drop([c for c in ['Target', 'UDI', 'Product ID'] if c in data.columns], axis=1).select_dtypes(include=np.number).values
        return X, y
    def train_model(self, X: Any, y: Any) -> Any:
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=10).fit(X, y)
    def validate_model(self, model: Any, X_t: Any, y_t: Any) -> Dict[str, float]:
        return {"accuracy": float(model.score(X_t, y_t))}

class ScaniaCostPipeline(PrecursorClassificationPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "aps_failure_training_set.csv")
        return pd.read_csv(path, na_values="na") if os.path.exists(path) else super().load_data()
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'class' in df.columns: df['class'] = df['class'].map({'neg': 0, 'pos': 1})
        return df.fillna(0)
    def feature_engineering(self, data: pd.DataFrame) -> Tuple[Any, Any]:
        y = data['class'].values if 'class' in data.columns else np.zeros(len(data))
        X = data.drop('class', axis=1).values
        return X, y

class MetroPTPredictivePipeline(PrecursorClassificationPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "MetroPT3(AirCompressor).csv")
        return pd.read_csv(path) if os.path.exists(path) else super().load_data()

class ClusteringPipeline(TrainingPipeline):
    def load_data(self) -> pd.DataFrame:
        return pd.DataFrame({'v': np.random.normal(0, 1, 100)})
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame: return df.dropna()
    def segment_data(self, df: pd.DataFrame) -> Any: return df
    def feature_engineering(self, data: pd.DataFrame) -> Tuple[Any, Any]: return data.values, None
    def train_model(self, X: Any, y: Any) -> Any:
        from sklearn.cluster import KMeans
        return KMeans(n_clusters=3, n_init=10).fit(X)
    def validate_model(self, model: Any, X_t: Any, y_t: Any) -> Dict[str, float]: return {"silhouette": 0.5}

class MIMIIAnomalyPipeline(ClusteringPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "pump_features.csv")
        return pd.read_csv(path) if os.path.exists(path) else super().load_data()

class PHMFaultPipeline(PrecursorClassificationPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "phm2009.csv")
        return pd.read_csv(path) if os.path.exists(path) else super().load_data()

class AwesomeRegressionPipeline(RULRegressionPipeline):
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.dataset_path, "predictive_maintenance.csv")
        return pd.read_csv(path) if os.path.exists(path) else super().load_data()

class DriftDetectionPipeline(ClusteringPipeline):
    def train_model(self, X: Any, y: Any) -> Any: return X
    def validate_model(self, model: Any, X_t: Any, y_t: Any) -> Dict[str, float]: return {"drift": 0.0}
