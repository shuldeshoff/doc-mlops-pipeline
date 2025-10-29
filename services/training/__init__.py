"""
Модуль обучения моделей классификации документов
"""
from .training_service import TrainingService
from .models import DocumentClassifier

__all__ = ['TrainingService', 'DocumentClassifier']

