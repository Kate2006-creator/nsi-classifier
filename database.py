from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

model = None

def init_db():
#Создает все таблицы в БД
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")

def get_db():
#Получение сессии БД
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_model():
#Загружает модель 
    global model
    if model is None:
        print("Загрузка модели sentence-transformers...")
        model = SentenceTransformer("sergeyzh/rubert-base-retriever")
        print("Модель загружена")
    return model

def save_etalons_to_db(etalon_df):
    from models import Etalon
    
    model = load_model()
    db = SessionLocal()
    
    try:
        db.query(Etalon).delete()
        
        etalon_names = etalon_df['etalon_name'].tolist()
        
        print(f"Вычисляем эмбеддинги для {len(etalon_names)} эталонов")
        embeddings = model.encode(etalon_names, show_progress_bar=True)
        
        for idx, row in etalon_df.iterrows():
            etalon = Etalon(
                cluster_id=int(row['cluster_id']),
                etalon_name=row['etalon_name'],
                cluster_size=int(row.get('cluster_size', 0)),
                embedding=embeddings[idx].tolist()
            )
            db.add(etalon)
        
        db.commit()
        print(f"Сохранено {len(etalon_df)} эталонов")
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def save_positions_to_db(df_clean):
    from models import Position
    db = SessionLocal()
    
    try:
        db.query(Position).delete()
        
        def safe_float(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_str(value):
            if pd.isna(value):
                return None
            return str(value)
        
        df_clean['cluster'] = df_clean['cluster'].apply(safe_float)
        
        for _, row in df_clean.iterrows():
            pos = Position(
                # Связь с исходной системой
                source_system=safe_str(row.get('source_system')),
                department_code=safe_str(row.get('department_code')),
                position_name=safe_str(row.get('position_name')),
                core_name=safe_str(row.get('cleaned_name')),
                category=safe_str(row.get('category')),
                rate=safe_str(row.get('rate')),
                harm=safe_str(row.get('harm')),
                rank=safe_str(row.get('rank')),
                cluster=safe_float(row.get('cluster')),
                etalon_name=safe_str(row.get('etalon_name')),
                confidence=safe_float(row.get('confidence')),
            )
            db.add(pos)
        
        db.commit()
        print(f"Сохранено {len(df_clean)} должностей")
    except Exception as e:
        db.rollback()
        print(f" Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# Функция для получения всех эмбеддингов эталонов из БД
def get_all_etalon_embeddings(db):
    #Возвращает словарь {etalon_name: embedding} для всех эталонов
    from models import Etalon
    
    etalons = db.query(Etalon).all()
    result = {}
    for etalon in etalons:
        if etalon.embedding is not None:
            result[etalon.etalon_name] = np.array(etalon.embedding)
    return result