import os
import requests
import hashlib
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class MediaHandler:
    def __init__(self, static_dir: str = "static", cache_manager=None):
        self.static_dir = static_dir
        self.cache_manager = cache_manager
        self.image_dir = os.path.join(static_dir, "images")
        self.video_dir = os.path.join(static_dir, "videos")
        self.audio_dir = os.path.join(static_dir, "audio")

        # 创建目录
        for dir_path in [self.image_dir, self.video_dir, self.audio_dir]:
            os.makedirs(dir_path, exist_ok=True)

    def download_media(self, url: str, media_type: str = "image") -> Optional[str]:
        """下载媒体文件并返回本地路径"""
        try:
            if self.cache_manager:
                cached_path = self.cache_manager.get_cached_media(url)
                if cached_path and os.path.exists(cached_path.lstrip('/')):
                    return cached_path

            # 生成文件名
            filename = self._generate_filename(url)

            # 确定保存目录
            if media_type == "image":
                save_dir = self.image_dir
                relative_path = f"/images/{filename}"
            elif media_type == "video":
                save_dir = self.video_dir
                relative_path = f"/videos/{filename}"
            elif media_type == "audio":
                save_dir = self.audio_dir
                relative_path = f"/audio/{filename}"
            else:
                return url

            file_path = os.path.join(save_dir, filename)

            # 如果文件已存在，直接返回
            if os.path.exists(file_path):
                return relative_path

            # 下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # 如果是图片，可以进行优化
            if media_type == "image":
                self._optimize_image(file_path)

            logger.info(f"Downloaded {media_type}: {filename}")

            # 下载成功后更新缓存
            if self.cache_manager and relative_path:
                self.cache_manager.cache_media(url, relative_path)

            return relative_path

        except Exception as e:
            logger.error(f"Error downloading media from {url}: {e}")
            return url  # 失败时返回原始URL

    def _generate_filename(self, url: str) -> str:
        """生成唯一的文件名"""
        # 从URL提取原始文件名
        parsed = urlparse(url)
        original_name = os.path.basename(unquote(parsed.path))

        # 如果没有文件名，使用URL的hash
        if not original_name or '.' not in original_name:
            hash_name = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"{hash_name}.jpg"  # 默认假设是jpg

        # 保留原始扩展名，但使用hash作为文件名避免冲突
        _, ext = os.path.splitext(original_name)
        hash_name = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{hash_name}{ext}"

    def _optimize_image(self, file_path: str, max_width: int = 1920):
        """优化图片尺寸和质量"""
        try:
            with Image.open(file_path) as img:
                # 转换为RGB（如果需要）
                if img.mode in ('RGBA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = rgb_img

                # 调整尺寸
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # 保存优化后的图片
                img.save(file_path, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            logger.warning(f"Failed to optimize image {file_path}: {e}")
