"""
Сервис загрузки и первичной обработки документов
"""
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, BinaryIO
import io
from PIL import Image
from loguru import logger
import sqlalchemy as sa
from sqlalchemy.orm import Session

from .storage import MinIOStorage
from .database import get_db_connection, Document


class IngestionService:
    """Сервис для загрузки и обработки входящих документов"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.pdf', '.bmp'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    def __init__(self, storage: Optional[MinIOStorage] = None):
        """
        Инициализация сервиса
        
        Args:
            storage: Объект хранилища MinIO
        """
        self.storage = storage or MinIOStorage()
        self.bucket_name = os.getenv('MINIO_BUCKET', 'documents')
        self.storage.ensure_bucket(self.bucket_name)
        logger.info("IngestionService initialized")
    
    def validate_file(self, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Валидация файла перед загрузкой
        
        Args:
            filename: Имя файла
            file_size: Размер файла в байтах
            
        Returns:
            Кортеж (валидность, сообщение об ошибке)
        """
        # Проверка расширения
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False, f"Недопустимое расширение файла. Разрешены: {self.ALLOWED_EXTENSIONS}"
        
        # Проверка размера
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"Файл слишком большой. Максимум: {max_mb} MB"
        
        return True, None
    
    def calculate_file_hash(self, file_data: bytes) -> str:
        """
        Вычисление SHA-256 хеша файла
        
        Args:
            file_data: Данные файла
            
        Returns:
            Хеш строка
        """
        return hashlib.sha256(file_data).hexdigest()
    
    def preprocess_image(self, file_data: bytes) -> Optional[bytes]:
        """
        Предобработка изображения (нормализация, конвертация)
        
        Args:
            file_data: Данные изображения
            
        Returns:
            Обработанные данные или None
        """
        try:
            image = Image.open(io.BytesIO(file_data))
            
            # Конвертация в RGB если необходимо
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Ограничение максимального размера
            max_dimension = 4096
            if max(image.size) > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                logger.info(f"Image resized to {image.size}")
            
            # Сохранение в буфер
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            return buffer.read()
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    def ingest_document(
        self,
        filename: str,
        file_data: BinaryIO,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Загрузка документа в систему
        
        Args:
            filename: Имя файла
            file_data: Данные файла
            metadata: Дополнительные метаданные
            
        Returns:
            Словарь с информацией о загруженном документе
        """
        # Чтение данных
        file_data.seek(0)
        data = file_data.read()
        file_size = len(data)
        
        # Валидация
        is_valid, error_msg = self.validate_file(filename, file_size)
        if not is_valid:
            logger.warning(f"File validation failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        # Вычисление хеша
        file_hash = self.calculate_file_hash(data)
        
        # Генерация уникального имени в хранилище
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_ext = Path(filename).suffix
        storage_filename = f"{timestamp}_{file_hash[:8]}{file_ext}"
        storage_path = f"raw/{storage_filename}"
        
        # Предобработка для изображений
        file_ext_lower = file_ext.lower()
        if file_ext_lower in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}:
            processed_data = self.preprocess_image(data)
            if processed_data:
                data = processed_data
                logger.info("Image preprocessed successfully")
        
        # Загрузка в MinIO
        upload_success = self.storage.upload_file(
            bucket_name=self.bucket_name,
            object_name=storage_path,
            file_data=io.BytesIO(data),
            content_type=self._get_content_type(file_ext),
            metadata=metadata or {}
        )
        
        if not upload_success:
            return {
                'success': False,
                'error': 'Ошибка загрузки в хранилище'
            }
        
        # Сохранение метаданных в БД
        try:
            db_record = self._save_to_database(
                filename=filename,
                storage_path=storage_path,
                file_size=file_size,
                file_hash=file_hash,
                metadata=metadata
            )
            
            logger.info(f"Document ingested successfully: {filename} (ID: {db_record['id']})")
            
            return {
                'success': True,
                'document_id': db_record['id'],
                'filename': filename,
                'storage_path': storage_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'timestamp': db_record['upload_timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            # Попытка удалить файл из хранилища
            self.storage.delete_file(self.bucket_name, storage_path)
            return {
                'success': False,
                'error': f'Ошибка сохранения в БД: {str(e)}'
            }
    
    def _get_content_type(self, file_ext: str) -> str:
        """Определение MIME типа по расширению"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.pdf': 'application/pdf',
            '.bmp': 'image/bmp'
        }
        return content_types.get(file_ext.lower(), 'application/octet-stream')
    
    def _save_to_database(
        self,
        filename: str,
        storage_path: str,
        file_size: int,
        file_hash: str,
        metadata: Optional[dict]
    ) -> dict:
        """
        Сохранение метаданных документа в БД
        
        Args:
            filename: Имя файла
            storage_path: Путь в хранилище
            file_size: Размер файла
            file_hash: Хеш файла
            metadata: Дополнительные метаданные
            
        Returns:
            Словарь с данными записи
        """
        with get_db_connection() as session:
            file_ext = Path(filename).suffix
            
            doc = Document(
                filename=filename,
                storage_path=storage_path,
                file_size=file_size,
                mime_type=self._get_content_type(file_ext),
                status='uploaded',
                metadata={
                    'file_hash': file_hash,
                    **(metadata or {})
                }
            )
            
            session.add(doc)
            session.commit()
            session.refresh(doc)
            
            return {
                'id': doc.id,
                'filename': doc.filename,
                'upload_timestamp': doc.upload_timestamp
            }
    
    def get_document_info(self, document_id: int) -> Optional[dict]:
        """
        Получение информации о документе
        
        Args:
            document_id: ID документа
            
        Returns:
            Словарь с информацией о документе
        """
        try:
            with get_db_connection() as session:
                doc = session.query(Document).filter(
                    Document.id == document_id
                ).first()
                
                if not doc:
                    return None
                
                return {
                    'id': doc.id,
                    'filename': doc.filename,
                    'storage_path': doc.storage_path,
                    'file_size': doc.file_size,
                    'mime_type': doc.mime_type,
                    'status': doc.status,
                    'upload_timestamp': doc.upload_timestamp.isoformat(),
                    'metadata': doc.metadata
                }
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return None

