import os
import re
import yaml
from datetime import datetime
from typing import List, Dict, Any
from markdownify import markdownify as md
import logging

logger = logging.getLogger(__name__)

class HugoConverter:
    def __init__(self, content_dir: str, media_handler):
        self.content_dir = content_dir
        self.media_handler = media_handler
        self.posts_dir = os.path.join(content_dir, "posts")
        os.makedirs(self.posts_dir, exist_ok=True)

    def convert_post(self, post) -> bool:
        """将 Notion 文章转换为 Hugo 格式"""
        try:
            # 转换内容
            content = self._blocks_to_markdown(post.blocks)

            # 创建 front matter
            front_matter = {
                'title': post.title,
                'date': post.date.isoformat(),
                'lastmod': post.last_edited.isoformat(),
                'slug': post.slug,
                'tags': post.tags,
                'draft': False,
                'math': self._has_math(post.blocks),  # 检测是否包含数学公式
            }

            # 添加封面图片
            if post.cover_image:
                local_cover = self.media_handler.download_media(post.cover_image, "image")
                if local_cover:
                    front_matter['cover'] = local_cover

            # 生成完整的 Markdown 文件
            file_content = "---\\n"
            file_content += yaml.dump(front_matter, allow_unicode=True, default_flow_style=False)
            file_content += "---\\n\\n"
            file_content += content

            # 保存文件
            filename = f"{post.slug}.md"
            file_path = os.path.join(self.posts_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)

            logger.info(f"Converted post: {post.title}")
            return True

        except Exception as e:
            logger.error(f"Error converting post {post.title}: {e}")
            return False

    def _blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """将 Notion 块转换为 Markdown"""
        markdown_parts = []

        for block in blocks:
            block_type = block['type']
            markdown = self._convert_block(block)
            if markdown:
                markdown_parts.append(markdown)

        return '\\n\\n'.join(markdown_parts)

    def _convert_block(self, block: Dict[str, Any]) -> str:
        """转换单个块"""
        block_type = block['type']

        try:
            if block_type == 'paragraph':
                return self._convert_paragraph(block)
            elif block_type.startswith('heading_'):
                return self._convert_heading(block)
            elif block_type == 'bulleted_list_item':
                return self._convert_list_item(block, '- ')
            elif block_type == 'numbered_list_item':
                return self._convert_list_item(block, '1. ')
            elif block_type == 'code':
                return self._convert_code(block)
            elif block_type == 'quote':
                return self._convert_quote(block)
            elif block_type == 'divider':
                return '---'
            elif block_type == 'image':
                return self._convert_image(block)
            elif block_type == 'video':
                return self._convert_video(block)
            elif block_type == 'audio':
                return self._convert_audio(block)
            elif block_type == 'equation':
                return self._convert_equation(block)
            elif block_type == 'toggle':
                return self._convert_toggle(block)
            elif block_type == 'callout':
                return self._convert_callout(block)
            else:
                logger.warning(f"Unsupported block type: {block_type}")
                return ""
        except Exception as e:
            logger.error(f"Error converting block type {block_type}: {e}")
            return ""

    def _convert_paragraph(self, block: Dict[str, Any]) -> str:
        """转换段落"""
        text = self._rich_text_to_markdown(block['paragraph']['rich_text'])
        return text if text else ""

    def _convert_heading(self, block: Dict[str, Any]) -> str:
        """转换标题"""
        level = block['type'].split('_')[1]
        text = self._rich_text_to_markdown(block[block['type']]['rich_text'])
        return f"{'#' * int(level)} {text}"

    def _convert_list_item(self, block: Dict[str, Any], prefix: str) -> str:
        """转换列表项"""
        text = self._rich_text_to_markdown(block[block['type']]['rich_text'])
        return f"{prefix}{text}"

    def _convert_code(self, block: Dict[str, Any]) -> str:
        """转换代码块"""
        code_info = block['code']
        language = code_info.get('language', '').lower()
        code_text = self._rich_text_to_plain_text(code_info['rich_text'])

        return f"```{language}\\n{code_text}\\n```"

    def _convert_quote(self, block: Dict[str, Any]) -> str:
        """转换引用"""
        text = self._rich_text_to_markdown(block['quote']['rich_text'])
        lines = text.split('\\n')
        return '\\n'.join(f"> {line}" for line in lines)

    def _convert_image(self, block: Dict[str, Any]) -> str:
        """转换图片"""
        image_info = block['image']

        if image_info['type'] == 'external':
            url = image_info['external']['url']
        else:
            url = image_info['file']['url']

        # 下载图片
        local_path = self.media_handler.download_media(url, "image")

        # 获取标题
        caption = ""
        if image_info.get('caption'):
            caption = self._rich_text_to_plain_text(image_info['caption'])

        return f"![{caption}]({local_path})"

    def _convert_video(self, block: Dict[str, Any]) -> str:
        """转换视频"""
        video_info = block['video']

        if video_info['type'] == 'external':
            url = video_info['external']['url']
            # 处理YouTube/Vimeo等外部视频
            if 'youtube.com' in url or 'youtu.be' in url:
                video_id = self._extract_youtube_id(url)
                return f'{{{{< youtube "{video_id}" >}}}}'
            elif 'vimeo.com' in url:
                video_id = url.split('/')[-1]
                return f'{{{{< vimeo "{video_id}" >}}}}'
            else:
                return f'<video src="{url}" controls></video>'
        else:
            # 下载视频文件
            url = video_info['file']['url']
            local_path = self.media_handler.download_media(url, "video")
            return f'<video src="{local_path}" controls></video>'

    def _convert_audio(self, block: Dict[str, Any]) -> str:
        """转换音频"""
        audio_info = block['audio']

        if audio_info['type'] == 'external':
            url = audio_info['external']['url']
        else:
            url = audio_info['file']['url']
            # 下载音频文件
            local_path = self.media_handler.download_media(url, "audio")
            url = local_path

        return f'<audio src="{url}" controls></audio>'

    def _convert_equation(self, block: Dict[str, Any]) -> str:
        """转换数学公式"""
        expression = block['equation']['expression']
        # 使用 $$ 包裹块级公式
        return f"$$\\n{expression}\\n$$"

    def _convert_toggle(self, block: Dict[str, Any]) -> str:
        """转换折叠块"""
        toggle_text = self._rich_text_to_markdown(block['toggle']['rich_text'])
        # Hugo 不直接支持折叠，使用 details 标签
        return f"<details>\\n<summary>{toggle_text}</summary>\\n\\n<!-- 折叠内容 -->\\n</details>"

    def _convert_callout(self, block: Dict[str, Any]) -> str:
        """转换提示框"""
        callout = block['callout']
        icon = callout.get('icon', {}).get('emoji', '💡')
        text = self._rich_text_to_markdown(callout['rich_text'])

        # 使用 Hugo shortcode 或自定义样式
        return f"> {icon} **提示**\\n> \\n> {text}"

    def _rich_text_to_markdown(self, rich_texts: List[Dict[str, Any]]) -> str:
        """将富文本转换为 Markdown"""
        if not rich_texts:
            return ""

        result = []
        for rt in rich_texts:
            text = rt['plain_text']
            annotations = rt.get('annotations', {})

            # 处理格式
            if annotations.get('bold'):
                text = f"**{text}**"
            if annotations.get('italic'):
                text = f"*{text}*"
            if annotations.get('code'):
                text = f"`{text}`"
            if annotations.get('strikethrough'):
                text = f"~~{text}~~"
            if annotations.get('underline'):
                text = f"<u>{text}</u>"

            # 处理链接
            if rt.get('href'):
                text = f"[{text}]({rt['href']})"

            # 处理颜色
            color = annotations.get('color', 'default')
            if color != 'default':
                text = f'<span style="color: {color}">{text}</span>'

            result.append(text)

        return ''.join(result)

    def _rich_text_to_plain_text(self, rich_texts: List[Dict[str, Any]]) -> str:
        """提取纯文本"""
        return ''.join(rt['plain_text'] for rt in rich_texts)

    def _has_math(self, blocks: List[Dict[str, Any]]) -> bool:
        """检查是否包含数学公式"""
        for block in blocks:
            if block['type'] == 'equation':
                return True
            # 检查行内公式
            if block['type'] in ['paragraph', 'bulleted_list_item', 'numbered_list_item']:
                text_content = self._rich_text_to_plain_text(
                    block.get(block['type'], {}).get('rich_text', [])
                )
                if '$' in text_content or '\\\\(' in text_content or '\\\\[' in text_content:
                    return True
        return False

    def _extract_youtube_id(self, url: str) -> str:
        """提取 YouTube 视频 ID"""
        patterns = [
            r'(?:youtube\\.com\\/watch\\?v=|youtu\\.be\\/)([^&\\n?#]+)',
            r'youtube\\.com\\/embed\\/([^&\\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return ""

    def clean_posts_directory(self):
        """清理文章目录"""
        try:
            for filename in os.listdir(self.posts_dir):
                if filename.endswith('.md'):
                    os.remove(os.path.join(self.posts_dir, filename))
            logger.info("Cleaned posts directory")
        except Exception as e:
            logger.error(f"Error cleaning posts directory: {e}")

    def _convert_embed(self, block: Dict[str, Any]) -> str:
        """转换嵌入内容"""
        embed_info = block['embed']
        url = embed_info['url']

        # Twitter/X 嵌入
        if 'twitter.com' in url or 'x.com' in url:
            tweet_id = url.split('/')[-1].split('?')[0]
            return f'{{{{< tweet user="username" id="{tweet_id}" >}}}}'

        # GitHub Gist
        elif 'gist.github.com' in url:
            return f'{{{{< gist url="{url}" >}}}}'

        # CodePen
        elif 'codepen.io' in url:
            return f'<iframe src="{url}" style="width:100%; height:400px;"></iframe>'

        # 通用 iframe
        else:
            return f'<iframe src="{url}" style="width:100%; height:400px;"></iframe>'

    def _convert_pdf(self, block: Dict[str, Any]) -> str:
        """转换 PDF"""
        pdf_info = block['pdf']

        if pdf_info['type'] == 'external':
            url = pdf_info['external']['url']
        else:
            url = pdf_info['file']['url']
            # 下载 PDF
            local_path = self.media_handler.download_media(url, "pdf")
            url = local_path

        return f'<iframe src="{url}" width="100%" height="600px"></iframe>'

    def _convert_table(self, block: Dict[str, Any]) -> str:
        """转换表格"""
        table = block['table']
        has_header = table.get('has_column_header', False)

        rows = []
        for i, row in enumerate(block.get('children', [])):
            cells = []
            for cell in row.get('table_row', {}).get('cells', []):
                cell_text = self._rich_text_to_markdown(cell)
                cells.append(cell_text)
            rows.append(cells)

        if not rows:
            return ""

        # 生成 Markdown 表格
        markdown = []

        # 表头
        if has_header and rows:
            markdown.append('| ' + ' | '.join(rows[0]) + ' |')
            markdown.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')
            rows = rows[1:]

        # 表格内容
        for row in rows:
            markdown.append('| ' + ' | '.join(row) + ' |')

        return '\\n'.join(markdown)
