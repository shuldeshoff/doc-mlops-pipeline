-- Создание баз данных для различных сервисов

-- База данных для MLflow
CREATE DATABASE mlflow;

-- База данных для Airflow
CREATE DATABASE airflow;

-- База данных для основного приложения
-- (основная БД уже создана через переменные окружения)

-- Создание схем для основной БД
\c mlops_docflow;

CREATE SCHEMA IF NOT EXISTS documents;
CREATE SCHEMA IF NOT EXISTS models;
CREATE SCHEMA IF NOT EXISTS metrics;

-- Таблица документов
CREATE TABLE IF NOT EXISTS documents.documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(512),
    storage_path VARCHAR(512) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'uploaded',
    metadata JSONB
);

-- Таблица результатов OCR
CREATE TABLE IF NOT EXISTS documents.ocr_results (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents.documents(id) ON DELETE CASCADE,
    extracted_text TEXT,
    language VARCHAR(10),
    confidence_score FLOAT,
    processing_time FLOAT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ocr_engine VARCHAR(50)
);

-- Таблица предсказаний модели
CREATE TABLE IF NOT EXISTS documents.predictions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents.documents(id) ON DELETE CASCADE,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    predicted_class VARCHAR(100),
    confidence_score FLOAT,
    all_scores JSONB,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица метрик моделей
CREATE TABLE IF NOT EXISTS models.model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    dataset_size INTEGER,
    training_time FLOAT,
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Таблица для мониторинга производительности
CREATE TABLE IF NOT EXISTS metrics.performance_metrics (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    endpoint VARCHAR(255),
    response_time FLOAT,
    status_code INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Индексы для оптимизации запросов
CREATE INDEX idx_documents_status ON documents.documents(status);
CREATE INDEX idx_documents_upload_timestamp ON documents.documents(upload_timestamp);
CREATE INDEX idx_ocr_results_document_id ON documents.ocr_results(document_id);
CREATE INDEX idx_predictions_document_id ON documents.predictions(document_id);
CREATE INDEX idx_predictions_predicted_at ON documents.predictions(predicted_at);
CREATE INDEX idx_performance_metrics_timestamp ON metrics.performance_metrics(timestamp);
CREATE INDEX idx_performance_metrics_service ON metrics.performance_metrics(service_name);

-- Комментарии к таблицам
COMMENT ON TABLE documents.documents IS 'Основная таблица для хранения метаданных загруженных документов';
COMMENT ON TABLE documents.ocr_results IS 'Результаты OCR обработки документов';
COMMENT ON TABLE documents.predictions IS 'Результаты классификации документов моделью';
COMMENT ON TABLE models.model_metrics IS 'Метрики качества обученных моделей';
COMMENT ON TABLE metrics.performance_metrics IS 'Метрики производительности сервисов';

