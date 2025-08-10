import json
import os
from datetime import datetime
from typing import Dict, Optional

class CacheManager:
    def __init__(self, cache_file: str = ".notion_cache.json"):
        self.cache_file = cache_file
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict:
        """加载缓存数据"""
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
        """保存缓存数据"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_data, f, indent=2, default=str)

    def should_update_post(self, post_id: str, last_edited: datetime) -> bool:
        """检查文章是否需要更新"""
        if post_id not in self.cache_data["posts"]:
            return True

        cached_time = datetime.fromisoformat(self.cache_data["posts"][post_id])
        return last_edited > cached_time

    def update_post_cache(self, post_id: str, last_edited: datetime):
        """更新文章缓存"""
        self.cache_data["posts"][post_id] = last_edited.isoformat()

    def get_cached_media(self, url: str) -> Optional[str]:
        """获取缓存的媒体文件路径"""
        return self.cache_data["media"].get(url)

    def cache_media(self, url: str, local_path: str):
        """缓存媒体文件路径"""
        self.cache_data["media"][url] = local_path

    def update_last_sync(self):
        """更新最后同步时间"""
        self.cache_data["last_sync"] = datetime.now().isoformat()
