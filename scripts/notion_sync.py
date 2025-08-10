#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from tqdm import tqdm

from notion_client import NotionClient
from hugo_converter import HugoConverter
from media_handler import MediaHandler

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # 加载环境变量
    load_dotenv()

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Sync Notion posts to Hugo')
    parser.add_argument('--notion-token', default=os.getenv('NOTION_TOKEN'),
                        help='Notion API token')
    parser.add_argument('--database-id', default=os.getenv('NOTION_DATABASE_ID'),
                        help='Notion database ID')
    parser.add_argument('--content-dir', default='./content',
                        help='Hugo content directory')
    parser.add_argument('--static-dir', default='./static',
                        help='Hugo static directory')
    parser.add_argument('--clean', action='store_true',
                        help='Clean existing posts before sync')

    args = parser.parse_args()

    # 验证必需的参数
    if not args.notion_token or not args.database_id:
        logger.error("NOTION_TOKEN and NOTION_DATABASE_ID are required")
        sys.exit(1)

    try:
        # 初始化组件
        notion_client = NotionClient(args.notion_token, args.database_id)
        media_handler = MediaHandler(args.static_dir)
        hugo_converter = HugoConverter(args.content_dir, media_handler)

        # 清理现有文章
        if args.clean:
            logger.info("Cleaning existing posts...")
            hugo_converter.clean_posts_directory()

        # 获取 Notion 文章
        logger.info("Fetching posts from Notion...")
        posts = notion_client.get_published_posts()
        logger.info(f"Found {len(posts)} published posts")

        # 转换文章
        success_count = 0
        with tqdm(total=len(posts), desc="Converting posts") as pbar:
            for post in posts:
                pbar.set_description(f"Converting: {post.title[:30]}...")
                if hugo_converter.convert_post(post):
                    success_count += 1
                pbar.update(1)
            else:
                logger.error(f"Failed to convert: {post.title}")

        # 汇总结果
        logger.info(f"Successfully converted {success_count}/{len(posts)} posts")

        if success_count < len(posts):
            sys.exit(1)

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
