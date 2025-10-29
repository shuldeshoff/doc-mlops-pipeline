"""
Airflow DAG для оркестрации ML пайплайна обработки документов
"""
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к модулям проекта
sys.path.insert(0, '/opt/airflow')

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from loguru import logger

from services.ingestion.ingestion_service import IngestionService
from services.ocr.ocr_service import OCRService
from services.training.training_service import TrainingService
from services.inference.inference_service import InferenceService
from services.monitoring.metrics_service import MetricsService


# Параметры DAG по умолчанию
default_args = {
    'owner': 'mlops',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Создание DAG
dag = DAG(
    'document_processing_pipeline',
    default_args=default_args,
    description='Полный пайплайн обработки и классификации документов',
    schedule_interval=timedelta(days=1),  # Ежедневный запуск
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'documents', 'ml-pipeline'],
)


def check_new_documents(**context):
    """Проверка наличия новых документов для обработки"""
    from services.ingestion.database import get_db_connection, Document
    import sqlalchemy as sa
    
    logger.info("Checking for new documents...")
    
    with get_db_connection() as session:
        # Документы, которые загружены но не обработаны OCR
        new_docs = session.query(Document).filter(
            Document.status == 'uploaded'
        ).count()
        
        logger.info(f"Found {new_docs} new documents to process")
        
        # Сохраняем результат в XCom
        context['ti'].xcom_push(key='new_documents_count', value=new_docs)
        
        return new_docs > 0


def process_ocr_batch(**context):
    """Обработка OCR для новых документов"""
    from services.ingestion.database import get_db_connection, Document
    
    logger.info("Starting OCR batch processing...")
    
    ocr_service = OCRService()
    
    with get_db_connection() as session:
        # Получаем документы для обработки
        documents = session.query(Document).filter(
            Document.status == 'uploaded'
        ).limit(100).all()  # Обрабатываем до 100 документов за раз
        
        document_ids = [doc.id for doc in documents]
        
        logger.info(f"Processing {len(document_ids)} documents...")
    
    # Пакетная обработка OCR
    results = ocr_service.batch_process_documents(document_ids)
    
    successful = sum(1 for r in results if r.get('success', False))
    
    logger.info(f"OCR processing completed: {successful}/{len(results)} successful")
    
    context['ti'].xcom_push(key='ocr_processed', value=successful)
    
    return successful


def check_training_needed(**context):
    """Проверка необходимости переобучения модели"""
    from services.training.database import ModelMetrics
    from services.ingestion.database import get_db_connection
    import sqlalchemy as sa
    
    logger.info("Checking if model retraining is needed...")
    
    with get_db_connection() as session:
        # Получаем последнюю модель
        last_model = session.query(ModelMetrics).order_by(
            ModelMetrics.trained_at.desc()
        ).first()
        
        if last_model is None:
            logger.info("No trained model found, training needed")
            return True
        
        # Проверяем дату последнего обучения
        days_since_training = (datetime.utcnow() - last_model.trained_at).days
        
        # Переобучаем если прошло больше 7 дней или точность низкая
        needs_retraining = (
            days_since_training > 7 or
            last_model.accuracy < 0.85
        )
        
        logger.info(
            f"Days since last training: {days_since_training}, "
            f"Accuracy: {last_model.accuracy:.4f}, "
            f"Retraining needed: {needs_retraining}"
        )
        
        context['ti'].xcom_push(key='needs_retraining', value=needs_retraining)
        
        return needs_retraining


def train_model(**context):
    """Обучение модели классификации"""
    logger.info("Starting model training...")
    
    training_service = TrainingService()
    
    # Загрузка данных для обучения
    texts, labels = training_service.load_training_data(min_confidence=0.6)
    
    if len(texts) < 100:
        logger.warning(f"Not enough training data: {len(texts)} samples")
        return False
    
    logger.info(f"Training with {len(texts)} samples...")
    
    # Обучение модели
    result = training_service.train_model(
        texts=texts,
        labels=labels,
        epochs=50,
        batch_size=32,
        learning_rate=0.001
    )
    
    if result.get('success'):
        logger.info(
            f"Training completed successfully. "
            f"Accuracy: {result['accuracy']:.4f}, "
            f"F1: {result['f1']:.4f}"
        )
        
        context['ti'].xcom_push(key='model_accuracy', value=result['accuracy'])
        return True
    else:
        logger.error("Training failed")
        return False


