# app/routes/forum_interactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from beanie import PydanticObjectId
from bson import ObjectId
import logging
from datetime import datetime

from app.models.forum_models import (
    ForumPostDocument, LikeDocument, CommentDocument, NotificationDocument,
    CommentCreate, CommentRead, CommentListResponse,
    NotificationType
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.forum_service import ForumService

router = APIRouter(prefix="/forum", tags=["forum-interactions"])
logger = logging.getLogger(__name__)

# === LIKE TOGGLE ===
@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        # Poszt létezésének ellenőrzése és láthatóság
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        forum_service = ForumService()
        if not await forum_service.can_user_see_post(current_user.id, post):
            raise HTTPException(status_code=403, detail="Not authorized to like this post")
        
        # Ellenőrizzük, hogy már like-olta-e
        existing_like = await LikeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "post_id": oid
        })
        
        if existing_like:
            # Like eltávolítása
            await existing_like.delete()
            post.like_count = max(0, post.like_count - 1)
            await post.save()
            
            return {
                "message": "Like removed",
                "is_liked": False,
                "like_count": post.like_count
            }
        else:
            # Like hozzáadása
            new_like = LikeDocument(
                post_id=oid,
                user_id=PydanticObjectId(current_user.id),
                username=current_user.username
            )
            await new_like.insert()
            
            post.like_count += 1
            await post.save()
            
            # Értesítés küldése (ha nem saját poszt)
            if str(post.user_id) != current_user.id:
                await forum_service.create_notification(
                    user_id=str(post.user_id),
                    from_user_id=current_user.id,
                    from_username=current_user.username,
                    notification_type=NotificationType.LIKE,
                    post_id=str(post.id),
                    message=f"{current_user.username} liked your post: {post.title[:50]}..."
                )
            
            return {
                "message": "Post liked",
                "is_liked": True,
                "like_count": post.like_count
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling like on post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle like")

# === KOMMENTEK LISTÁZÁSA ===
@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        # Poszt létezésének ellenőrzése és láthatóság
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        forum_service = ForumService()
        if not await forum_service.can_user_see_post(current_user.id, post):
            raise HTTPException(status_code=403, detail="Not authorized to view comments")
        
        # Kommentek lekérdezése
        total_count = await CommentDocument.find({"post_id": oid}).count()
        comments = await CommentDocument.find({"post_id": oid})\
            .sort("created_at")\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Válasz összeállítása
        read_comments = []
        for comment in comments:
            read_comments.append(CommentRead(
                id=str(comment.id),
                post_id=str(comment.post_id),
                user_id=str(comment.user_id),
                username=comment.username,
                content=comment.content,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
                is_my_comment=str(comment.user_id) == current_user.id
            ))
        
        return CommentListResponse(
            comments=read_comments,
            total_count=total_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing comments for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list comments")

# === KOMMENT LÉTREHOZÁSA ===
@router.post("/posts/{post_id}/comments", response_model=CommentRead, status_code=201)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        # Poszt létezésének ellenőrzése és láthatóság
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        forum_service = ForumService()
        if not await forum_service.can_user_see_post(current_user.id, post):
            raise HTTPException(status_code=403, detail="Not authorized to comment on this post")
        
        # Komment létrehozása
        new_comment = CommentDocument(
            post_id=oid,
            user_id=PydanticObjectId(current_user.id),
            username=current_user.username,
            content=comment_data.content
        )
        await new_comment.insert()
        
        # Poszt komment számának frissítése
        post.comment_count += 1
        await post.save()
        
        # Értesítés küldése (ha nem saját poszt)
        if str(post.user_id) != current_user.id:
            await forum_service.create_notification(
                user_id=str(post.user_id),
                from_user_id=current_user.id,
                from_username=current_user.username,
                notification_type=NotificationType.COMMENT,
                post_id=str(post.id),
                message=f"{current_user.username} commented on your post: {post.title[:50]}..."
            )
        
        return CommentRead(
            id=str(new_comment.id),
            post_id=str(new_comment.post_id),
            user_id=str(new_comment.user_id),
            username=new_comment.username,
            content=new_comment.content,
            created_at=new_comment.created_at,
            updated_at=new_comment.updated_at,
            is_my_comment=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment on post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create comment")

# === KOMMENT TÖRLÉSE ===
@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(comment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid comment ID")
    
    try:
        comment = await CommentDocument.get(oid)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Csak saját komment törölhető
        if str(comment.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
        
        # Poszt komment számának csökkentése
        post = await ForumPostDocument.get(comment.post_id)
        if post:
            post.comment_count = max(0, post.comment_count - 1)
            await post.save()
        
        # Komment törlése
        await comment.delete()
        
        return {"message": "Comment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete comment")

# === POSZT LIKE-JAINAK LISTÁZÁSA ===
@router.get("/posts/{post_id}/likes")
async def list_post_likes(
    post_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        # Poszt létezésének ellenőrzése és láthatóság
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        forum_service = ForumService()
        if not await forum_service.can_user_see_post(current_user.id, post):
            raise HTTPException(status_code=403, detail="Not authorized to view likes")
        
        # Like-ok lekérdezése
        total_count = await LikeDocument.find({"post_id": oid}).count()
        likes = await LikeDocument.find({"post_id": oid})\
            .sort("-created_at")\
            .skip(skip)\
            .limit(limit)\
            .to_list()
        
        # Válasz összeállítása
        like_list = []
        for like in likes:
            like_list.append({
                "user_id": str(like.user_id),
                "username": like.username,
                "created_at": like.created_at
            })
        
        return {
            "likes": like_list,
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing likes for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list likes")