from sqlalchemy import Column, Integer, String, Float, DateTime, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Etalon(Base):
    __tablename__ = 'etalons'
    
    id = Column(Integer, primary_key=True)
    cluster_id = Column(Integer, unique=True, nullable=False)
    etalon_name = Column(String(255), nullable=False)
    cluster_size = Column(Integer, default=0)
    embedding = Column(ARRAY(Float), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    
    source_system = Column(String(50), nullable=True)
    department_code = Column(String(50), nullable=True)
    position_name = Column(String(500), nullable=True)   
    core_name = Column(String(255), nullable=True)      
    category = Column(String(50), nullable=True)  
    rate = Column(String(20), nullable=True)      
    harm = Column(String(20), nullable=True)     
    rank = Column(String(10), nullable=True)      
    cluster = Column(Float, nullable=True)
    etalon_name = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)     
    created_at = Column(DateTime, default=datetime.now)


class ClassificationLog(Base):
    __tablename__ = 'classification_logs'
    
    id = Column(Integer, primary_key=True)
    query = Column(String(255), nullable=False)
    result = Column(String(255))
    timestamp = Column(DateTime, default=datetime.now)