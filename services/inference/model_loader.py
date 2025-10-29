"""
Загрузчик моделей для inference
"""
import os
import pickle
from pathlib import Path
from typing import Optional, Dict
import torch
from loguru import logger

from services.training.models import SimpleTextClassifier


class ModelLoader:
    """Класс для загрузки обученных моделей"""
    
    def __init__(self, model_dir: str = 'data/models'):
        """
        Инициализация загрузчика
        
        Args:
            model_dir: Директория с моделями
        """
        self.model_dir = Path(model_dir)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"ModelLoader initialized, device: {self.device}")
    
    def load_model(
        self,
        model_name: str,
        version: str = 'latest'
    ) -> Optional[torch.nn.Module]:
        """
        Загрузка модели
        
        Args:
            model_name: Имя модели
            version: Версия модели
            
        Returns:
            Загруженная модель или None
        """
        try:
            model_path = self.model_dir / f"{model_name}_{version}.pth"
            label_map_path = self.model_dir / f"{model_name}_labels.pkl"
            
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return None
            
            # Загрузка label mapping для определения num_classes
            with open(label_map_path, 'rb') as f:
                label_mapping = pickle.load(f)
            
            num_classes = len(label_mapping['idx_to_label'])
            
            # Загрузка векторизатора для определения input_size
            vectorizer = self.load_vectorizer(model_name)
            if vectorizer is None:
                return None
            
            input_size = len(vectorizer.get_feature_names_out())
            
            # Создание модели
            model = SimpleTextClassifier(
                input_size=input_size,
                num_classes=num_classes,
                hidden_sizes=[512, 256]
            )
            
            # Загрузка весов
            state_dict = torch.load(model_path, map_location=self.device)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            
            logger.info(f"Model loaded: {model_name}_{version}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def load_vectorizer(self, model_name: str):
        """
        Загрузка векторизатора
        
        Args:
            model_name: Имя модели
            
        Returns:
            TfidfVectorizer или None
        """
        try:
            vectorizer_path = self.model_dir / f"{model_name}_vectorizer.pkl"
            
            if not vectorizer_path.exists():
                logger.error(f"Vectorizer file not found: {vectorizer_path}")
                return None
            
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
            
            logger.info(f"Vectorizer loaded for model: {model_name}")
            return vectorizer
            
        except Exception as e:
            logger.error(f"Error loading vectorizer: {e}")
            return None
    
    def load_label_mapping(self, model_name: str) -> Optional[Dict]:
        """
        Загрузка маппинга меток
        
        Args:
            model_name: Имя модели
            
        Returns:
            Словарь с маппингом или None
        """
        try:
            label_map_path = self.model_dir / f"{model_name}_labels.pkl"
            
            if not label_map_path.exists():
                logger.error(f"Label mapping file not found: {label_map_path}")
                return None
            
            with open(label_map_path, 'rb') as f:
                label_mapping = pickle.load(f)
            
            logger.info(f"Label mapping loaded for model: {model_name}")
            return label_mapping
            
        except Exception as e:
            logger.error(f"Error loading label mapping: {e}")
            return None
    
    def load_all_artifacts(
        self,
        model_name: str,
        version: str = 'latest'
    ) -> Optional[Dict]:
        """
        Загрузка всех артефактов модели
        
        Args:
            model_name: Имя модели
            version: Версия модели
            
        Returns:
            Словарь с артефактами или None
        """
        model = self.load_model(model_name, version)
        if model is None:
            return None
        
        vectorizer = self.load_vectorizer(model_name)
        if vectorizer is None:
            return None
        
        label_mapping = self.load_label_mapping(model_name)
        if label_mapping is None:
            return None
        
        return {
            'model': model,
            'vectorizer': vectorizer,
            'label_mapping': label_mapping
        }

