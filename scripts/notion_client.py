from datetime import datetime
from typing import List, Dict, Any, Optional
from notion_client import Client
from retry_decorator import retry
import logging
import requests

logger = logging.getLogger(__name__)

class NotionPost:
    def __init__(self):
        self.id: str = ""
        self.title: str = ""
        self.slug: str = ""
        self.date: datetime = datetime.now()
        self.tags: List[str] = []
        self.content: str = ""
        self.last_edited: datetime = datetime.now()
        self.cover_image: Optional[str] = None
        self.blocks: List[Dict[str, Any]] = []

class NotionClient:
    def __init__(self, token: str, database_id: str):
        self.client = Client(auth=token)
        self.database_id = database_id

    @retry(max_attempts=3, delay=2, exceptions=(requests.RequestException,))
    def get_published_posts(self) -> List[NotionPost]:
        """获取所有已发布的文章"""
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Published",
                    "checkbox": {
                        "equals": True
                    }
                }
            )

            posts = []
            for page in response['results']:
                post = self._parse_page(page)
                if post:
                    posts.append(post)

            return posts
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []

    def _parse_page(self, page: Dict[str, Any]) -> Optional[NotionPost]:
        """解析页面数据"""
        try:
            post = NotionPost()
            post.id = page['id']

            props = page['properties']

            # 标题
            if 'Title' in props and props['Title']['title']:
                post.title = props['Title']['title'][0]['plain_text']
            else:
                post.title = "Untitled"

            # Slug
            if 'Slug' in props and props['Slug']['rich_text']:
                post.slug = props['Slug']['rich_text'][0]['plain_text']
            else:
                post.slug = page['id'].replace('-', '')

            # 日期
            if 'Date' in props and props['Date']['date']:
                post.date = datetime.fromisoformat(
                    props['Date']['date']['start'].replace('Z', '+00:00')
                )

            # 标签
            if 'Tags' in props and props['Tags']['multi_select']:
                post.tags = [tag['name'] for tag in props['Tags']['multi_select']]

            # 封面图片
            if page.get('cover'):
                cover = page['cover']
                if cover['type'] == 'external':
                    post.cover_image = cover['external']['url']
                elif cover['type'] == 'file':
                    post.cover_image = cover['file']['url']

            # 最后编辑时间
            post.last_edited = datetime.fromisoformat(
                page['last_edited_time'].replace('Z', '+00:00')
            )

            # 获取页面内容块
            post.blocks = self._get_page_blocks(post.id)

            return post
        except Exception as e:
            logger.error(f"Error parsing page {page.get('id', 'unknown')}: {e}")
            return None

    def _get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """获取页面的所有块"""
        blocks = []
        has_more = True
        cursor = None

        while has_more:
            try:
                if cursor:
                    response = self.client.blocks.children.list(
                        block_id=page_id,
                        start_cursor=cursor
                    )
                else:
                    response = self.client.blocks.children.list(block_id=page_id)

                blocks.extend(response['results'])
                has_more = response['has_more']
                cursor = response.get('next_cursor')
            except Exception as e:
                logger.error(f"Error fetching blocks for page {page_id}: {e}")
                break

        return blocks
