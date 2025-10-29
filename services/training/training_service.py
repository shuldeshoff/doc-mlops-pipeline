"""
Сервис обучения моделей классификации документов
"""
import os
import pickle
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from loguru import logger
import mlflow
import mlflow.pytorch

from services.ingestion.database import get_db_connection
from services.ocr.database import OCRResult
from .models import SimpleTextClassifier
from .database import ModelMetrics


class TextDataset(Dataset):
    """Dataset для текстовых данных"""
    
    def __init__(self, features, labels):
        self.features = torch.FloatTensor(features)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class TrainingService:
    """Сервис для обучения моделей классификации"""
    
    def __init__(
        self,
        model_name: str = 'document_classifier',
        mlflow_tracking_uri: Optional[str] = None
    ):
        """
        Инициализация сервиса обучения
        
        Args:
            model_name: Имя модели
            mlflow_tracking_uri: URI для MLflow tracking
        """
        self.model_name = model_name
        self.mlflow_tracking_uri = mlflow_tracking_uri or os.getenv(
            'MLFLOW_TRACKING_URI',
            'http://mlflow:5000'
        )
        
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"TrainingService initialized, device: {self.device}")
    
    def load_training_data(
        self,
        min_confidence: float = 0.5
    ) -> Tuple[List[str], List[str]]:
        """
        Загрузка данных для обучения из БД
        
        Args:
            min_confidence: Минимальный уровень confidence OCR
            
        Returns:
            Кортеж (тексты, метки)
        """
        texts = []
        labels = []
        
        try:
            with get_db_connection() as session:
                # Здесь предполагается, что у нас есть размеченные данные
                # В реальной системе это могут быть данные с метками классов
                results = session.query(OCRResult).filter(
                    OCRResult.confidence_score >= min_confidence
                ).all()
                
                for result in results:
                    if result.extracted_text:
                        texts.append(result.extracted_text)
                        # Здесь должна быть реальная логика получения меток
                        # Для примера используем заглушку
                        labels.append('unknown')
                
                logger.info(f"Loaded {len(texts)} training samples")
                
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
        
        return texts, labels
    
    def prepare_features(
        self,
        texts: List[str],
        vectorizer: Optional[TfidfVectorizer] = None,
        max_features: int = 5000
    ) -> Tuple[np.ndarray, TfidfVectorizer]:
        """
        Подготовка признаков из текстов
        
        Args:
            texts: Список текстов
            vectorizer: Существующий векторизатор
            max_features: Максимальное количество признаков
            
        Returns:
            Кортеж (матрица признаков, векторизатор)
        """
        if vectorizer is None:
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                stop_words='english'
            )
            features = vectorizer.fit_transform(texts)
        else:
            features = vectorizer.transform(texts)
        
        logger.info(f"Features prepared: {features.shape}")
        return features.toarray(), vectorizer
    
    def train_model(
        self,
        texts: List[str],
        labels: List[str],
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        test_size: float = 0.2,
        experiment_name: str = 'document_classification'
    ) -> Dict:
        """
        Обучение модели классификации
        
        Args:
            texts: Список текстов
            labels: Список меток
            epochs: Количество эпох
            batch_size: Размер батча
            learning_rate: Learning rate
            test_size: Доля тестовой выборки
            experiment_name: Имя эксперимента в MLflow
            
        Returns:
            Словарь с результатами обучения
        """
        start_time = datetime.utcnow()
        
        # Настройка MLflow
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run():
            # Логирование параметров
            mlflow.log_params({
                'epochs': epochs,
                'batch_size': batch_size,
                'learning_rate': learning_rate,
                'test_size': test_size
            })
            
            # Подготовка данных
            logger.info("Preparing features...")
            features, vectorizer = self.prepare_features(texts)
            
            # Кодирование меток
            unique_labels = sorted(list(set(labels)))
            label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
            idx_to_label = {idx: label for label, idx in label_to_idx.items()}
            
            encoded_labels = [label_to_idx[label] for label in labels]
            
            # Разделение на train/test
            X_train, X_test, y_train, y_test = train_test_split(
                features,
                encoded_labels,
                test_size=test_size,
                random_state=42,
                stratify=encoded_labels
            )
            
            logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
            
            # Создание DataLoader'ов
            train_dataset = TextDataset(X_train, y_train)
            test_dataset = TextDataset(X_test, y_test)
            
            train_loader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                shuffle=True
            )
            test_loader = DataLoader(
                test_dataset,
                batch_size=batch_size,
                shuffle=False
            )
            
            # Инициализация модели
            num_classes = len(unique_labels)
            input_size = features.shape[1]
            
            model = SimpleTextClassifier(
                input_size=input_size,
                num_classes=num_classes,
                hidden_sizes=[512, 256]
            ).to(self.device)
            
            # Loss и optimizer
            criterion = nn.CrossEntropyLoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
            
            # Обучение
            logger.info("Starting training...")
            best_accuracy = 0.0
            
            for epoch in range(epochs):
                model.train()
                train_loss = 0.0
                
                for batch_features, batch_labels in train_loader:
                    batch_features = batch_features.to(self.device)
                    batch_labels = batch_labels.to(self.device)
                    
                    optimizer.zero_grad()
                    outputs = model(batch_features)
                    loss = criterion(outputs, batch_labels)
                    loss.backward()
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                # Валидация
                model.eval()
                test_loss = 0.0
                predictions = []
                true_labels = []
                
                with torch.no_grad():
                    for batch_features, batch_labels in test_loader:
                        batch_features = batch_features.to(self.device)
                        batch_labels = batch_labels.to(self.device)
                        
                        outputs = model(batch_features)
                        loss = criterion(outputs, batch_labels)
                        test_loss += loss.item()
                        
                        _, predicted = torch.max(outputs, 1)
                        predictions.extend(predicted.cpu().numpy())
                        true_labels.extend(batch_labels.cpu().numpy())
                
                # Метрики
                accuracy = accuracy_score(true_labels, predictions)
                precision, recall, f1, _ = precision_recall_fscore_support(
                    true_labels,
                    predictions,
                    average='weighted'
                )
                
                # Логирование в MLflow
                mlflow.log_metrics({
                    'train_loss': train_loss / len(train_loader),
                    'test_loss': test_loss / len(test_loader),
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }, step=epoch)
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch [{epoch+1}/{epochs}] "
                        f"Train Loss: {train_loss/len(train_loader):.4f}, "
                        f"Test Loss: {test_loss/len(test_loader):.4f}, "
                        f"Accuracy: {accuracy:.4f}"
                    )
            
            # Сохранение модели
            model_dir = Path('data/models')
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = model_dir / f"{self.model_name}_latest.pth"
            vectorizer_path = model_dir / f"{self.model_name}_vectorizer.pkl"
            label_map_path = model_dir / f"{self.model_name}_labels.pkl"
            
            torch.save(model.state_dict(), model_path)
            
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(vectorizer, f)
            
            with open(label_map_path, 'wb') as f:
                pickle.dump({
                    'label_to_idx': label_to_idx,
                    'idx_to_label': idx_to_label
                }, f)
            
            # Логирование артефактов в MLflow
            mlflow.log_artifact(str(model_path))
            mlflow.log_artifact(str(vectorizer_path))
            mlflow.log_artifact(str(label_map_path))
            
            # Логирование модели
            mlflow.pytorch.log_model(model, "model")
            
            training_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Сохранение метрик в БД
            self._save_metrics({
                'model_name': self.model_name,
                'model_version': 'latest',
                'accuracy': best_accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'dataset_size': len(texts),
                'training_time': training_time
            })
            
            logger.info(f"Training completed in {training_time:.2f}s")
            
            return {
                'success': True,
                'model_name': self.model_name,
                'accuracy': best_accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'training_time': training_time,
                'model_path': str(model_path)
            }
    
    def _save_metrics(self, metrics: Dict) -> None:
        """Сохранение метрик модели в БД"""
        try:
            with get_db_connection() as session:
                model_metrics = ModelMetrics(
                    model_name=metrics['model_name'],
                    model_version=metrics['model_version'],
                    accuracy=metrics['accuracy'],
                    precision_score=metrics['precision'],
                    recall_score=metrics['recall'],
                    f1_score=metrics['f1'],
                    dataset_size=metrics['dataset_size'],
                    training_time=metrics['training_time']
                )
                
                session.add(model_metrics)
                session.commit()
                
                logger.info("Model metrics saved to database")
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

