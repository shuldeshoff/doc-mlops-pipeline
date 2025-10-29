"""
Движки OCR для распознавания текста
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import time
import cv2
import numpy as np
from PIL import Image
from loguru import logger

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available")


class OCREngine(ABC):
    """Базовый класс для OCR движков"""
    
    @abstractmethod
    def extract_text(
        self,
        image: np.ndarray,
        language: str = 'eng'
    ) -> Tuple[str, float]:
        """
        Извлечение текста из изображения
        
        Args:
            image: Изображение в формате numpy array
            language: Язык текста
            
        Returns:
            Кортеж (текст, confidence score)
        """
        pass
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Предобработка изображения для улучшения OCR
        
        Args:
            image: Входное изображение
            
        Returns:
            Обработанное изображение
        """
        # Конвертация в grayscale если необходимо
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Бинаризация (адаптивный порог)
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Удаление шума
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        return denoised


class TesseractEngine(OCREngine):
    """OCR движок на основе Tesseract"""
    
    def __init__(self, config: Optional[str] = None):
        """
        Инициализация Tesseract движка
        
        Args:
            config: Дополнительная конфигурация Tesseract
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("pytesseract is not installed")
        
        self.config = config or '--oem 3 --psm 6'
        logger.info(f"TesseractEngine initialized with config: {self.config}")
    
    def extract_text(
        self,
        image: np.ndarray,
        language: str = 'eng'
    ) -> Tuple[str, float]:
        """
        Извлечение текста с помощью Tesseract
        
        Args:
            image: Изображение в формате numpy array
            language: Язык текста ('eng', 'rus', 'eng+rus')
            
        Returns:
            Кортеж (текст, confidence score)
        """
        start_time = time.time()
        
        try:
            # Предобработка
            processed_image = self.preprocess_image(image)
            
            # Распознавание текста
            text = pytesseract.image_to_string(
                processed_image,
                lang=language,
                config=self.config
            )
            
            # Получение confidence score
            data = pytesseract.image_to_data(
                processed_image,
                lang=language,
                config=self.config,
                output_type=pytesseract.Output.DICT
            )
            
            # Вычисление среднего confidence
            confidences = [
                float(conf) for conf in data['conf']
                if conf != '-1' and str(conf).replace('.', '', 1).isdigit()
            ]
            
            avg_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0.0
            )
            
            processing_time = time.time() - start_time
            logger.info(
                f"Tesseract OCR completed in {processing_time:.2f}s, "
                f"confidence: {avg_confidence:.2f}%"
            )
            
            return text.strip(), avg_confidence / 100.0
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return "", 0.0


class EasyOCREngine(OCREngine):
    """OCR движок на основе EasyOCR"""
    
    def __init__(self, gpu: bool = False):
        """
        Инициализация EasyOCR движка
        
        Args:
            gpu: Использовать GPU
        """
        if not EASYOCR_AVAILABLE:
            raise RuntimeError("EasyOCR is not installed")
        
        self.gpu = gpu
        self.reader = None
        self._initialized_languages = set()
        logger.info(f"EasyOCREngine initialized (GPU: {gpu})")
    
    def _get_reader(self, language: str):
        """Получение или создание reader для языка"""
        # Преобразование кодов языков
        lang_map = {
            'eng': 'en',
            'rus': 'ru',
            'eng+rus': ['en', 'ru']
        }
        
        languages = lang_map.get(language, 'en')
        if isinstance(languages, str):
            languages = [languages]
        
        # Создание нового reader если необходимо
        lang_key = tuple(sorted(languages))
        if self.reader is None or lang_key not in self._initialized_languages:
            self.reader = easyocr.Reader(
                languages,
                gpu=self.gpu,
                verbose=False
            )
            self._initialized_languages.add(lang_key)
            logger.info(f"EasyOCR reader created for languages: {languages}")
        
        return self.reader
    
    def extract_text(
        self,
        image: np.ndarray,
        language: str = 'eng'
    ) -> Tuple[str, float]:
        """
        Извлечение текста с помощью EasyOCR
        
        Args:
            image: Изображение в формате numpy array
            language: Язык текста ('eng', 'rus', 'eng+rus')
            
        Returns:
            Кортеж (текст, confidence score)
        """
        start_time = time.time()
        
        try:
            reader = self._get_reader(language)
            
            # Распознавание текста
            results = reader.readtext(image)
            
            if not results:
                return "", 0.0
            
            # Объединение текста и вычисление среднего confidence
            texts = []
            confidences = []
            
            for bbox, text, conf in results:
                texts.append(text)
                confidences.append(conf)
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = time.time() - start_time
            logger.info(
                f"EasyOCR completed in {processing_time:.2f}s, "
                f"confidence: {avg_confidence:.2f}"
            )
            
            return full_text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return "", 0.0


class EnsembleOCREngine(OCREngine):
    """Ансамбль OCR движков для повышения точности"""
    
    def __init__(self, engines: list[OCREngine], voting_strategy: str = 'confidence'):
        """
        Инициализация ансамбля движков
        
        Args:
            engines: Список OCR движков
            voting_strategy: Стратегия выбора результата ('confidence', 'majority')
        """
        self.engines = engines
        self.voting_strategy = voting_strategy
        logger.info(
            f"EnsembleOCREngine initialized with {len(engines)} engines, "
            f"strategy: {voting_strategy}"
        )
    
    def extract_text(
        self,
        image: np.ndarray,
        language: str = 'eng'
    ) -> Tuple[str, float]:
        """
        Извлечение текста с использованием ансамбля движков
        
        Args:
            image: Изображение в формате numpy array
            language: Язык текста
            
        Returns:
            Кортеж (текст, confidence score)
        """
        results = []
        
        for engine in self.engines:
            try:
                text, confidence = engine.extract_text(image, language)
                results.append((text, confidence, engine.__class__.__name__))
            except Exception as e:
                logger.warning(f"Engine {engine.__class__.__name__} failed: {e}")
        
        if not results:
            return "", 0.0
        
        # Выбор лучшего результата
        if self.voting_strategy == 'confidence':
            # Выбор результата с максимальной уверенностью
            best_result = max(results, key=lambda x: x[1])
            logger.info(f"Best result from {best_result[2]} with confidence {best_result[1]:.2f}")
            return best_result[0], best_result[1]
        
        # Другие стратегии можно добавить здесь
        return results[0][0], results[0][1]

