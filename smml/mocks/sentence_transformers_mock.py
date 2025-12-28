import numpy as np

class SentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name
    def encode(self, texts):
        return np.random.normal(0, 1, (len(texts), 384))
