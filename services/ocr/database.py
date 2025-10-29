"""
Модели базы данных для модуля OCR
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from services.ingestion.database import Base


class OCRResult(Base):
    """Модель результата OCR обработки"""
    __tablename__ = 'ocr_results'
    __table_args__ = {'schema': 'documents'}
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.documents.id', ondelete='CASCADE'))
    extracted_text = Column(Text)
    language = Column(String(10))
    confidence_score = Column(Float)
    processing_time = Column(Float)
    processed_at = Column(DateTime, default=datetime.utcnow)
    ocr_engine = Column(String(50))
    
    def __repr__(self):
        return (
            f"<OCRResult(id={self.id}, document_id={self.document_id}, "
            f"confidence={self.confidence_score:.2f})>"
        )

