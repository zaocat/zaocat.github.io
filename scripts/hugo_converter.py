import os
import re
import yaml
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class HugoConverter:
    def __init__(self, content_dir: str, media_handler):
        self.content_dir = content_dir
        self.media_handler = media_handler
        self.posts_dir = os.path.join(content_dir, "posts")
        os.makedirs(self.posts_dir, exist_ok=True)

    def convert_post(self, post) -> bool:
        """Convert a Notion post into Hugo format"""
        try:
            # Convert content
            content = self._blocks_to_markdown(post.blocks)

            # Create front matter
            front_matter = {
                'title': post.title,
                'date': post.date.isoformat(),
                'lastmod': post.last_edited.isoformat(),
                'slug': post.slug,
                'tags': post.tags,
                'draft': False,
                'math': self._has_math(post.blocks),  # Check if it contains math formulas
            }

            # Add cover image
            if post.cover_image:
                local_cover = self.media_handler.download_media(post.cover_image, "image")
                if local_cover:
                    front_matter['cover'] = local_cover

            # Generate full Markdown file
            file_content = "---\n"
            file_content += yaml.dump(front_matter, allow_unicode=True, default_flow_style=False)
            file_content += "---\n\n"
            file_content += content

            # Save file
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
        """Convert Notion blocks to Markdown"""
        markdown_parts = []

        for block in blocks:
            block_type = block.get('type', '')
            markdown = self._convert_block(block)
            if markdown:
                markdown_parts.append(markdown)

        return '\n\n'.join(markdown_parts)

    def _convert_block(self, block: Dict[str, Any]) -> str:
        """Convert a single block"""
        block_type = block.get('type', '')

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
            elif block_type == 'bookmark':
                return self._convert_bookmark(block)
            elif block_type == 'embed':
                return self._convert_embed(block)
            elif block_type == 'table':
                return self._convert_table(block)
            elif block_type == 'column_list':
                return self._convert_column_list(block)
            elif block_type == 'link_preview':
                return self._convert_link_preview(block)
            elif block_type == 'child_page':
                return self._convert_child_page(block)
            elif block_type == 'pdf':
                return self._convert_pdf(block)
            elif block_type == 'file':
                return self._convert_file(block)
            elif block_type == 'table_of_contents':
                return "{{< toc >}}"
            elif block_type == 'column':
                # Column blocks are handled by column_list
                return ""
            elif block_type == 'synced_block':
                return "<!-- Synced block -->"
            elif block_type == 'unsupported':
                return "<!-- Unsupported block type -->"
            else:
                logger.warning(f"Unsupported block type: {block_type}")
                return ""
        except Exception as e:
            logger.error(f"Error converting block type {block_type}: {e}")
            return ""

    def _convert_paragraph(self, block: Dict[str, Any]) -> str:
        """Convert paragraph"""
        paragraph = block.get('paragraph', {})
        if not paragraph:
            return ""

        text = self._rich_text_to_markdown(paragraph.get('rich_text', []))
        return text if text else ""

    def _convert_heading(self, block: Dict[str, Any]) -> str:
        """Convert heading"""
        level = block['type'].split('_')[1]
        heading_data = block.get(block['type'], {})
        if not heading_data:
            return ""

        text = self._rich_text_to_markdown(heading_data.get('rich_text', []))
        return f"{'#' * int(level)} {text}"

    def _convert_list_item(self, block: Dict[str, Any], prefix: str) -> str:
        """Convert list item"""
        list_item = block.get(block['type'], {})
        if not list_item:
            return ""

        text = self._rich_text_to_markdown(list_item.get('rich_text', []))

        # Handle child items
        children = block.get('children', [])
        if children:
            child_content = []
            for child in children:
                child_text = self._convert_block(child)
                if child_text:
                    # Indent child items
                    indented = '\n'.join(f"  {line}" for line in child_text.split('\n'))
                    child_content.append(indented)

            if child_content:
                text += '\n' + '\n'.join(child_content)

        return f"{prefix}{text}"

    def _convert_code(self, block: Dict[str, Any]) -> str:
        """Convert code block"""
        code_info = block.get('code', {})
        if not code_info:
            return ""

        language = code_info.get('language', '').lower()
        code_text = self._rich_text_to_plain_text(code_info.get('rich_text', []))
        return f"```{language}\n{code_text}\n```"

    def _convert_quote(self, block: Dict[str, Any]) -> str:
        """Convert quote"""
        quote = block.get('quote', {})
        if not quote:
            return ""

        text = self._rich_text_to_markdown(quote.get('rich_text', []))
        lines = text.split('\n')
        return '\n'.join(f"> {line}" for line in lines)

    def _convert_image(self, block: Dict[str, Any]) -> str:
        """Convert image"""
        image_info = block.get('image', {})
        if not image_info:
            return ""

        if image_info.get('type') == 'external':
            url = image_info.get('external', {}).get('url', '')
        else:
            url = image_info.get('file', {}).get('url', '')

        if not url:
            return ""

        # Download image
        local_path = self.media_handler.download_media(url, "image")

        # Get caption
        caption = ""
        if image_info.get('caption'):
            caption = self._rich_text_to_plain_text(image_info['caption'])

        return f"![{caption}]({local_path})"

    def _convert_video(self, block: Dict[str, Any]) -> str:
        """Convert video"""
        video_info = block.get('video', {})
        if not video_info:
            return ""

        if video_info.get('type') == 'external':
            url = video_info.get('external', {}).get('url', '')
            # Handle external video providers like YouTube/Vimeo
            if 'youtube.com' in url or 'youtu.be' in url:
                video_id = self._extract_youtube_id(url)
                if video_id:
                    return f'{{{{< youtube "{video_id}" >}}}}'
            elif 'vimeo.com' in url:
                video_id = url.split('/')[-1]
                return f'{{{{< vimeo "{video_id}" >}}}}'
            else:
                return f'<video src="{url}" controls></video>'
        else:
            # Download video file
            url = video_info.get('file', {}).get('url', '')
            if url:
                local_path = self.media_handler.download_media(url, "video")
                return f'<video src="{local_path}" controls></video>'

        return ""

    def _convert_audio(self, block: Dict[str, Any]) -> str:
        """Convert audio"""
        audio_info = block.get('audio', {})
        if not audio_info:
            return ""

        if audio_info.get('type') == 'external':
            url = audio_info.get('external', {}).get('url', '')
        else:
            url = audio_info.get('file', {}).get('url', '')
            if url:
                # Download audio file
                local_path = self.media_handler.download_media(url, "audio")
                url = local_path

        if url:
            return f'<audio src="{url}" controls></audio>'
        return ""

    def _convert_equation(self, block: Dict[str, Any]) -> str:
        """Convert mathematical equation"""
        equation = block.get('equation', {})
        expression = equation.get('expression', '')
        if expression:
            # Use $$ to wrap block-level formulas
            return f"$$\n{expression}\n$$"
        return ""

    def _convert_toggle(self, block: Dict[str, Any]) -> str:
        """Convert toggle block"""
        toggle = block.get('toggle', {})
        if not toggle:
            return ""

        toggle_text = self._rich_text_to_markdown(toggle.get('rich_text', []))

        # Get child content
        children = block.get('children', [])
        content = ""
        if children:
            content = self._blocks_to_markdown(children)

        # Hugo doesn't directly support toggle, use details tag
        return f"<details>\n<summary>{toggle_text}</summary>\n\n{content}\n</details>"

    def _convert_callout(self, block: Dict[str, Any]) -> str:
        """Convert callout block"""
        callout = block.get('callout')
        if not callout:
            return ""

        # Safely get icon
        icon = '💡'
        icon_obj = callout.get('icon')
        if icon_obj and isinstance(icon_obj, dict):
            if icon_obj.get('type') == 'emoji':
                icon = icon_obj.get('emoji', '💡')

        text = self._rich_text_to_markdown(callout.get('rich_text', []))

        # Get child content
        children = block.get('children', [])
        if children:
            child_content = self._blocks_to_markdown(children)
            if child_content:
                text += '\n\n' + child_content

        # Use blockquote style
        lines = text.split('\n')
        formatted_lines = [f"> {icon} **Note**"]
        formatted_lines.extend(f"> {line}" for line in lines)

        return '\n'.join(formatted_lines)

    def _convert_bookmark(self, block: Dict[str, Any]) -> str:
        """Convert bookmark"""
        bookmark = block.get('bookmark', {})
        if not bookmark:
            return ""

        url = bookmark.get('url', '')
        if not url:
            return ""

        # Get title
        caption = ""
        if bookmark.get('caption'):
            caption = self._rich_text_to_plain_text(bookmark['caption'])

        # Return bookmark format
        if caption:
            return f"🔖 [{caption}]({url})"
        else:
            return f"🔖 <{url}>"

    def _convert_table(self, block: Dict[str, Any]) -> str:
        """Convert table"""
        table = block.get('table', {})
        if not table:
            return ""

        has_header = table.get('has_column_header', False)

        # Get table rows
        rows = []
        children = block.get('children', [])

        for child in children:
            if child.get('type') == 'table_row':
                row_data = child.get('table_row', {})
                cells = row_data.get('cells', [])
                row = []
                for cell in cells:
                    cell_text = self._rich_text_to_markdown(cell)
                    row.append(cell_text)
                rows.append(row)

        if not rows:
            return ""

        # Generate Markdown table
        markdown_lines = []

        if has_header and rows:
            # Table header
            markdown_lines.append('| ' + ' | '.join(rows[0]) + ' |')
            markdown_lines.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')
            rows = rows[1:]
        else:
            # If no header, add empty header
            if rows:
                markdown_lines.append('| ' + ' | '.join([''] * len(rows[0])) + ' |')
                markdown_lines.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')

        # Table content
        for row in rows:
            markdown_lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(markdown_lines)

    def _convert_column_list(self, block: Dict[str, Any]) -> str:
        """Convert column layout"""
        children = block.get('children', [])
        if not children:
            return ""

        # Use HTML div to simulate column layout
        content_parts = ['<div style="display: flex; gap: 20px;">']

        for child in children:
            if child.get('type') == 'column':
                column_children = child.get('children', [])
                column_content = self._blocks_to_markdown(column_children)
                content_parts.append(f'<div style="flex: 1;">\n\n{column_content}\n\n</div>')

        content_parts.append('</div>')

        return '\n'.join(content_parts)

    def _convert_embed(self, block: Dict[str, Any]) -> str:
        """Convert embedded content"""
        embed_info = block.get('embed', {})
        url = embed_info.get('url', '')

        if not url:
            return ""

        # Twitter/X embed
        if 'twitter.com' in url or 'x.com' in url:
            # Extract tweet ID
            match = re.search(r'/status/(\\d+)', url)
            if match:
                tweet_id = match.group(1)
                return f'{{{{< tweet user="user" id="{tweet_id}" >}}}}'

        # YouTube
        elif 'youtube.com' in url or 'youtu.be' in url:
            video_id = self._extract_youtube_id(url)
            if video_id:
                return f'{{{{< youtube "{video_id}" >}}}}'

        # GitHub Gist
        elif 'gist.github.com' in url:
            return f'{{{{< gist url="{url}" >}}}}'

        # CodePen
        elif 'codepen.io' in url:
            return f'<iframe src="{url}" style="width:100%; height:400px;"></iframe>'

        # Generic iframe
        else:
            return f'<iframe src="{url}" style="width:100%; height:400px;"></iframe>'

    def _convert_link_preview(self, block: Dict[str, Any]) -> str:
        """Convert link preview"""
        link_preview = block.get('link_preview', {})
        url = link_preview.get('url', '')

        if url:
            return f"🔗 <{url}>"
        return ""

    def _convert_child_page(self, block: Dict[str, Any]) -> str:
        """Convert child page reference"""
        child_page = block.get('child_page', {})
        title = child_page.get('title', 'Child Page')

        return f"📄 **{title}** *(child page)*"

    def _convert_pdf(self, block: Dict[str, Any]) -> str:
        """Convert PDF"""
        pdf_info = block.get('pdf', {})
        if not pdf_info:
            return ""

        if pdf_info.get('type') == 'external':
            url = pdf_info.get('external', {}).get('url', '')
        else:
            url = pdf_info.get('file', {}).get('url', '')

        if not url:
            return ""

        # Get title
        caption = ""
        if pdf_info.get('caption'):
            caption = self._rich_text_to_plain_text(pdf_info['caption'])

        title = caption or "PDF Document"

        return f'📄 [{title}]({url})'

    def _convert_file(self, block: Dict[str, Any]) -> str:
        """Convert file"""
        file_info = block.get('file', {})
        if not file_info:
            return ""

        if file_info.get('type') == 'external':
            url = file_info.get('external', {}).get('url', '')
        else:
            url = file_info.get('file', {}).get('url', '')

        if not url:
            return ""

        # Get filename
        caption = ""
        if file_info.get('caption'):
            caption = self._rich_text_to_plain_text(file_info['caption'])

        filename = caption or url.split('/')[-1]

        return f'📎 [{filename}]({url})'

    def _rich_text_to_markdown(self, rich_texts: List[Dict[str, Any]]) -> str:
        """Convert rich text to Markdown"""
        if not rich_texts:
            return ""

        result = []

        for rt in rich_texts:
            text = rt.get('plain_text', '')
            annotations = rt.get('annotations', {})

            # Handle links
            if rt.get('href'):
                text = f"[{text}]({rt['href']})"

            # Handle formatting
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

            # Handle colors
            color = annotations.get('color', 'default')
            if color != 'default':
                text = f'<span style="color: {color}">{text}</span>'

            result.append(text)

        return ''.join(result)

    def _rich_text_to_plain_text(self, rich_texts: List[Dict[str, Any]]) -> str:
        """Extract plain text"""
        if not rich_texts:
            return ""

        return ''.join(rt.get('plain_text', '') for rt in rich_texts)

    def _has_math(self, blocks: List[Dict[str, Any]]) -> bool:
        """Check if contains mathematical formulas"""
        for block in blocks:
            if block.get('type') == 'equation':
                return True

            # Check inline formulas
            block_type = block.get('type', '')
            if block_type in ['paragraph', 'bulleted_list_item', 'numbered_list_item']:
                block_data = block.get(block_type, {})
                text_content = self._rich_text_to_plain_text(
                    block_data.get('rich_text', [])
                )
                if '$' in text_content or '\\\\(' in text_content or '\\\\[' in text_content:
                    return True

        return False

    def _extract_youtube_id(self, url: str) -> str:
        """Extract YouTube video ID"""
        patterns = [
            r'(?:youtube\\.com\\/watch\\?v=|youtu\\.be\\/)([^&\n?#]+)',
            r'youtube\\.com\\/embed\\/([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return ""

    def clean_posts_directory(self):
        """Clean posts directory"""
        try:
            import shutil
            if os.path.exists(self.posts_dir):
                shutil.rmtree(self.posts_dir)
            os.makedirs(self.posts_dir, exist_ok=True)
            logger.info("Cleaned posts directory")
        except Exception as e:
            logger.error(f"Error cleaning posts directory: {e}")
