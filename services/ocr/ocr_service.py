"""
Сервис OCR для распознавания текста в документах
"""
import os
import io
from typing import Optional, Dict
from datetime import datetime
import numpy as np
from PIL import Image
import cv2
from loguru import logger
import sqlalchemy as sa
from sqlalchemy.orm import Session

from services.ingestion.storage import MinIOStorage
from services.ingestion.database import get_db_connection, Document
from .ocr_engines import OCREngine, TesseractEngine, EasyOCREngine
from .database import OCRResult


class OCRService:
    """Сервис для OCR обработки документов"""
    
    def __init__(
        self,
        engine: Optional[OCREngine] = None,
        storage: Optional[MinIOStorage] = None
    ):
        """
        Инициализация OCR сервиса
        
        Args:
            engine: OCR движок
            storage: Объект хранилища MinIO
        """
        self.engine = engine or TesseractEngine()
        self.storage = storage or MinIOStorage()
        self.bucket_name = os.getenv('MINIO_BUCKET', 'documents')
        logger.info(f"OCRService initialized with engine: {self.engine.__class__.__name__}")
    
    def load_image_from_storage(self, storage_path: str) -> Optional[np.ndarray]:
        """
        Загрузка изображения из хранилища
        
        Args:
            storage_path: Путь к изображению в хранилище
            
        Returns:
            Изображение в формате numpy array или None
        """
        try:
            # Скачивание из MinIO
            image_data = self.storage.download_file(self.bucket_name, storage_path)
            if image_data is None:
                logger.error(f"Failed to download image from {storage_path}")
                return None
            
            # Конвертация в numpy array
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)
            
            # Конвертация RGB -> BGR для OpenCV если необходимо
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            logger.info(f"Image loaded from storage: {storage_path}, shape: {image_np.shape}")
            return image_np
            
        except Exception as e:
            logger.error(f"Error loading image from storage: {e}")
            return None
    
    def process_document(
        self,
        document_id: int,
        language: str = 'eng',
        save_to_db: bool = True
    ) -> Dict:
        """
        OCR обработка документа
        
        Args:
            document_id: ID документа в БД
            language: Язык текста
            save_to_db: Сохранять результат в БД
            
        Returns:
            Словарь с результатами OCR
        """
        start_time = datetime.utcnow()
        
        # Получение информации о документе
        with get_db_connection() as session:
            document = session.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not document:
                logger.error(f"Document {document_id} not found")
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
            storage_path = document.storage_path
        
        # Загрузка изображения
        image = self.load_image_from_storage(storage_path)
        if image is None:
            return {
                'success': False,
                'error': 'Failed to load image'
            }
        
        # OCR обработка
        try:
            extracted_text, confidence = self.engine.extract_text(image, language)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'success': True,
                'document_id': document_id,
                'extracted_text': extracted_text,
                'language': language,
                'confidence_score': confidence,
                'processing_time': processing_time,
                'ocr_engine': self.engine.__class__.__name__,
                'text_length': len(extracted_text),
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Сохранение в БД
            if save_to_db:
                self._save_ocr_result(result)
            
            # Обновление статуса документа
            self._update_document_status(document_id, 'ocr_completed')
            
            logger.info(
                f"OCR processing completed for document {document_id}: "
                f"{len(extracted_text)} chars, confidence: {confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during OCR processing: {e}")
            self._update_document_status(document_id, 'ocr_failed')
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_process_documents(
        self,
        document_ids: list[int],
        language: str = 'eng'
    ) -> list[Dict]:
        """
        Пакетная OCR обработка документов
        
        Args:
            document_ids: Список ID документов
            language: Язык текста
            
        Returns:
            Список результатов OCR
        """
        results = []
        
        for doc_id in document_ids:
            try:
                result = self.process_document(doc_id, language)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")
                results.append({
                    'success': False,
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        successful = sum(1 for r in results if r.get('success', False))
        logger.info(
            f"Batch processing completed: {successful}/{len(document_ids)} successful"
        )
        
        return results
    
    def _save_ocr_result(self, result: Dict) -> None:
        """
        Сохранение результата OCR в БД
        
        Args:
            result: Словарь с результатами OCR
        """
        try:
            with get_db_connection() as session:
                ocr_result = OCRResult(
                    document_id=result['document_id'],
                    extracted_text=result['extracted_text'],
                    language=result['language'],
                    confidence_score=result['confidence_score'],
                    processing_time=result['processing_time'],
                    ocr_engine=result['ocr_engine']
                )
                
                session.add(ocr_result)
                session.commit()
                
                logger.info(f"OCR result saved for document {result['document_id']}")
                
        except Exception as e:
            logger.error(f"Error saving OCR result: {e}")
    
    def _update_document_status(self, document_id: int, status: str) -> None:
        """
        Обновление статуса документа
        
        Args:
            document_id: ID документа
            status: Новый статус
        """
        try:
            with get_db_connection() as session:
                session.query(Document).filter(
                    Document.id == document_id
                ).update({'status': status})
                session.commit()
                
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
    
    def get_ocr_results(self, document_id: int) -> Optional[Dict]:
        """
        Получение результатов OCR для документа
        
        Args:
            document_id: ID документа
            
        Returns:
            Словарь с результатами OCR или None
        """
        try:
            with get_db_connection() as session:
                result = session.query(OCRResult).filter(
                    OCRResult.document_id == document_id
                ).order_by(OCRResult.processed_at.desc()).first()
                
                if not result:
                    return None
                
                return {
                    'id': result.id,
                    'document_id': result.document_id,
                    'extracted_text': result.extracted_text,
                    'language': result.language,
                    'confidence_score': result.confidence_score,
                    'processing_time': result.processing_time,
                    'ocr_engine': result.ocr_engine,
                    'processed_at': result.processed_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting OCR results: {e}")
            return None

