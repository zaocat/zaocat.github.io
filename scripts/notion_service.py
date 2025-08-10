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

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Notion database"""
        result = {
            "success": False,
            "database_info": None,
            "error": None,
            "warnings": []
        }

        try:
            # 1. Test if Token is valid
            logger.info("Testing Notion API token...")
            user_info = self.client.users.me()
            logger.info(f"✅ Token is valid. Bot ID: {user_info['id']}")

            # 2. Test database access
            logger.info(f"Testing database access: {self.database_id}")
            database = self.client.databases.retrieve(database_id=self.database_id)

            # 3. Extract database information
            db_title = "Untitled"
            if database.get('title') and len(database['title']) > 0:
                db_title = database['title'][0]['plain_text']

            logger.info(f"✅ Successfully connected to database: {db_title}")

            # 4. Check required properties
            properties = database.get('properties', {})
            required_props = {
                'Title': 'title',
                'Published': 'checkbox',
                'Date': 'date',
                'Slug': 'rich_text',
                'Tags': 'multi_select'
            }

            missing_props = []
            wrong_type_props = []

            for prop_name, expected_type in required_props.items():
                if prop_name not in properties:
                    missing_props.append(prop_name)
                elif properties[prop_name].get('type') != expected_type:
                    actual_type = properties[prop_name].get('type', 'unknown')
                    wrong_type_props.append(
                        f"{prop_name} (expected {expected_type}, got {actual_type})"
                    )

            # 5. Generate warning messages
            if missing_props:
                warning = f"Missing properties: {', '.join(missing_props)}"
                result['warnings'].append(warning)
                logger.warning(f"⚠️  {warning}")

            if wrong_type_props:
                warning = f"Wrong property types: {', '.join(wrong_type_props)}"
                result['warnings'].append(warning)
                logger.warning(f"⚠️  {warning}")

            # 6. Test query permissions
            logger.info("Testing query permissions...")
            test_query = self.client.databases.query(
                database_id=self.database_id,
                page_size=1
            )

            total_posts = len(test_query.get('results', []))
            has_more = test_query.get('has_more', False)

            logger.info(f"✅ Query successful. Found at least {total_posts} post(s)")

            # 7. Summarize results
            result['success'] = True
            result['database_info'] = {
                'id': self.database_id,
                'title': db_title,
                'properties': list(properties.keys()),
                'total_properties': len(properties),
                'sample_post_count': total_posts,
                'has_more_posts': has_more
            }

            # 8. Display database properties
            logger.info("📋 Database Properties:")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'unknown')
                logger.info(f"   - {prop_name}: {prop_type}")

            return result

        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg

            # Provide more friendly error messages
            if "unauthorized" in error_msg.lower():
                logger.error("❌ Authorization failed!")
                logger.error("   Please check:")
                logger.error("   1. Your NOTION_TOKEN is correct")
                logger.error("   2. The Integration has access to the database")
                logger.error("   3. The database is shared with your Integration")
            elif "not found" in error_msg.lower():
                logger.error("❌ Database not found!")
                logger.error("   Please check:")
                logger.error("   1. Your NOTION_DATABASE_ID is correct")
                logger.error("   2. The ID format (with or without hyphens)")
            elif "rate_limited" in error_msg.lower():
                logger.error("❌ Rate limited by Notion API!")
                logger.error("   Please wait a moment and try again")
            else:
                logger.error(f"❌ Connection failed: {error_msg}")

            return result

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Query published posts
            published_response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Published",
                    "checkbox": {"equals": True}
                }
            )

            # Query all posts
            all_response = self.client.databases.query(
                database_id=self.database_id,
                page_size=1
            )

            published_count = len(published_response.get('results', []))

            # If there are more pages, show "at least" count
            published_more = published_response.get('has_more', False)
            all_more = all_response.get('has_more', False)

            stats = {
                'published_posts': f"{published_count}{'+ ' if published_more else ''}",
                'total_posts': f"{'at least ' if all_more else ''}1+",
                'database_id': self.database_id
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    @retry(max_attempts=3, delay=2, exceptions=(requests.RequestException,))
    def get_published_posts(self) -> List[NotionPost]:
        """Get all published posts"""
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
        """Parse page data"""
        try:
            post = NotionPost()
            post.id = page['id']

            props = page['properties']

            # Title
            if 'Title' in props and props['Title']['title']:
                post.title = props['Title']['title'][0]['plain_text']
            else:
                post.title = "Untitled"

            # Slug
            if 'Slug' in props and props['Slug']['rich_text']:
                post.slug = props['Slug']['rich_text'][0]['plain_text']
            else:
                post.slug = page['id'].replace('-', '')

            # Date
            if 'Date' in props and props['Date']['date']:
                post.date = datetime.fromisoformat(
                    props['Date']['date']['start'].replace('Z', '+00:00')
                )

            # Tags
            if 'Tags' in props and props['Tags']['multi_select']:
                post.tags = [tag['name'] for tag in props['Tags']['multi_select']]

            # Cover image
            if page.get('cover'):
                cover = page['cover']
                if cover['type'] == 'external':
                    post.cover_image = cover['external']['url']
                elif cover['type'] == 'file':
                    post.cover_image = cover['file']['url']

            # Last edited time
            post.last_edited = datetime.fromisoformat(
                page['last_edited_time'].replace('Z', '+00:00')
            )

            # Get all page blocks
            post.blocks = self._get_page_blocks(post.id)

            return post
        except Exception as e:
            logger.error(f"Error parsing page {page.get('id', 'unknown')}: {e}")
            return None

    def _get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all blocks of a page with full nested children (recursive)."""

        def fetch_children_recursively(block_id: str) -> List[Dict[str, Any]]:
            collected_blocks: List[Dict[str, Any]] = []
            local_has_more = True
            local_cursor = None

            while local_has_more:
                try:
                    if local_cursor:
                        resp = self.client.blocks.children.list(
                            block_id=block_id,
                            start_cursor=local_cursor
                        )
                    else:
                        resp = self.client.blocks.children.list(block_id=block_id)

                    items = resp.get('results', [])

                    for b in items:
                        # Recursively populate children for any block that has them
                        if b.get('has_children'):
                            try:
                                b['children'] = fetch_children_recursively(b['id'])
                            except Exception as child_err:
                                logger.warning(
                                    f"Failed to fetch children for block {b.get('id')}: {child_err}"
                                )
                                b['children'] = []

                        collected_blocks.append(b)

                    local_has_more = resp.get('has_more', False)
                    local_cursor = resp.get('next_cursor')
                except Exception as e:
                    logger.error(f"Error fetching children for block {block_id}: {e}")
                    break

            return collected_blocks

        # Top-level: page_id is also a block container for its direct children
        return fetch_children_recursively(page_id)

