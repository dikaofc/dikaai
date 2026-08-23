"""
DikaAI Model - Neural network, tokenizer, and training pipeline.

Components:
    DikaModel       - LSTM text predictor (pure Python, no numpy)
    DikaTokenizer   - Indonesian chat tokenizer with slang normalization
    DikaTrainer     - Fully automatic training pipeline
"""

from dikaai.model.model import DikaModel, get_lr
from dikaai.model.tokenizer import DikaTokenizer, _is_noise, _is_indonesian
from dikaai.model.trainer import DikaTrainer

__all__ = [
    'DikaModel',
    'DikaTokenizer',
    'DikaTrainer',
    'get_lr',
    '_is_noise',
    '_is_indonesian',
]
