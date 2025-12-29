try:
    import instaloader
except ImportError:
    instaloader = None

import time
import random
import os
import glob
from typing import List, Dict, Any
from .scraper_interface import ScraperInterface

class InstagramScraper(ScraperInterface):
    """
    Real implementation using Instaloader.
    """
    def __init__(self, download_dir: str = "data/raw/images"):
        if not instaloader:
            raise ImportError("Instaloader is not installed. Please run `pip install instaloader`.")
        
        self.loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=False, 
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=False
        )
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    def get_profile_info(self, username: str) -> Dict[str, Any]:
        print(f"Fetching profile metadata for {username}...")
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            return {
                "username": profile.username,
                "follower_count": profile.followers,
                "biography": profile.biography or "",
                "post_count": profile.mediacount,
                "is_verified": profile.is_verified,
                "is_business_account": profile.is_business_account
            }
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return {}

    def get_posts(self, username: str, count: int = 50) -> List[Dict[str, Any]]:
        print(f"Fetching last {count} posts for {username}...")
        posts_data = []
        
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            posts = profile.get_posts()
            
            user_dir = os.path.join(self.download_dir, username)
            os.makedirs(user_dir, exist_ok=True)
            
            for i, post in enumerate(posts):
                if i >= count:
                    break
                
                print(f"Processing post {i+1}/{count}: {post.shortcode}")
                
                # Download image to specific directory
                image_path = self._download_post_image(post, username, user_dir)

                post_info = {
                    "post_id": post.shortcode,
                    "timestamp": post.date_utc.isoformat(),
                    "caption": post.caption if post.caption else "",
                    "likes": post.likes,
                    "comments": post.comments,
                    "is_reel": post.is_video,
                    "media_type": post.typename,
                    "media_url": post.url,
                    "local_image_path": image_path
                }
                posts_data.append(post_info)
                
                # Rate limit jitter
                time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"Error fetching posts: {e}")
            import traceback
            traceback.print_exc()
        
        return posts_data

    def _download_post_image(self, post, username, target_dir):
        """
        Download post image and return the local path.
        """
        try:
            # Create a unique filename based on shortcode
            shortcode = post.shortcode
            date_str = post.date_utc.strftime("%Y-%m-%d_%H-%M-%S")
            
            # Try to download the post
            if post.typename == "GraphImage":
                # Single image
                filename = f"{date_str}_{shortcode}.jpg"
                filepath = os.path.join(target_dir, filename)
                
                if not os.path.exists(filepath):
                    self.loader.download_pic(filename=filepath, url=post.url, mtime=post.date_utc)
                
                return filepath
                
            elif post.typename == "GraphSidecar":
                # Carousel - download first image
                filename = f"{date_str}_{shortcode}_1.jpg"
                filepath = os.path.join(target_dir, filename)
                
                if not os.path.exists(filepath):
                    # Get first image from carousel
                    nodes = list(post.get_sidecar_nodes())
                    if nodes:
                        self.loader.download_pic(filename=filepath, url=nodes[0].display_url, mtime=post.date_utc)
                
                return filepath
                
            elif post.typename == "GraphVideo":
                # Video - download thumbnail
                filename = f"{date_str}_{shortcode}_thumb.jpg"
                filepath = os.path.join(target_dir, filename)
                
                if not os.path.exists(filepath):
                    self.loader.download_pic(filename=filepath, url=post.url, mtime=post.date_utc)
                
                return filepath
            
            return ""
            
        except Exception as e:
            print(f"Failed to download image for {post.shortcode}: {e}")
            return ""
