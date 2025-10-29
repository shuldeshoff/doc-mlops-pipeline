"""
Модуль OCR для извлечения текста из документов
"""
from .ocr_service import OCRService
from .ocr_engines import TesseractEngine, EasyOCREngine

__all__ = ['OCRService', 'TesseractEngine', 'EasyOCREngine']