def deploy_model(**context):
    """Деплой модели (обновление inference service)"""
    logger.info("Deploying model...")
    
    # В реальной системе здесь был бы код для деплоя через Seldon/KServe
    # Для демонстрации просто логируем
    
    model_accuracy = context['ti'].xcom_pull(
        task_ids='train_model',
        key='model_accuracy'
    )
    
    logger.info(f"Model deployed with accuracy: {model_accuracy:.4f}")
    
    # Перезагрузка inference service (в production через API или Kubernetes)
    inference_service = InferenceService()
    
    # Переинициализация с новой моделью
    artifacts = inference_service.model_loader.load_all_artifacts(
        'document_classifier',
        'latest'
    )
    
    if artifacts:
        inference_service.model = artifacts['model']
        inference_service.vectorizer = artifacts['vectorizer']
        inference_service.label_mapping = artifacts['label_mapping']
        logger.info("Inference service updated with new model")
        return True
    else:
        logger.error("Failed to load new model")
        return False


def run_predictions(**context):
    """Запуск предсказаний для документов с OCR"""
    from services.ingestion.database import get_db_connection, Document
    import sqlalchemy as sa
    
    logger.info("Running predictions...")
    
    inference_service = InferenceService()
    
    with get_db_connection() as session:
        # Получаем документы с завершенным OCR, но без предсказаний
        documents = session.query(Document).filter(
            Document.status == 'ocr_completed'
        ).limit(100).all()
        
        document_ids = [doc.id for doc in documents]
        
        logger.info(f"Running predictions for {len(document_ids)} documents...")
    
    # Обработка предсказаний
    successful = 0
    for doc_id in document_ids:
        result = inference_service.predict_from_document(doc_id)
        if result.get('success'):
            successful += 1
    
    logger.info(f"Predictions completed: {successful}/{len(document_ids)} successful")
    
    context['ti'].xcom_push(key='predictions_made', value=successful)
    
    return successful


def collect_metrics(**context):
    """Сбор и анализ метрик системы"""
    logger.info("Collecting system metrics...")
    
    metrics_service = MetricsService()
    
    # Получение общей статистики
    stats = metrics_service.get_system_stats(days=7)
    
    logger.info(f"System stats: {stats}")
    
    # Детектирование аномалий
    anomalies = metrics_service.detect_anomalies(threshold=0.5)
    
    if anomalies:
        logger.warning(f"Detected {len(anomalies)} anomalies:")
        for anomaly in anomalies:
            logger.warning(f"  - {anomaly['description']}")
    else:
        logger.info("No anomalies detected")
    
    context['ti'].xcom_push(key='anomalies_count', value=len(anomalies))
    
    return True


def cleanup_old_data(**context):
    """Очистка старых данных и логов"""
    from services.ingestion.database import get_db_connection
    from services.monitoring.database import PerformanceMetric
    
    logger.info("Cleaning up old data...")
    
    # Удаление старых метрик производительности (старше 30 дней)
    with get_db_connection() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted = session.query(PerformanceMetric).filter(
            PerformanceMetric.timestamp < cutoff_date
        ).delete()
        
        session.commit()
        
        logger.info(f"Deleted {deleted} old performance metrics")
    
    return True


# Определение задач
check_docs_task = PythonOperator(
    task_id='check_new_documents',
    python_callable=check_new_documents,
    dag=dag,
)

ocr_task = PythonOperator(
    task_id='process_ocr_batch',
    python_callable=process_ocr_batch,
    dag=dag,
)

check_training_task = PythonOperator(
    task_id='check_training_needed',
    python_callable=check_training_needed,
    dag=dag,
)

train_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

deploy_task = PythonOperator(
    task_id='deploy_model',
    python_callable=deploy_model,
    dag=dag,
)

predict_task = PythonOperator(
    task_id='run_predictions',
    python_callable=run_predictions,
    dag=dag,
)

metrics_task = PythonOperator(
    task_id='collect_metrics',
    python_callable=collect_metrics,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag,
)

# Определение зависимостей задач
check_docs_task >> ocr_task >> check_training_task

# Ветка обучения модели (если необходимо)
check_training_task >> train_task >> deploy_task >> predict_task

# Ветка предсказаний (если обучение не нужно)
check_training_task >> predict_task

# Сбор метрик и очистка
predict_task >> metrics_task >> cleanup_task

