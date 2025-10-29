"""
Модели базы данных для модуля training
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON

from services.ingestion.database import Base


class ModelMetrics(Base):
    """Модель метрик обученных моделей"""
    __tablename__ = 'model_metrics'
    __table_args__ = {'schema': 'models'}
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100))
    model_version = Column(String(50))
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    dataset_size = Column(Integer)
    training_time = Column(Float)
    trained_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
    
    def __repr__(self):
        return (
            f"<ModelMetrics(model_name='{self.model_name}', "
            f"version='{self.model_version}', accuracy={self.accuracy:.4f})>"
        )

