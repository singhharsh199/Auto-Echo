import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
import warnings

# Suppress ConvergenceWarnings from GMM for clean output
warnings.filterwarnings("ignore")

def evaluate_clusters(X, labels):
    """Calculate Silhouette Score to evaluate cluster quality."""
    if len(set(labels)) < 2:
        return -1.0 # Invalid clustering
    return silhouette_score(X, labels, sample_size=10000, random_state=42) # Sample to speed up computation

def discover_memory_levels_kmeans(df: pd.DataFrame, column: str = 'latency_ns', max_k: int = 7) -> tuple:
    """
    Automatically determine the number of memory levels using K-Means and Silhouette Score.
    """
    X = df[[column]].values
    best_k = 2
    best_score = -1.0
    best_model = None
    
    print("Evaluating K-Means models...")
    for k in range(2, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        score = evaluate_clusters(X, labels)
        print(f"  k={k}, Silhouette Score: {score:.4f}")
        
        if score > best_score:
            best_score = score
            best_k = k
            best_model = kmeans
            
    print(f"Optimal number of levels (K-Means): {best_k}")
    
    df_result = df.copy()
    df_result['cluster'] = best_model.predict(X)
    return df_result, best_model

def discover_memory_levels_gmm(df: pd.DataFrame, column: str = 'latency_ns', max_k: int = 7) -> tuple:
    """
    Automatically determine the number of memory levels using Gaussian Mixture Models and BIC/Silhouette.
    """
    X = df[[column]].values
    best_k = 2
    best_score = -1.0
    best_model = None
    
    print("Evaluating GMM models...")
    for k in range(2, max_k + 1):
        gmm = GaussianMixture(n_components=k, random_state=42)
        labels = gmm.fit_predict(X)
        score = evaluate_clusters(X, labels)
        print(f"  k={k}, Silhouette Score: {score:.4f}")
        
        if score > best_score:
            best_score = score
            best_k = k
            best_model = gmm
            
    print(f"Optimal number of levels (GMM): {best_k}")
    
    df_result = df.copy()
    df_result['cluster'] = best_model.predict(X)
    return df_result, best_model

def map_clusters_to_levels(df: pd.DataFrame, column: str = 'latency_ns') -> tuple:
    """
    Map unordered cluster IDs to logical memory levels (L1, L2, L3, etc.) by sorting them based on mean latency.
    Attaches 'level_name' and 'inferred_level' columns to the DataFrame and returns (df, cluster_stats).
    """
    # Calculate stats for each cluster
    cluster_stats = df.groupby('cluster')[column].agg(['min', 'max', 'mean', 'count']).reset_index()
    
    # Sort clusters by mean latency
    cluster_stats = cluster_stats.sort_values(by='mean').reset_index(drop=True)
    
    # Latency-ordered commodity cache-hierarchy names. "WPQ" (a persistent-memory
    # / write-pending-queue concept from Klimis et al.'s Optane setup) is
    # deliberately excluded: it does not exist on a commodity CPU cache hierarchy.
    level_names = [
        'L1 Cache',
        'L2 Cache',
        'L3 Cache',
        'DRAM',
        'Deeper / Swap'
    ]
    
    num_clusters = len(cluster_stats)
    assigned_names = level_names[:num_clusters] if num_clusters <= len(level_names) else [f'Level {i}' for i in range(1, num_clusters + 1)]
    
    cluster_stats['Level_Name'] = assigned_names
    cluster_stats['Display_Label'] = cluster_stats.apply(
        lambda row: f"{row['Level_Name']} (~{row['mean']:.1f} ns)", axis=1
    )
    
    # Mappings
    cluster_to_name = dict(zip(cluster_stats['cluster'], cluster_stats['Level_Name']))
    cluster_to_label = dict(zip(cluster_stats['cluster'], cluster_stats['Display_Label']))
    
    df_result = df.copy()
    df_result['level_name'] = df_result['cluster'].map(cluster_to_name)
    df_result['inferred_level'] = df_result['cluster'].map(cluster_to_label)
    
    return df_result, cluster_stats

