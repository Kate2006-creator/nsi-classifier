from sqlalchemy import Column, Integer, String, Float, DateTime, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Etalon(Base):
    #Таблица с эталонными должностями
    __tablename__ = 'etalons'
    
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, unique=True, nullable=False)
    etalon_name = Column(String(255), nullable=False)
    cluster_size = Column(Integer, default=0)
    embedding = Column(ARRAY(Float), nullable=True)  
    created_at = Column(DateTime, default=datetime.now)

class Position(Base):
    #Таблица со всеми должностями и их классификацией
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    core_name = Column(String(255), nullable=False, unique=True)
    cluster = Column(Float)
    etalon_name = Column(String(255))
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class ClassificationLog(Base):
    #Лог запросов к классификатору
    __tablename__ = 'classification_logs'
    
    id = Column(Integer, primary_key=True)
    query = Column(String(255), nullable=False)
    result = Column(String(255))
    timestamp = Column(DateTime, default=datetime.now)