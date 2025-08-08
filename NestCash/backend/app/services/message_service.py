from typing import List, Dict, Optional, Tuple
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime
import logging

from app.models.message_models import MessageDocument, ConversationDocument
from app.models.user import UserDocument

logger = logging.getLogger(__name__)

class MessageService:
    
    async def get_or_create_conversation(self, user1_id: str, user2_id: str) -> ConversationDocument:
        """Beszélgetés lekérése vagy létrehozása két felhasználó között"""
        try:
            oid1 = ObjectId(user1_id)
            oid2 = ObjectId(user2_id)
            
            # Keresés meglévő beszélgetésre (sorrendtől függetlenül)
            conversation = await ConversationDocument.find_one({
                "$or": [
                    {"participant_ids": [oid1, oid2]},
                    {"participant_ids": [oid2, oid1]}
                ]
            })
            
            if conversation:
                return conversation
            
            # Új beszélgetés létrehozása
            user1 = await UserDocument.get(oid1)
            user2 = await UserDocument.get(oid2)
            
            if not user1 or not user2:
                raise ValueError("One or both users not found")
            
            conversation = ConversationDocument(
                participant_ids=[oid1, oid2],
                participant_usernames=[user1.username, user2.username]
            )
            await conversation.insert()
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {e}")
            raise e
    
    async def send_message(self, sender_id: str, receiver_id: str, content: str) -> MessageDocument:
        """Üzenet küldése"""
        try:
            # Felhasználók ellenőrzése
            sender = await UserDocument.get(ObjectId(sender_id))
            receiver = await UserDocument.get(ObjectId(receiver_id))
            
            if not sender or not receiver:
                raise ValueError("Sender or receiver not found")
            
            # Üzenet létrehozása
            message = MessageDocument(
                sender_id=PydanticObjectId(sender_id),
                receiver_id=PydanticObjectId(receiver_id),
                sender_username=sender.username,
                receiver_username=receiver.username,
                content=content
            )
            await message.insert()
            
            # Beszélgetés frissítése
            conversation = await self.get_or_create_conversation(sender_id, receiver_id)
            conversation.last_message_id = message.id
            conversation.last_message_content = content
            conversation.last_message_at = message.created_at
            conversation.updated_at = datetime.utcnow()
            
            # Olvasatlan számláló növelése a címzettnek
            if str(conversation.participant_ids[0]) == receiver_id:
                conversation.unread_count_user1 += 1
            else:
                conversation.unread_count_user2 += 1
            
            await conversation.save()
            
            return message
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise e
    
    async def get_conversations(self, user_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[Dict], int]:
        """Felhasználó beszélgetéseinek lekérése"""
        try:
            oid = ObjectId(user_id)
            
            # Beszélgetések lekérése
            total_count = await ConversationDocument.find({
                "participant_ids": oid
            }).count()
            
            conversations = await ConversationDocument.find({
                "participant_ids": oid
            }).sort("-updated_at").skip(skip).limit(limit).to_list()
            
            # Formázás
            result = []
            for conv in conversations:
                # Másik résztvevő meghatározása
                other_user_idx = 0 if str(conv.participant_ids[1]) == user_id else 1
                other_user_id = str(conv.participant_ids[other_user_idx])
                other_username = conv.participant_usernames[other_user_idx]
                
                # Olvasatlan számláló meghatározása
                unread_count = conv.unread_count_user1 if str(conv.participant_ids[0]) == user_id else conv.unread_count_user2
                
                result.append({
                    "id": str(conv.id),
                    "other_user_id": other_user_id,
                    "other_username": other_username,
                    "last_message_content": conv.last_message_content,
                    "last_message_at": conv.last_message_at,
                    "unread_count": unread_count
                })
            
            return result, total_count
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            raise e
    
    async def get_messages(self, user_id: str, other_user_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[Dict], int]:
        """Beszélgetés üzeneteinek lekérése"""
        try:
            oid1 = ObjectId(user_id)
            oid2 = ObjectId(other_user_id)
            
            # Üzenetek lekérése
            query = {
                "$or": [
                    {"sender_id": oid1, "receiver_id": oid2},
                    {"sender_id": oid2, "receiver_id": oid1}
                ]
            }
            
            total_count = await MessageDocument.find(query).count()
            
            messages = await MessageDocument.find(query)\
                .sort("-created_at").skip(skip).limit(limit).to_list()
            
            # Olvasottnak jelölés (fogadott üzenetek)
            unread_received_messages = [msg for msg in messages 
                                      if str(msg.receiver_id) == user_id and not msg.is_read]
            
            for msg in unread_received_messages:
                msg.is_read = True
                await msg.save()
            
            # Beszélgetés olvasatlan számlálójának nullázása
            if unread_received_messages:
                conversation = await self.get_or_create_conversation(user_id, other_user_id)
                if str(conversation.participant_ids[0]) == user_id:
                    conversation.unread_count_user1 = 0
                else:
                    conversation.unread_count_user2 = 0
                await conversation.save()
            
            # Formázás
            result = []
            for msg in reversed(messages):  # Időrend szerinti sorrend
                result.append({
                    "id": str(msg.id),
                    "sender_id": str(msg.sender_id),
                    "receiver_id": str(msg.receiver_id),
                    "sender_username": msg.sender_username,
                    "receiver_username": msg.receiver_username,
                    "content": msg.content,
                    "is_read": msg.is_read,
                    "created_at": msg.created_at,
                    "is_my_message": str(msg.sender_id) == user_id
                })
            
            return result, total_count
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            raise e