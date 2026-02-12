import pandas as pd
import numpy as np
from typing import List, Tuple

def compute_rolling_features(df: pd.DataFrame, window_size: int, columns: List[str]) -> pd.DataFrame:
    """
    Computes rolling mean, std, and slope for specified columns.
    """
    res = df.copy()
    
    for col in columns:
        # Rolling Mean & Std
        res[f"{col}_mean"] = df[col].rolling(window=window_size).mean()
        res[f"{col}_std"] = df[col].rolling(window=window_size).std()
        
        # Simple Rate of Change (Slope approximation: current - prev / 1)
        res[f"{col}_roc"] = df[col].diff()
        
        # Slope over window (simplified: (last - first) / window)
        # For more accurate slope, use polyfit on rolling window, but expensive.
        # Approximation: mean of differences in window? Or just diff(window)
        res[f"{col}_slope"] = df[col].diff(periods=window_size) / window_size
        
    return res.dropna()

def create_sliding_windows(data: np.ndarray, target: np.ndarray, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Creates sequences for LSTM/RNN models.
    Input data shape: (N, features)
    Output X shape: (N - seq_len, seq_len, features)
    Output y shape: (N - seq_len,)
    """
    sequences = []
    targets = []
    
    # Validation
    if len(data) <= sequence_length:
        return np.array([]), np.array([])
        
    for i in range(len(data) - sequence_length):
        sequences.append(data[i:i+sequence_length])
        targets.append(target[i+sequence_length]) # Next step target or current step RUL?
        # Usually for RUL, target is RUL at the end of the sequence window.
        
    return np.array(sequences), np.array(targets)
