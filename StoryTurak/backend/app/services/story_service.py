import json
import os
import logging

logger = logging.getLogger(__name__)

STORY_DATA = {}

def load_stories():
    STORY_DATA.clear()
    
    # Get absolute path to the data directory
    # Relative to backend/app/services/story_service.py -> ../../../data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory not found at {data_dir}")
        return {}

    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            p = os.path.join(data_dir, filename)
            try:
                with open(p, "r", encoding="utf-8") as f:
                    story = json.load(f)
                    STORY_DATA[story["id"]] = story
                    logger.info(f"Successfully loaded story: {story['id']} from {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    if not STORY_DATA:
        logger.warning("No stories were loaded!")
    
    return STORY_DATA

def get_all_stories():
    if not STORY_DATA:
        load_stories()
    return list(STORY_DATA.values())

def get_story_by_id(story_id: str):
    if not STORY_DATA:
        load_stories()
    return STORY_DATA.get(story_id)
