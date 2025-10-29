"""
Модели базы данных для модуля ingestion
"""
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    BigInteger,
    DateTime,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from loguru import logger


Base = declarative_base()


class Document(Base):
    """Модель документа"""
    __tablename__ = 'documents'
    __table_args__ = {'schema': 'documents'}
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(512))
    storage_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='uploaded')
    metadata = Column(JSON)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"


def get_database_url() -> str:
    """Получение URL базы данных из переменных окружения"""
    user = os.getenv('POSTGRES_USER', 'mlops')
    password = os.getenv('POSTGRES_PASSWORD', 'mlops_password_2024')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'mlops_docflow')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


# Создание движка БД
engine = create_engine(
    get_database_url(),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_connection() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для работы с БД
    
    Yields:
        Session объект SQLAlchemy
    """
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """Инициализация схемы базы данных"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

