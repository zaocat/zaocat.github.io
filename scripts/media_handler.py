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

        # Create directories
        for dir_path in [self.image_dir, self.video_dir, self.audio_dir]:
            os.makedirs(dir_path, exist_ok=True)

    def download_media(self, url: str, media_type: str = "image") -> Optional[str]:
        """Download media file and return local path"""
        try:
            if self.cache_manager:
                cached_path = self.cache_manager.get_cached_media(url)
                if cached_path and os.path.exists(cached_path.lstrip('/')):
                    return cached_path

            # Generate filename
            filename = self._generate_filename(url)

            # Determine save directory
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

            # If file already exists, return directly
            if os.path.exists(file_path):
                return relative_path

            # Download file
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Optimize image if applicable
            if media_type == "image":
                self._optimize_image(file_path)

            logger.info(f"Downloaded {media_type}: {filename}")

            # Update cache after successful download
            if self.cache_manager and relative_path:
                self.cache_manager.cache_media(url, relative_path)

            return relative_path

        except Exception as e:
            logger.error(f"Error downloading media from {url}: {e}")
            return url  # Return original URL on failure

    def _generate_filename(self, url: str) -> str:
        """Generate a unique filename"""
        # Extract original filename from URL
        parsed = urlparse(url)
        original_name = os.path.basename(unquote(parsed.path))

        # Use hash of URL if no filename present
        if not original_name or '.' not in original_name:
            hash_name = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"{hash_name}.jpg"  # 默认假设是jpg

        # Keep original extension but use hash as filename to avoid conflicts
        _, ext = os.path.splitext(original_name)
        hash_name = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"{hash_name}{ext}"

    def _optimize_image(self, file_path: str, max_width: int = 1920):
        """Optimize image size and quality"""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                    img = rgb_img

                # Resize if wider than max_width
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Save optimized image
                img.save(file_path, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            logger.warning(f"Failed to optimize image {file_path}: {e}")
