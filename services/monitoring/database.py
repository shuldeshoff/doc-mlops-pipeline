"""
Модели базы данных для модуля monitoring
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON

from services.ingestion.database import Base


class PerformanceMetric(Base):
    """Модель метрик производительности"""
    __tablename__ = 'performance_metrics'
    __table_args__ = {'schema': 'metrics'}
    
    id = Column(Integer, primary_key=True)
    service_name = Column(String(100))
    endpoint = Column(String(255))
    response_time = Column(Float)
    status_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
    
    def __repr__(self):
        return (
            f"<PerformanceMetric(service='{self.service_name}', "
            f"endpoint='{self.endpoint}', time={self.response_time:.4f}s)>"
        )

