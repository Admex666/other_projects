"""
Quick test script for Instagram scraper
"""
import sys
sys.path.insert(0, '.')

try:
    import mocks
except ImportError:
    pass

from src.scraper.instagram_scraper import InstagramScraper

def test_scraper():
    print("=== Testing Instagram Scraper ===\n")
    
    scraper = InstagramScraper()
    
    # Test with a known public account
    username = "instagram"  # Instagram's official account
    
    # Get profile info
    print(f"1. Fetching profile info for @{username}...")
    profile = scraper.get_profile_info(username)
    
    if profile:
        print(f"   [OK] Username: {profile.get('username')}")
        print(f"   [OK] Followers: {profile.get('follower_count'):,}")
        print(f"   [OK] Posts: {profile.get('post_count'):,}")
        print(f"   [OK] Verified: {profile.get('is_verified')}")
    else:
        print("   [FAIL] Failed to fetch profile")
        return
    
    # Get posts
    print(f"\n2. Fetching 2 posts from @{username}...")
    posts = scraper.get_posts(username, count=2)
    
    if posts:
        print(f"   [OK] Successfully fetched {len(posts)} posts")
        for i, post in enumerate(posts, 1):
            print(f"\n   Post {i}:")
            print(f"     - ID: {post['post_id']}")
            print(f"     - Likes: {post['likes']:,}")
            print(f"     - Comments: {post['comments']:,}")
            print(f"     - Type: {post['media_type']}")
            print(f"     - Local path: {post['local_image_path']}")
            print(f"     - Caption preview: {post['caption'][:50]}..." if post['caption'] else "     - No caption")
    else:
        print("   [FAIL] Failed to fetch posts")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_scraper()
