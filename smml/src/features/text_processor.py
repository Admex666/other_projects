from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class TextProcessor:
    """
    Handles text embedding and linguistic feature extraction.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Load pre-trained model
        self.model = SentenceTransformer(model_name)

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Extract SBERT embeddings for a list of texts.
        """
        return self.model.encode(texts)

    def extract_linguistic_features(self, text: str) -> dict:
        """
        Extract rule-based linguistic features.
        """
        return {
            "caption_length": len(text),
            "hashtag_count": text.count("#"),
            "emoji_count": self._count_emojis(text),
            "is_question": "?" in text
        }

    def _count_emojis(self, text: str) -> int:
        # Simple placeholder for emoji counting logic
        return len([char for char in text if ord(char) > 127])
