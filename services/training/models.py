"""
Модели классификации документов
"""
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from loguru import logger


class DocumentClassifier(nn.Module):
    """Классификатор документов на основе текстовых признаков"""
    
    def __init__(
        self,
        num_classes: int,
        model_name: str = 'distilbert-base-uncased',
        dropout: float = 0.3
    ):
        """
        Инициализация классификатора
        
        Args:
            num_classes: Количество классов документов
            model_name: Название предобученной модели
            dropout: Dropout вероятность
        """
        super(DocumentClassifier, self).__init__()
        
        self.num_classes = num_classes
        self.model_name = model_name
        
        # Загрузка предобученной модели
        self.encoder = AutoModel.from_pretrained(model_name)
        self.hidden_size = self.encoder.config.hidden_size
        
        # Классификационная голова
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(self.hidden_size, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes)
        )
        
        logger.info(
            f"DocumentClassifier initialized: {model_name}, "
            f"{num_classes} classes, hidden_size={self.hidden_size}"
        )
    
    def forward(self, input_ids, attention_mask):
        """
        Forward pass
        
        Args:
            input_ids: Токенизированный текст
            attention_mask: Маска внимания
            
        Returns:
            Логиты классификации
        """
        # Получение эмбеддингов
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        # Используем [CLS] токен для классификации
        pooled_output = outputs.last_hidden_state[:, 0, :]
        
        # Классификация
        logits = self.classifier(pooled_output)
        
        return logits
    
    def predict(self, input_ids, attention_mask, return_probabilities=True):
        """
        Предсказание классов документов
        
        Args:
            input_ids: Токенизированный текст
            attention_mask: Маска внимания
            return_probabilities: Возвращать вероятности вместо логитов
            
        Returns:
            Предсказанные классы и их вероятности
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(input_ids, attention_mask)
            
            if return_probabilities:
                probabilities = torch.softmax(logits, dim=1)
                return probabilities
            
            return logits


class SimpleTextClassifier(nn.Module):
    """Простой классификатор на основе TF-IDF + MLP"""
    
    def __init__(
        self,
        input_size: int,
        num_classes: int,
        hidden_sizes: list = [512, 256],
        dropout: float = 0.3
    ):
        """
        Инициализация простого классификатора
        
        Args:
            input_size: Размер входного вектора (TF-IDF размерность)
            num_classes: Количество классов
            hidden_sizes: Размеры скрытых слоев
            dropout: Dropout вероятность
        """
        super(SimpleTextClassifier, self).__init__()
        
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.BatchNorm1d(hidden_size)
            ])
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, num_classes))
        
        self.network = nn.Sequential(*layers)
        
        logger.info(
            f"SimpleTextClassifier initialized: "
            f"input={input_size}, classes={num_classes}, hidden={hidden_sizes}"
        )
    
    def forward(self, x):
        """Forward pass"""
        return self.network(x)
    
    def predict(self, x, return_probabilities=True):
        """Предсказание классов"""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            
            if return_probabilities:
                probabilities = torch.softmax(logits, dim=1)
                return probabilities
            
            return logits

