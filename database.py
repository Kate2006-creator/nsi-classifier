from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from models import Base
import numpy as np
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
#Сохраняет эталоны из CSV в БД с эмбеддингами
    from models import Etalon
    
    model = load_model()
    db = SessionLocal()
    
    try:
        db.query(Etalon).delete()
        
        # Получаем все названия эталонов
        etalon_names = etalon_df['etalon_name'].tolist()
        
        # Считаем эмбеддинги для всех эталонов сразу (быстрее)
        print(f"Вычисляем эмбеддинги для {len(etalon_names)} эталонов")
        embeddings = model.encode(etalon_names, show_progress_bar=True)

        for idx, row in etalon_df.iterrows():
            etalon = Etalon(
                cluster_id=row['cluster_id'],
                etalon_name=row['etalon_name'],
                cluster_size=row['cluster_size'],
                embedding=embeddings[idx].tolist() 
            )
            db.add(etalon)
        
        db.commit()
        print(f"Сохранено {len(etalon_df)} эталонов с эмбеддингами в БД")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении эталонов: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def save_positions_to_db(df_clean):
#Сохраняет классифицированные должности в БД с удалением дубликатов
    from models import Position
    db = SessionLocal()
    
    try:
        db.query(Position).delete()
        
        df_clean = df_clean.drop_duplicates(subset=['core_name'], keep='first')

        def safe_float(value):
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        df_clean['cluster'] = df_clean['cluster'].apply(safe_float)
        df_clean = df_clean.dropna(subset=['cluster'])
        
        for _, row in df_clean.iterrows():
            pos = Position(
                core_name=row['core_name'],
                cluster=float(row['cluster']),
                etalon_name=row.get('etalon_name'),
                confidence=float(row.get('confidence', 1.0))
            )
            db.add(pos)
        
        db.commit()
        print(f"Сохранено {len(df_clean)} должностей в БД")
    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении должностей: {e}")
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