"""
Сервис inference для предсказаний
"""
import os
from typing import Dict, List, Optional
import torch
import numpy as np
from loguru import logger
from datetime import datetime

from services.ingestion.database import get_db_connection
from services.ocr.ocr_service import OCRService
from .model_loader import ModelLoader
from .database import Prediction


class InferenceService:
    """Сервис для предсказания классов документов"""
    
    def __init__(
        self,
        model_name: str = None,
        model_version: str = 'latest',
        confidence_threshold: float = 0.7
    ):
        """
        Инициализация inference сервиса
        
        Args:
            model_name: Имя модели
            model_version: Версия модели
            confidence_threshold: Порог уверенности для предсказаний
        """
        self.model_name = model_name or os.getenv('MODEL_NAME', 'document_classifier')
        self.model_version = model_version
        self.confidence_threshold = float(
            os.getenv('CONFIDENCE_THRESHOLD', confidence_threshold)
        )
        
        # Загрузка модели и артефактов
        self.model_loader = ModelLoader()
        artifacts = self.model_loader.load_all_artifacts(
            self.model_name,
            self.model_version
        )
        
        if artifacts is None:
            logger.warning("Failed to load model artifacts")
            self.model = None
            self.vectorizer = None
            self.label_mapping = None
        else:
            self.model = artifacts['model']
            self.vectorizer = artifacts['vectorizer']
            self.label_mapping = artifacts['label_mapping']
            logger.info(
                f"InferenceService initialized: {self.model_name}_{self.model_version}"
            )
        
        self.ocr_service = OCRService()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def predict_from_text(
        self,
        text: str,
        return_all_scores: bool = False
    ) -> Dict:
        """
        Предсказание класса по тексту
        
        Args:
            text: Текст документа
            return_all_scores: Возвращать scores для всех классов
            
        Returns:
            Словарь с предсказанием
        """
        if self.model is None or self.vectorizer is None:
            return {
                'success': False,
                'error': 'Model not loaded'
            }
        
        try:
            # Векторизация текста
            features = self.vectorizer.transform([text]).toarray()
            features_tensor = torch.FloatTensor(features).to(self.device)
            
            # Предсказание
            with torch.no_grad():
                probabilities = self.model.predict(
                    features_tensor,
                    return_probabilities=True
                )
            
            probs = probabilities.cpu().numpy()[0]
            predicted_idx = int(np.argmax(probs))
            confidence = float(probs[predicted_idx])
            
            predicted_class = self.label_mapping['idx_to_label'][predicted_idx]
            
            result = {
                'success': True,
                'predicted_class': predicted_class,
                'confidence_score': confidence,
                'is_confident': confidence >= self.confidence_threshold,
                'model_name': self.model_name,
                'model_version': self.model_version
            }
            
            if return_all_scores:
                all_scores = {
                    self.label_mapping['idx_to_label'][idx]: float(score)
                    for idx, score in enumerate(probs)
                }
                result['all_scores'] = all_scores
            
            return result
            
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_from_document(
        self,
        document_id: int,
        ocr_language: str = 'eng',
        return_all_scores: bool = False,
        save_to_db: bool = True
    ) -> Dict:
        """
        Предсказание класса документа по ID
        
        Args:
            document_id: ID документа
            ocr_language: Язык для OCR
            return_all_scores: Возвращать scores для всех классов
            save_to_db: Сохранять результат в БД
            
        Returns:
            Словарь с предсказанием
        """
        # Получение OCR результатов
        ocr_results = self.ocr_service.get_ocr_results(document_id)
        
        if ocr_results is None:
            # Если OCR не был выполнен, выполняем
            logger.info(f"Running OCR for document {document_id}")
            ocr_results = self.ocr_service.process_document(
                document_id,
                ocr_language
            )
            
            if not ocr_results.get('success'):
                return {
                    'success': False,
                    'error': 'OCR processing failed'
                }
        
        extracted_text = ocr_results.get('extracted_text', '')
        
        if not extracted_text:
            return {
                'success': False,
                'error': 'No text extracted from document'
            }
        
        # Предсказание
        prediction = self.predict_from_text(extracted_text, return_all_scores)
        
        if prediction.get('success') and save_to_db:
            # Сохранение в БД
            self._save_prediction({
                'document_id': document_id,
                'predicted_class': prediction['predicted_class'],
                'confidence_score': prediction['confidence_score'],
                'all_scores': prediction.get('all_scores'),
                'model_name': self.model_name,
                'model_version': self.model_version
            })
        
        prediction['document_id'] = document_id
        return prediction
    
    def batch_predict(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict]:
        """
        Пакетное предсказание
        
        Args:
            texts: Список текстов
            batch_size: Размер батча
            
        Returns:
            Список предсказаний
        """
        if self.model is None or self.vectorizer is None:
            return [{
                'success': False,
                'error': 'Model not loaded'
            }] * len(texts)
        
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                # Векторизация батча
                features = self.vectorizer.transform(batch).toarray()
                features_tensor = torch.FloatTensor(features).to(self.device)
                
                # Предсказание
                with torch.no_grad():
                    probabilities = self.model.predict(
                        features_tensor,
                        return_probabilities=True
                    )
                
                probs = probabilities.cpu().numpy()
                
                # Формирование результатов
                for j, prob in enumerate(probs):
                    predicted_idx = int(np.argmax(prob))
                    confidence = float(prob[predicted_idx])
                    predicted_class = self.label_mapping['idx_to_label'][predicted_idx]
                    
                    results.append({
                        'success': True,
                        'predicted_class': predicted_class,
                        'confidence_score': confidence,
                        'is_confident': confidence >= self.confidence_threshold
                    })
                    
            except Exception as e:
                logger.error(f"Error in batch prediction: {e}")
                results.extend([{
                    'success': False,
                    'error': str(e)
                }] * len(batch))
        
        return results
    
    def _save_prediction(self, prediction_data: Dict) -> None:
        """
        Сохранение предсказания в БД
        
        Args:
            prediction_data: Данные предсказания
        """
        try:
            with get_db_connection() as session:
                prediction = Prediction(
                    document_id=prediction_data['document_id'],
                    model_name=prediction_data['model_name'],
                    model_version=prediction_data['model_version'],
                    predicted_class=prediction_data['predicted_class'],
                    confidence_score=prediction_data['confidence_score'],
                    all_scores=prediction_data.get('all_scores')
                )
                
                session.add(prediction)
                session.commit()
                
                logger.info(
                    f"Prediction saved for document {prediction_data['document_id']}"
                )
                
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
    
    def get_prediction_history(
        self,
        document_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Получение истории предсказаний для документа
        
        Args:
            document_id: ID документа
            limit: Максимальное количество записей
            
        Returns:
            Список предсказаний
        """
        try:
            with get_db_connection() as session:
                predictions = session.query(Prediction).filter(
                    Prediction.document_id == document_id
                ).order_by(
                    Prediction.predicted_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'id': p.id,
                        'predicted_class': p.predicted_class,
                        'confidence_score': p.confidence_score,
                        'model_name': p.model_name,
                        'model_version': p.model_version,
                        'predicted_at': p.predicted_at.isoformat(),
                        'all_scores': p.all_scores
                    }
                    for p in predictions
                ]
                
        except Exception as e:
            logger.error(f"Error getting prediction history: {e}")
            return []

