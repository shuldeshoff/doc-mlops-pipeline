"""
Монитор производительности системы
"""
import time
from functools import wraps
from typing import Callable, Any
from datetime import datetime
from loguru import logger

from services.ingestion.database import get_db_connection
from .database import PerformanceMetric


class PerformanceMonitor:
    """Класс для мониторинга производительности"""
    
    @staticmethod
    def measure_time(func: Callable) -> Callable:
        """
        Декоратор для измерения времени выполнения функции
        
        Args:
            func: Функция для мониторинга
            
        Returns:
            Обёрнутая функция
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                logger.info(
                    f"Function '{func.__name__}' executed in {elapsed_time:.4f}s"
                )
                
                return result
                
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(
                    f"Function '{func.__name__}' failed after {elapsed_time:.4f}s: {e}"
                )
                raise
        
        return wrapper
    
    @staticmethod
    def measure_and_log(
        service_name: str,
        endpoint: str = None
    ) -> Callable:
        """
        Декоратор для измерения и логирования метрик производительности в БД
        
        Args:
            service_name: Имя сервиса
            endpoint: Имя эндпоинта/функции
            
        Returns:
            Декоратор
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                endpoint_name = endpoint or func.__name__
                status_code = 200
                
                try:
                    result = func(*args, **kwargs)
                    elapsed_time = time.time() - start_time
                    
                    # Определение статус кода из результата
                    if isinstance(result, dict):
                        if not result.get('success', True):
                            status_code = 400
                    
                    # Сохранение метрики
                    PerformanceMonitor._save_metric(
                        service_name=service_name,
                        endpoint=endpoint_name,
                        response_time=elapsed_time,
                        status_code=status_code
                    )
                    
                    return result
                    
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    status_code = 500
                    
                    # Сохранение метрики с ошибкой
                    PerformanceMonitor._save_metric(
                        service_name=service_name,
                        endpoint=endpoint_name,
                        response_time=elapsed_time,
                        status_code=status_code,
                        metadata={'error': str(e)}
                    )
                    
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def _save_metric(
        service_name: str,
        endpoint: str,
        response_time: float,
        status_code: int,
        metadata: dict = None
    ) -> None:
        """
        Сохранение метрики производительности в БД
        
        Args:
            service_name: Имя сервиса
            endpoint: Эндпоинт
            response_time: Время ответа
            status_code: HTTP статус код
            metadata: Дополнительные метаданные
        """
        try:
            with get_db_connection() as session:
                metric = PerformanceMetric(
                    service_name=service_name,
                    endpoint=endpoint,
                    response_time=response_time,
                    status_code=status_code,
                    metadata=metadata or {}
                )
                
                session.add(metric)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error saving performance metric: {e}")
    
    @staticmethod
    def get_service_stats(
        service_name: str,
        hours: int = 24
    ) -> dict:
        """
        Получение статистики производительности сервиса
        
        Args:
            service_name: Имя сервиса
            hours: Количество часов для анализа
            
        Returns:
            Словарь со статистикой
        """
        try:
            import sqlalchemy as sa
            from datetime import timedelta
            
            with get_db_connection() as session:
                start_time = datetime.utcnow() - timedelta(hours=hours)
                
                # Общая статистика
                metrics = session.query(
                    sa.func.count(PerformanceMetric.id).label('total_requests'),
                    sa.func.avg(PerformanceMetric.response_time).label('avg_response_time'),
                    sa.func.min(PerformanceMetric.response_time).label('min_response_time'),
                    sa.func.max(PerformanceMetric.response_time).label('max_response_time')
                ).filter(
                    PerformanceMetric.service_name == service_name,
                    PerformanceMetric.timestamp >= start_time
                ).first()
                
                # Статистика по статус кодам
                status_codes = session.query(
                    PerformanceMetric.status_code,
                    sa.func.count(PerformanceMetric.id).label('count')
                ).filter(
                    PerformanceMetric.service_name == service_name,
                    PerformanceMetric.timestamp >= start_time
                ).group_by(
                    PerformanceMetric.status_code
                ).all()
                
                # Статистика по эндпоинтам
                endpoints = session.query(
                    PerformanceMetric.endpoint,
                    sa.func.count(PerformanceMetric.id).label('count'),
                    sa.func.avg(PerformanceMetric.response_time).label('avg_time')
                ).filter(
                    PerformanceMetric.service_name == service_name,
                    PerformanceMetric.timestamp >= start_time
                ).group_by(
                    PerformanceMetric.endpoint
                ).all()
                
                return {
                    'service_name': service_name,
                    'period_hours': hours,
                    'total_requests': metrics.total_requests or 0,
                    'avg_response_time': float(metrics.avg_response_time or 0),
                    'min_response_time': float(metrics.min_response_time or 0),
                    'max_response_time': float(metrics.max_response_time or 0),
                    'status_codes': {
                        str(code): count for code, count in status_codes
                    },
                    'endpoints': [
                        {
                            'endpoint': ep,
                            'count': count,
                            'avg_time': float(avg_time)
                        }
                        for ep, count, avg_time in endpoints
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting service stats: {e}")
            return {}

