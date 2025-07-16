from typing import Optional
from beanie import Document

class Item(Document):
    text: Optional[str]
    is_done: bool = False

    class Settings:
        name = "items"
