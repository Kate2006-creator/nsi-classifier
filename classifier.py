import pandas as pd

def load_data():
#Загружает данные из CSV файлов
    df_clean = pd.read_csv('data/cleaned_positions.csv')
    cluster_df = pd.read_csv('data/clusters_final.csv')
    etalon_df = pd.read_csv('data/etalon_final.csv')
    
    return df_clean, cluster_df, etalon_df

def classify_position(name, df_clean, etalon_df):
#Классифицирует одну должность
    cluster_to_etalon = dict(zip(etalon_df['cluster_id'], etalon_df['etalon_name']))
    name_to_cluster = dict(zip(df_clean['core_name'], df_clean['cluster']))
    
    cluster = name_to_cluster.get(name.lower().strip())
    if cluster is not None:
        etalon = cluster_to_etalon.get(cluster)
        return {
            "position": name,
            "cluster": int(cluster),
            "etalon": etalon,
            "found": True
        }
    return {
        "position": name,
        "cluster": None,
        "etalon": None,
        "found": False
    }