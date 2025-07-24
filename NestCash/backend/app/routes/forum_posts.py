# app/routes/forum_posts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime
import logging

from app.models.forum_models import (
    ForumPostDocument, LikeDocument, CommentDocument, FollowDocument,
    PostCreate, PostUpdate, PostRead, PostListResponse,
    PostCategory, PrivacyLevel, FeedType, SortBy
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.forum_service import ForumService

router = APIRouter(prefix="/forum/posts", tags=["forum-posts"])
logger = logging.getLogger(__name__)

# === POST LÉTREHOZÁS ===
@router.post("/", response_model=PostRead, status_code=201)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        # Ha nincs megadva privacy_level, akkor használjuk a felhasználó alapértelmezett beállítását
        forum_service = ForumService()
        if post_data.privacy_level is None:
            user_settings = await forum_service.get_user_forum_settings(current_user.id)
            post_data.privacy_level = user_settings.default_privacy_level
        
        new_post = ForumPostDocument(
            user_id=PydanticObjectId(current_user.id),
            username=current_user.username,
            **post_data.model_dump()
        )
        
        await new_post.insert()
        
        return PostRead(
            id=str(new_post.id),
            user_id=str(new_post.user_id),
            username=new_post.username,
            title=new_post.title,
            content=new_post.content,
            category=new_post.category,
            privacy_level=new_post.privacy_level,
            created_at=new_post.created_at,
            updated_at=new_post.updated_at,
            like_count=new_post.like_count,
            comment_count=new_post.comment_count,
            is_liked_by_me=False,
            is_my_post=True
        )
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

# === POSZTOK LISTÁZÁSA ===
@router.get("/", response_model=PostListResponse)
async def list_posts(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    category: Optional[PostCategory] = Query(None),
    feed_type: FeedType = Query(FeedType.ALL),
    sort_by: SortBy = Query(SortBy.NEWEST),
    search: Optional[str] = Query(None, description="Keresés címben és tartalomban")
):
    try:
        # Alapszűrő építése
        query_filter = {}
        
        # Kategória szűrés
        if category:
            query_filter["category"] = category.value  # JAVÍTÁS: .value hozzáadása
        
        # Feed típus alapján szűrés
        if feed_type == FeedType.MY_POSTS:
            query_filter["user_id"] = ObjectId(current_user.id)
        elif feed_type == FeedType.FOLLOWING:
            # Csak követett felhasználók posztjai
            try:
                following_users = await FollowDocument.find(
                    {"follower_id": ObjectId(current_user.id)}
                ).to_list()
                following_ids = [follow.following_id for follow in following_users]
                following_ids.append(ObjectId(current_user.id))  # Saját posztok is
                query_filter["user_id"] = {"$in": following_ids}
            except Exception as e:
                logger.error(f"Error fetching following users: {e}")
                # Ha hiba van a követett felhasználók lekérésénél, csak saját posztok
                query_filter["user_id"] = ObjectId(current_user.id)
        
        # Láthatóság ellenőrzése (ha nem saját posztokat nézzük)
        if feed_type != FeedType.MY_POSTS:
            try:
                forum_service = ForumService()
                visibility_filter = await forum_service.build_visibility_filter(current_user.id)
                query_filter.update(visibility_filter)
            except Exception as e:
                logger.error(f"Error building visibility filter: {e}")
                # Alapértelmezett: csak publikus posztok
                query_filter["privacy_level"] = "public"
        
        # Keresés
        if search:
            query_filter["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}}
            ]
        
        # Rendezés - JAVÍTÁS: helyes MongoDB rendezési formátum
        if sort_by == SortBy.NEWEST:
            sort_criteria = [("created_at", -1)]
        elif sort_by == SortBy.POPULAR:
            sort_criteria = [("like_count", -1), ("created_at", -1)]
        elif sort_by == SortBy.MOST_COMMENTED:
            sort_criteria = [("comment_count", -1), ("created_at", -1)]
        else:
            sort_criteria = [("created_at", -1)]  # alapértelmezett
        
        # Lekérdezés végrehajtása
        try:
            total_count = await ForumPostDocument.find(query_filter).count()
            
            posts_query = ForumPostDocument.find(query_filter)
            for field, direction in sort_criteria:
                posts_query = posts_query.sort([(field, direction)])
            
            posts = await posts_query.skip(skip).limit(limit).to_list()
            
        except Exception as e:
            logger.error(f"Error executing database query: {e}")
            # Visszatérés üres eredménnyel hiba esetén
            return PostListResponse(
                posts=[],
                total_count=0,
                skip=skip,
                limit=limit
            )
        
        # Like-ok ellenőrzése a jelenlegi felhasználóra
        post_ids = [post.id for post in posts]
        user_likes = []
        if post_ids:  # JAVÍTÁS: csak ha vannak posztok
            try:
                user_likes = await LikeDocument.find({
                    "user_id": ObjectId(current_user.id),
                    "post_id": {"$in": post_ids}
                }).to_list()
            except Exception as e:
                logger.error(f"Error fetching user likes: {e}")
        
        liked_post_ids = {like.post_id for like in user_likes}
        
        # Válasz összeállítása
        read_posts = []
        for post in posts:
            try:
                read_posts.append(PostRead(
                    id=str(post.id),
                    user_id=str(post.user_id),
                    username=post.username or "Ismeretlen",  # JAVÍTÁS: None védelem
                    title=post.title or "",
                    content=post.content or "",
                    category=post.category,
                    privacy_level=post.privacy_level,
                    created_at=post.created_at,
                    updated_at=post.updated_at,
                    like_count=post.like_count or 0,  # JAVÍTÁS: None védelem
                    comment_count=post.comment_count or 0,  # JAVÍTÁS: None védelem
                    is_liked_by_me=post.id in liked_post_ids,
                    is_my_post=str(post.user_id) == current_user.id
                ))
            except Exception as e:
                logger.error(f"Error creating PostRead for post {post.id}: {e}")
                continue  # Kihagyjuk a hibás posztot
        
        return PostListResponse(
            posts=read_posts,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing posts: {e}")
        # JAVÍTÁS: részletesebb hibaüzenet a logban
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to list posts")

# === EGY POSZT LEKÉRÉSE ===
@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Láthatóság ellenőrzése
        forum_service = ForumService()
        if not await forum_service.can_user_see_post(current_user.id, post):
            raise HTTPException(status_code=403, detail="Not authorized to view this post")
        
        # Like ellenőrzése
        user_like = await LikeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "post_id": oid
        })
        
        return PostRead(
            id=str(post.id),
            user_id=str(post.user_id),
            username=post.username,
            title=post.title,
            content=post.content,
            category=post.category,
            privacy_level=post.privacy_level,
            created_at=post.created_at,
            updated_at=post.updated_at,
            like_count=post.like_count,
            comment_count=post.comment_count,
            is_liked_by_me=user_like is not None,
            is_my_post=str(post.user_id) == current_user.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get post")

# === POSZT FRISSÍTÉSE ===
@router.put("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Csak saját poszt szerkeszthető
        if str(post.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this post")
        
        # Frissítés
        update_data = post_data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            for key, value in update_data.items():
                setattr(post, key, value)
            await post.save()
        
        # Like ellenőrzése a válaszhoz
        user_like = await LikeDocument.find_one({
            "user_id": ObjectId(current_user.id),
            "post_id": oid
        })
        
        return PostRead(
            id=str(post.id),
            user_id=str(post.user_id),
            username=post.username,
            title=post.title,
            content=post.content,
            category=post.category,
            privacy_level=post.privacy_level,
            created_at=post.created_at,
            updated_at=post.updated_at,
            like_count=post.like_count,
            comment_count=post.comment_count,
            is_liked_by_me=user_like is not None,
            is_my_post=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")

# === POSZT TÖRLÉSE ===
@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        oid = PydanticObjectId(post_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid post ID")
    
    try:
        post = await ForumPostDocument.get(oid)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Csak saját poszt törölhető
        if str(post.user_id) != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        
        # Kapcsolódó adatok törlése
        await LikeDocument.find({"post_id": oid}).delete()
        await CommentDocument.find({"post_id": oid}).delete()
        
        # Poszt törlése
        await post.delete()
        
        return {"message": "Post deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete post")