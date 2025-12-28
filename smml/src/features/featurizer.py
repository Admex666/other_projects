import pandas as pd
import numpy as np
import datetime
from typing import List, Dict, Any
from .text_processor import TextProcessor
from .image_processor import ImageProcessor

class Featurizer:
    """
    Orchestrates the extraction of multimodal features for posts.
    """
    def __init__(self):
        self.text_proc = TextProcessor()
        self.img_proc = ImageProcessor()

    def process_all_posts(self, posts: List[Dict[str, Any]], profile_info: Dict[str, Any]) -> pd.DataFrame:
        """
        Creates a unified DataFrame with all features extracted.
        """
        data = []
        for post in posts:
            # 1. Context Features
            feat = self._extract_context_features(post, profile_info)
            
            # 2. Text Features
            text_feat = self.text_proc.extract_linguistic_features(post['caption'])
            feat.update(text_feat)
            
            # 3. Visual Features (Basic)
            visual_feat = self.img_proc.extract_visual_features("") # Empty path for mock
            feat.update(visual_feat)
            
            # 4. Embeddings (as list/flattened)
            # In a production system, these would be stored separately or flattened
            feat['text_embedding'] = self.text_proc.get_embeddings([post['caption']])[0].tolist()
            feat['actual_engagement'] = post['likes'] + post['comments']
            
            data.append(feat)
            
        return pd.DataFrame(data)

    def _extract_context_features(self, post: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        ts = datetime.datetime.fromisoformat(post['timestamp'])
        return {
            "post_id": post['post_id'],
            "follower_count_log": np.log1p(profile['follower_count']),
            "hour_of_day": ts.hour,
            "day_of_week": ts.weekday(),
            "is_reel": 1 if post.get('is_reel') else 0,
            "is_carousel": 1 if post.get('media_type') == "CAROUSEL" else 0
        }
