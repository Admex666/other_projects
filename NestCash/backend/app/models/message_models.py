from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId
from bson import ObjectId

class MessageDocument(Document):
    sender_id: PydanticObjectId
    receiver_id: PydanticObjectId
    sender_username: str  # Denormalizált adat
    receiver_username: str  # Denormalizált adat
    content: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "private_messages"

class ConversationDocument(Document):
    participant_ids: List[PydanticObjectId] = Field(max_items=2, min_items=2)  # Pontosan 2 résztvevő
    participant_usernames: List[str] = Field(max_items=2, min_items=2)
    last_message_id: Optional[PydanticObjectId] = None
    last_message_content: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count_user1: int = Field(default=0)  # participant_ids[0] olvasatlan száma
    unread_count_user2: int = Field(default=0)  # participant_ids[1] olvasatlan száma
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "conversations"

# Response schemas
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)

class MessageRead(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    sender_username: str
    receiver_username: str
    content: str
    is_read: bool
    created_at: datetime
    is_my_message: bool = Field(default=False)

class ConversationRead(BaseModel):
    id: str
    other_user_id: str
    other_username: str
    last_message_content: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = Field(default=0)

class ConversationListResponse(BaseModel):
    conversations: List[ConversationRead]
    total_count: int

class MessageListResponse(BaseModel):
    messages: List[MessageRead]
    total_count: int