"""
Сервис для сбора и анализа метрик
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from prometheus_client import Counter, Histogram, Gauge, Summary
import sqlalchemy as sa

from services.ingestion.database import get_db_connection, Document
from services.ocr.database import OCRResult
from services.inference.database import Prediction
from services.training.database import ModelMetrics


# Prometheus метрики
documents_uploaded = Counter(
    'documents_uploaded_total',
    'Общее количество загруженных документов'
)

documents_processed = Counter(
    'documents_processed_total',
    'Общее количество обработанных документов',
    ['status']
)

ocr_processing_time = Histogram(
    'ocr_processing_seconds',
    'Время обработки OCR в секундах',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

ocr_confidence = Histogram(
    'ocr_confidence_score',
    'Confidence score OCR',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

prediction_confidence = Histogram(
    'prediction_confidence_score',
    'Confidence score предсказаний',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

predictions_total = Counter(
    'predictions_total',
    'Общее количество предсказаний',
    ['predicted_class']
)

model_accuracy = Gauge(
    'model_accuracy',
    'Текущая точность модели'
)

api_request_duration = Summary(
    'api_request_duration_seconds',
    'Длительность API запросов',
    ['endpoint', 'method']
)


class MetricsService:
    """Сервис для сбора и анализа метрик системы"""
    
    def __init__(self):
        """Инициализация сервиса метрик"""
        logger.info("MetricsService initialized")
    
    def get_system_stats(self, days: int = 7) -> Dict:
        """
        Получение общей статистики системы
        
        Args:
            days: Количество дней для анализа
            
        Returns:
            Словарь со статистикой
        """
        try:
            with get_db_connection() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Статистика документов
                total_documents = session.query(
                    sa.func.count(Document.id)
                ).scalar()
                
                recent_documents = session.query(
                    sa.func.count(Document.id)
                ).filter(
                    Document.upload_timestamp >= start_date
                ).scalar()
                
                # Статистика OCR
                total_ocr = session.query(
                    sa.func.count(OCRResult.id)
                ).scalar()
                
                avg_ocr_confidence = session.query(
                    sa.func.avg(OCRResult.confidence_score)
                ).scalar()
                
                avg_ocr_time = session.query(
                    sa.func.avg(OCRResult.processing_time)
                ).scalar()
                
                # Статистика предсказаний
                total_predictions = session.query(
                    sa.func.count(Prediction.id)
                ).scalar()
                
                avg_prediction_confidence = session.query(
                    sa.func.avg(Prediction.confidence_score)
                ).scalar()
                
                # Распределение классов
                class_distribution = session.query(
                    Prediction.predicted_class,
                    sa.func.count(Prediction.id).label('count')
                ).group_by(
                    Prediction.predicted_class
                ).all()
                
                return {
                    'period_days': days,
                    'documents': {
                        'total': total_documents or 0,
                        'recent': recent_documents or 0
                    },
                    'ocr': {
                        'total_processed': total_ocr or 0,
                        'avg_confidence': float(avg_ocr_confidence or 0),
                        'avg_processing_time': float(avg_ocr_time or 0)
                    },
                    'predictions': {
                        'total': total_predictions or 0,
                        'avg_confidence': float(avg_prediction_confidence or 0),
                        'class_distribution': {
                            cls: count for cls, count in class_distribution
                        }
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def get_model_performance(
        self,
        model_name: str = 'document_classifier',
        limit: int = 10
    ) -> List[Dict]:
        """
        Получение истории производительности модели
        
        Args:
            model_name: Имя модели
            limit: Количество записей
            
        Returns:
            Список метрик модели
        """
        try:
            with get_db_connection() as session:
                metrics = session.query(ModelMetrics).filter(
                    ModelMetrics.model_name == model_name
                ).order_by(
                    ModelMetrics.trained_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'model_version': m.model_version,
                        'accuracy': m.accuracy,
                        'precision': m.precision_score,
                        'recall': m.recall_score,
                        'f1': m.f1_score,
                        'dataset_size': m.dataset_size,
                        'training_time': m.training_time,
                        'trained_at': m.trained_at.isoformat()
                    }
                    for m in metrics
                ]
                
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return []
    
    def get_confidence_distribution(
        self,
        metric_type: str = 'prediction',
        bins: int = 10
    ) -> Dict:
        """
        Получение распределения confidence scores
        
        Args:
            metric_type: Тип метрики ('prediction' или 'ocr')
            bins: Количество бинов для гистограммы
            
        Returns:
            Словарь с распределением
        """
        try:
            with get_db_connection() as session:
                if metric_type == 'prediction':
                    scores = session.query(
                        Prediction.confidence_score
                    ).all()
                elif metric_type == 'ocr':
                    scores = session.query(
                        OCRResult.confidence_score
                    ).all()
                else:
                    return {}
                
                scores = [s[0] for s in scores if s[0] is not None]
                
                if not scores:
                    return {'bins': [], 'counts': []}
                
                # Создание гистограммы
                import numpy as np
                counts, bin_edges = np.histogram(scores, bins=bins, range=(0, 1))
                
                return {
                    'bins': bin_edges.tolist(),
                    'counts': counts.tolist(),
                    'mean': float(np.mean(scores)),
                    'median': float(np.median(scores)),
                    'std': float(np.std(scores))
                }
                
        except Exception as e:
            logger.error(f"Error getting confidence distribution: {e}")
            return {}
    
    def get_processing_throughput(self, days: int = 7) -> Dict:
        """
        Получение метрик пропускной способности
        
        Args:
            days: Количество дней для анализа
            
        Returns:
            Словарь с метриками пропускной способности
        """
        try:
            with get_db_connection() as session:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Документы по дням
                documents_by_day = session.query(
                    sa.func.date(Document.upload_timestamp).label('date'),
                    sa.func.count(Document.id).label('count')
                ).filter(
                    Document.upload_timestamp >= start_date
                ).group_by(
                    sa.func.date(Document.upload_timestamp)
                ).all()
                
                # OCR обработка по дням
                ocr_by_day = session.query(
                    sa.func.date(OCRResult.processed_at).label('date'),
                    sa.func.count(OCRResult.id).label('count'),
                    sa.func.avg(OCRResult.processing_time).label('avg_time')
                ).filter(
                    OCRResult.processed_at >= start_date
                ).group_by(
                    sa.func.date(OCRResult.processed_at)
                ).all()
                
                # Предсказания по дням
                predictions_by_day = session.query(
                    sa.func.date(Prediction.predicted_at).label('date'),
                    sa.func.count(Prediction.id).label('count')
                ).filter(
                    Prediction.predicted_at >= start_date
                ).group_by(
                    sa.func.date(Prediction.predicted_at)
                ).all()
                
                return {
                    'documents_by_day': [
                        {'date': d.isoformat(), 'count': count}
                        for d, count in documents_by_day
                    ],
                    'ocr_by_day': [
                        {
                            'date': d.isoformat(),
                            'count': count,
                            'avg_time': float(avg_time)
                        }
                        for d, count, avg_time in ocr_by_day
                    ],
                    'predictions_by_day': [
                        {'date': d.isoformat(), 'count': count}
                        for d, count in predictions_by_day
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting processing throughput: {e}")
            return {}
    
    def detect_anomalies(self, threshold: float = 0.5) -> List[Dict]:
        """
        Детектирование аномалий в данных
        
        Args:
            threshold: Порог для определения низкой уверенности
            
        Returns:
            Список потенциальных аномалий
        """
        anomalies = []
        
        try:
            with get_db_connection() as session:
                # Низкие confidence scores в OCR
                low_ocr_confidence = session.query(
                    OCRResult
                ).filter(
                    OCRResult.confidence_score < threshold
                ).count()
                
                if low_ocr_confidence > 0:
                    anomalies.append({
                        'type': 'low_ocr_confidence',
                        'count': low_ocr_confidence,
                        'threshold': threshold,
                        'description': f'{low_ocr_confidence} документов с низким OCR confidence'
                    })
                
                # Низкие confidence scores в предсказаниях
                low_prediction_confidence = session.query(
                    Prediction
                ).filter(
                    Prediction.confidence_score < threshold
                ).count()
                
                if low_prediction_confidence > 0:
                    anomalies.append({
                        'type': 'low_prediction_confidence',
                        'count': low_prediction_confidence,
                        'threshold': threshold,
                        'description': f'{low_prediction_confidence} предсказаний с низкой уверенностью'
                    })
                
                # Долгая обработка OCR
                long_ocr_processing = session.query(
                    OCRResult
                ).filter(
                    OCRResult.processing_time > 30.0
                ).count()
                
                if long_ocr_processing > 0:
                    anomalies.append({
                        'type': 'long_ocr_processing',
                        'count': long_ocr_processing,
                        'threshold': 30.0,
                        'description': f'{long_ocr_processing} документов с долгой OCR обработкой (>30s)'
                    })
                
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
        
        return anomalies

