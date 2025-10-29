"""
Модели базы данных для модуля inference
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey

from services.ingestion.database import Base


class Prediction(Base):
    """Модель предсказания класса документа"""
    __tablename__ = 'predictions'
    __table_args__ = {'schema': 'documents'}
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.documents.id', ondelete='CASCADE'))
    model_name = Column(String(100))
    model_version = Column(String(50))
    predicted_class = Column(String(100))
    confidence_score = Column(Float)
    all_scores = Column(JSON)
    predicted_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return (
            f"<Prediction(id={self.id}, document_id={self.document_id}, "
            f"class='{self.predicted_class}', confidence={self.confidence_score:.2f})>"
        )

