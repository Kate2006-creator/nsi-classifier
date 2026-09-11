import pandas as pd
import os

def load_data():
    files = {
        'positions': 'data/positions_with_etalon.csv',
        'clusters': 'data/clusters_final.csv',
        'etalons': 'data/etalon_final.csv',
    }
    
    for name, path in files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"Файл {path} не найден!")
    
    df_clean = pd.read_csv(files['positions'])
    cluster_df = pd.read_csv(files['clusters'])
    etalon_df = pd.read_csv(files['etalons'])
    
    return df_clean, cluster_df, etalon_df