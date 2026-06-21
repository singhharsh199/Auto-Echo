import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor

def remove_outliers_iqr(df: pd.DataFrame, column: str = 'latency_ns', multiplier: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers using the Interquartile Range (IQR) method.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)].copy()

def remove_outliers_lof(df: pd.DataFrame, column: str = 'latency_ns', contamination: float = 0.01) -> pd.DataFrame:
    """
    Remove outliers using the Local Outlier Factor (LOF) method.
    Recommended by the ECOOP 2025 paper for micro-architectural noise filtering.
    """
    # LOF can be slow for millions of rows. It's recommended to subsample or use a small n_neighbors.
    # We use a default contamination rate of 1%
    X = df[[column]].values
    lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination, n_jobs=-1)
    
    # predict returns 1 for inliers, -1 for outliers
    y_pred = lof.fit_predict(X)
    
    return df[y_pred == 1].copy()

def apply_moving_average(df: pd.DataFrame, column: str = 'latency_ns', window: int = 5) -> pd.DataFrame:
    """
    Apply a simple moving average to smooth out transient noise.
    """
    smoothed_df = df.copy()
    smoothed_df[column] = smoothed_df[column].rolling(window=window, center=True).mean()
    
    # Drop NaN values introduced by rolling window at the edges
    smoothed_df = smoothed_df.dropna().reset_index(drop=True)
    return smoothed_df

def preprocess_pipeline(df: pd.DataFrame, use_lof: bool = False) -> pd.DataFrame:
    """
    Run the full recommended preprocessing pipeline.
    """
    print(f"Original dataset size: {len(df)}")
    
    # Step 1: Broad filtering of extreme anomalies (e.g. context switches > 1ms)
    # 1,000,000 ns = 1 ms
    clean_df = df[df['latency_ns'] < 1000000].copy() 
    
    # Step 2: Advanced Outlier Detection
    if use_lof:
        # LOF is more robust but computationally expensive
        clean_df = remove_outliers_lof(clean_df)
    else:
        # IQR is faster
        clean_df = remove_outliers_iqr(clean_df, multiplier=3.0)
    
    print(f"After outlier removal: {len(clean_df)}")
    
    # Step 3: Moving Average Smoothing
    clean_df = apply_moving_average(clean_df, window=5)
    print(f"Final dataset size after smoothing: {len(clean_df)}")
    
    return clean_df
