import json
import os
from datetime import datetime
from typing import Dict, Optional

class CacheManager:
    def __init__(self, cache_file: str = ".notion_cache.json"):
        self.cache_file = cache_file
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache data"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_sync": None,
            "posts": {},
            "media": {}
        }

    def save_cache(self):
        """Save cache data"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_data, f, indent=2, default=str)

    def should_update_post(self, post_id: str, last_edited: datetime) -> bool:
        """Check whether a post needs updating"""
        if post_id not in self.cache_data["posts"]:
            return True

        cached_time = datetime.fromisoformat(self.cache_data["posts"][post_id])
        return last_edited > cached_time

    def update_post_cache(self, post_id: str, last_edited: datetime):
        """Update post cache"""
        self.cache_data["posts"][post_id] = last_edited.isoformat()

    def get_cached_media(self, url: str) -> Optional[str]:
        """Get cached media file path"""
        return self.cache_data["media"].get(url)

    def cache_media(self, url: str, local_path: str):
        """Cache media file path"""
        self.cache_data["media"][url] = local_path

    def update_last_sync(self):
        """Update last sync time"""
        self.cache_data["last_sync"] = datetime.now().isoformat()
