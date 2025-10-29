"""
FastAPI приложение для inference API
"""
import os
import sys
from typing import Optional
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from loguru import logger
import uvicorn

from services.inference.inference_service import InferenceService
from services.ingestion.ingestion_service import IngestionService


# Настройка логирования
logger.add(
    "logs/inference_api.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# Инициализация FastAPI
app = FastAPI(
    title="MLOps Document Classification API",
    description="API для классификации документов с использованием ML моделей",
    version="1.0.0"
)

# Prometheus метрики
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Сервисы
inference_service = InferenceService()
ingestion_service = IngestionService()


# Pydantic модели
class PredictionResponse(BaseModel):
    """Модель ответа предсказания"""
    success: bool
    document_id: Optional[int] = None
    predicted_class: Optional[str] = None
    confidence_score: Optional[float] = None
    is_confident: Optional[bool] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    all_scores: Optional[dict] = None
    error: Optional[str] = None


class TextPredictionRequest(BaseModel):
    """Модель запроса предсказания по тексту"""
    text: str = Field(..., description="Текст документа для классификации")
    return_all_scores: bool = Field(
        False,
        description="Вернуть scores для всех классов"
    )


class HealthResponse(BaseModel):
    """Модель ответа health check"""
    status: str
    timestamp: str
    model_loaded: bool
    model_name: Optional[str] = None
    model_version: Optional[str] = None


@app.get("/", response_model=dict)
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "MLOps Document Classification API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check эндпоинт"""
    model_loaded = inference_service.model is not None
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        model_loaded=model_loaded,
        model_name=inference_service.model_name if model_loaded else None,
        model_version=inference_service.model_version if model_loaded else None
    )


@app.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(..., description="Файл документа для загрузки")
):
    """
    Загрузка документа в систему
    
    - **file**: Файл документа (изображение или PDF)
    
    Returns:
        Информация о загруженном документе
    """
    try:
        logger.info(f"Uploading document: {file.filename}")
        
        # Загрузка документа
        result = ingestion_service.ingest_document(
            filename=file.filename,
            file_data=file.file,
            metadata={'uploaded_via': 'api'}
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Upload failed')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/predict/text", response_model=PredictionResponse)
async def predict_from_text(request: TextPredictionRequest):
    """
    Предсказание класса документа по тексту
    
    - **text**: Текст документа
    - **return_all_scores**: Вернуть scores для всех классов (по умолчанию False)
    
    Returns:
        Предсказание класса и confidence score
    """
    try:
        logger.info(f"Predicting from text (length: {len(request.text)})")
        
        result = inference_service.predict_from_text(
            text=request.text,
            return_all_scores=request.return_all_scores
        )
        
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Error predicting from text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/predict/document/{document_id}", response_model=PredictionResponse)
async def predict_from_document(
    document_id: int,
    ocr_language: str = 'eng',
    return_all_scores: bool = False
):
    """
    Предсказание класса документа по ID
    
    - **document_id**: ID документа в системе
    - **ocr_language**: Язык для OCR (eng, rus, eng+rus)
    - **return_all_scores**: Вернуть scores для всех классов
    
    Returns:
        Предсказание класса и confidence score
    """
    try:
        logger.info(f"Predicting for document ID: {document_id}")
        
        result = inference_service.predict_from_document(
            document_id=document_id,
            ocr_language=ocr_language,
            return_all_scores=return_all_scores,
            save_to_db=True
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', 'Prediction failed')
            )
        
        return PredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting from document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/upload-and-predict", response_model=dict)
async def upload_and_predict(
    file: UploadFile = File(..., description="Файл документа"),
    ocr_language: str = 'eng',
    return_all_scores: bool = False
):
    """
    Загрузка документа и немедленное предсказание класса
    
    - **file**: Файл документа
    - **ocr_language**: Язык для OCR
    - **return_all_scores**: Вернуть scores для всех классов
    
    Returns:
        Информация о загрузке и предсказание
    """
    try:
        logger.info(f"Upload and predict: {file.filename}")
        
        # Загрузка документа
        upload_result = ingestion_service.ingest_document(
            filename=file.filename,
            file_data=file.file,
            metadata={'uploaded_via': 'api'}
        )
        
        if not upload_result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=upload_result.get('error', 'Upload failed')
            )
        
        document_id = upload_result['document_id']
        
        # Предсказание
        prediction_result = inference_service.predict_from_document(
            document_id=document_id,
            ocr_language=ocr_language,
            return_all_scores=return_all_scores,
            save_to_db=True
        )
        
        return {
            'upload': upload_result,
            'prediction': prediction_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload-and-predict: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/prediction/history/{document_id}", response_model=list)
async def get_prediction_history(document_id: int, limit: int = 10):
    """
    Получение истории предсказаний для документа
    
    - **document_id**: ID документа
    - **limit**: Максимальное количество записей
    
    Returns:
        История предсказаний
    """
    try:
        history = inference_service.get_prediction_history(document_id, limit)
        return history
        
    except Exception as e:
        logger.error(f"Error getting prediction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/document/{document_id}", response_model=dict)
async def get_document_info(document_id: int):
    """
    Получение информации о документе
    
    - **document_id**: ID документа
    
    Returns:
        Информация о документе
    """
    try:
        info = ingestion_service.get_document_info(document_id)
        
        if info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


if __name__ == "__main__":
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

