"""
Модуль inference для предсказаний классов документов
"""
from .inference_service import InferenceService
from .model_loader import ModelLoader

__all__ = ['InferenceService', 'ModelLoader']

