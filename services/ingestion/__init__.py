"""
Модуль загрузки документов (Ingestion Service)
"""
from .ingestion_service import IngestionService
from .storage import MinIOStorage

__all__ = ['IngestionService', 'MinIOStorage']

