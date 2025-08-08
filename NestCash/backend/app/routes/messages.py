from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from beanie import PydanticObjectId
import logging

from app.models.message_models import (
    MessageCreate, MessageRead, ConversationRead, 
    ConversationListResponse, MessageListResponse
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["messages"])
logger = logging.getLogger(__name__)

@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    try:
        service = MessageService()
        conversations_data, total_count = await service.get_conversations(
            current_user.id, skip, limit
        )
        
        conversations = [ConversationRead(**conv) for conv in conversations_data]
        
        return ConversationListResponse(
            conversations=conversations,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")

@router.get("/conversations/{other_user_id}", response_model=MessageListResponse)
async def get_messages(
    other_user_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    try:
        PydanticObjectId(other_user_id)  # Validate ID
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if other_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    
    try:
        service = MessageService()
        messages_data, total_count = await service.get_messages(
            current_user.id, other_user_id, skip, limit
        )
        
        messages = [MessageRead(**msg) for msg in messages_data]
        
        return MessageListResponse(
            messages=messages,
            total_count=total_count
        )
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")

@router.post("/conversations/{other_user_id}", response_model=MessageRead, status_code=201)
async def send_message(
    other_user_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        PydanticObjectId(other_user_id)  # Validate ID
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if other_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    
    try:
        service = MessageService()
        message = await service.send_message(
            current_user.id, other_user_id, message_data.content
        )
        
        return MessageRead(
            id=str(message.id),
            sender_id=str(message.sender_id),
            receiver_id=str(message.receiver_id),
            sender_username=message.sender_username,
            receiver_username=message.receiver_username,
            content=message.content,
            is_read=message.is_read,
            created_at=message.created_at,
            is_my_message=True
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.get("/unread-count")
async def get_unread_message_count(
    current_user: User = Depends(get_current_user)
):
    try:
        from app.models.message_models import ConversationDocument
        from bson import ObjectId
        
        conversations = await ConversationDocument.find({
            "participant_ids": ObjectId(current_user.id)
        }).to_list()
        
        total_unread = 0
        for conv in conversations:
            if str(conv.participant_ids[0]) == current_user.id:
                total_unread += conv.unread_count_user1
            else:
                total_unread += conv.unread_count_user2
        
        return {"unread_count": total_unread}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")