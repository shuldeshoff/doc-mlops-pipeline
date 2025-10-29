"""
Модуль для работы с хранилищем MinIO
"""
import os
from typing import BinaryIO, Optional
from minio import Minio
from minio.error import S3Error
from loguru import logger
import io


class MinIOStorage:
    """Класс для работы с MinIO S3-совместимым хранилищем"""
    
    def __init__(
        self,
        endpoint: str = None,
        access_key: str = None,
        secret_key: str = None,
        secure: bool = False
    ):
        """
        Инициализация клиента MinIO
        
        Args:
            endpoint: Адрес MinIO сервера
            access_key: Ключ доступа
            secret_key: Секретный ключ
            secure: Использовать HTTPS
        """
        self.endpoint = endpoint or os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = secret_key or os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure
        )
        
        logger.info(f"MinIO client initialized for endpoint: {self.endpoint}")
    
    def ensure_bucket(self, bucket_name: str) -> bool:
        """
        Проверка существования бакета и создание при необходимости
        
        Args:
            bucket_name: Имя бакета
            
        Returns:
            True если бакет существует или создан
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Bucket '{bucket_name}' created")
            return True
        except S3Error as e:
            logger.error(f"Error ensuring bucket '{bucket_name}': {e}")
            return False
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: BinaryIO,
        content_type: str = 'application/octet-stream',
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Загрузка файла в MinIO
        
        Args:
            bucket_name: Имя бакета
            object_name: Имя объекта (путь в бакете)
            file_data: Данные файла
            content_type: MIME тип файла
            metadata: Дополнительные метаданные
            
        Returns:
            True если загрузка успешна
        """
        try:
            self.ensure_bucket(bucket_name)
            
            # Получаем размер файла
            file_data.seek(0, os.SEEK_END)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self.client.put_object(
                bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type,
                metadata=metadata or {}
            )
            
            logger.info(f"File uploaded: {bucket_name}/{object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            return False
    
    def download_file(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[bytes]:
        """
        Скачивание файла из MinIO
        
        Args:
            bucket_name: Имя бакета
            object_name: Имя объекта
            
        Returns:
            Данные файла или None
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"File downloaded: {bucket_name}/{object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            return None
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Проверка существования файла
        
        Args:
            bucket_name: Имя бакета
            object_name: Имя объекта
            
        Returns:
            True если файл существует
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: str = ''
    ) -> list:
        """
        Список объектов в бакете
        
        Args:
            bucket_name: Имя бакета
            prefix: Префикс для фильтрации
            
        Returns:
            Список имен объектов
        """
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """
        Удаление файла из MinIO
        
        Args:
            bucket_name: Имя бакета
            object_name: Имя объекта
            
        Returns:
            True если удаление успешно
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"File deleted: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False

