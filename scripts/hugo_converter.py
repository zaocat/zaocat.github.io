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
        self.id_to_slug = {}

    def set_id_to_slug_mapping(self, mapping: Dict[str, str]):
        self.id_to_slug = mapping or {}

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

            # Enable Mermaid when needed
            if self._has_mermaid(post.blocks):
                front_matter['mermaid'] = True

            # Add cover image
            if post.cover_image:
                local_cover = self.media_handler.download_media(post.cover_image, "image")
                if local_cover:
                    front_matter['cover'] = {
                        'image': local_cover,
                        'alt': post.title
                    }

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

        rich_text = paragraph.get('rich_text', [])
        text = self._rich_text_to_markdown(rich_text)
        return text if text else ""

    def _convert_heading(self, block: Dict[str, Any]) -> str:
        """Convert heading"""
        level = block['type'].split('_')[1]
        heading_data = block.get(block['type'], {})
        if not heading_data:
            return ""

        text = self._rich_text_to_markdown(heading_data.get('rich_text', []))

        # Use Notion block id as a stable anchor so intra-post links work reliably.
        # Normalize to compact lowercase hex without dashes to match Notion-style fragments.
        block_id = (block.get('id') or '').replace('-', '').lower()
        if block_id:
            return f"{'#' * int(level)} {text} {{#{block_id}}}"
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
                    # Indent child items by 4 spaces so Goldmark treats them as part of the same list item.
                    # This preserves ordered list numbering and keeps nested bullets/numbered lists.
                    indented = '\n'.join(f"    {line}" for line in child_text.split('\n'))
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

        # Detect Mermaid even if language wasn't set explicitly in Notion
        mermaid_like = ('graph TD' in code_text) or ('flowchart' in code_text) or ('sequenceDiagram' in code_text)
        if not language and mermaid_like:
            language = 'mermaid'

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
                return f'<video controls style="width: 100%; max-width: 800px;">\n  <source src="{url}">\n</video>'
        else:
            # Download video file
            url = video_info.get('file', {}).get('url', '')
            if url:
                local_path = self.media_handler.download_media(url, "video")
                return f'<video controls style="width: 100%; max-width: 800px;">\n  <source src="{local_path}">\n</video>'

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
            return f'<audio controls preload="none" style="width: 100%;">\n  <source src="{url}">\n</audio>'
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
        formatted_lines = [f"> {icon} "]
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

        # Always return as HTML anchor so we can control target
        link_text = caption or url
        return f"- <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">{self._escape_html(link_text)}</a>"

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

        # Collect all content in columns
        all_content = []
        image_count = 0

        for column in children:
            if column.get('type') == 'column':
                column_children = column.get('children', [])

                # Check if this column only contains images
                column_has_only_images = all(
                    child.get('type') == 'image'
                    for child in column_children
                )

                if column_has_only_images and column_children:
                    # If column only contains images, handle each image separately
                    for child in column_children:
                        image_info = child.get('image', {})
                        if not image_info:
                            continue
                        # Resolve URL
                        if image_info.get('type') == 'external':
                            url = image_info.get('external', {}).get('url', '')
                        else:
                            url = image_info.get('file', {}).get('url', '')
                        if not url:
                            continue
                        # Download and build HTML directly so Markdown is not nested inside HTML
                        local_path = self.media_handler.download_media(url, "image")
                        caption = ""
                        if image_info.get('caption'):
                            caption = self._rich_text_to_plain_text(image_info['caption'])
                        figcaption = f"<figcaption>{caption}</figcaption>" if caption else ""
                        html = (
                            f"<figure style=\"margin:0;\">\n"
                            f"  <img src=\"{local_path}\" alt=\"{caption}\" style=\"width:100%;height:auto;\">\n"
                            f"  {figcaption}\n"
                            f"</figure>"
                        )
                        all_content.append(html)
                        image_count += 1
                else:
                    # Otherwise, handle column content normally
                    column_content = self._blocks_to_markdown(column_children)
                    if column_content:
                        all_content.append(f'<div style="flex: 1;">\\n\\n{column_content}\\n\\n</div>')

        # If all columns are images, use image grid layout
        if image_count == len(all_content):
            return f'''<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
    {chr(10).join(all_content)}
    </div>'''

        # Otherwise, use normal flex layout
        return f'''<div style="display: flex; gap: 20px; flex-wrap: wrap;">
    {chr(10).join(all_content)}
    </div>'''

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

        # Check if in column layout (simplified by checking parent context)
        # If in grid layout, no extra styles needed
        return f"![{caption}]({local_path})"

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
            return f"- <a href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">{self._escape_html(url)}</a>"
        return ""

    def _convert_child_page(self, block: Dict[str, Any]) -> str:
        """Convert child page reference"""
        child_page = block.get('child_page', {})
        title = child_page.get('title', 'Child Page')
        # Avoid verbose placeholders; omit unless we can link to a local page.
        return ""

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
            href = rt.get('href')

            # Rewrite Notion links to local Hugo slugs if possible
            if href:
                local_href = self._rewrite_notion_link(href)
            else:
                local_href = None

            # Build formatting using HTML to avoid conflicts when wrapped inside HTML spans
            # and to ensure consistent rendering by Goldmark.
            if annotations.get('code'):
                text = f"<code>{self._escape_html(text)}</code>"
            else:
                if annotations.get('bold'):
                    text = f"<strong>{text}</strong>"
                if annotations.get('italic'):
                    text = f"<em>{text}</em>"
                if annotations.get('strikethrough'):
                    text = f"<del>{text}</del>"
                if annotations.get('underline'):
                    text = f"<u>{text}</u>"

            color = annotations.get('color', 'default')
            if color != 'default':
                text = f'<span style="color: {color}">{text}</span>'

            if local_href:
                is_external = (
                    local_href.startswith('http://') or
                    local_href.startswith('https://') or
                    local_href.startswith('//')
                )
                if is_external and not local_href.startswith('/') and not local_href.startswith('#'):
                    text = f"<a href=\"{local_href}\" target=\"_blank\" rel=\"noopener noreferrer\">{text}</a>"
                else:
                    text = f"<a href=\"{local_href}\">{text}</a>"

            result.append(text)

        return ''.join(result)

    def _rich_text_to_plain_text(self, rich_texts: List[Dict[str, Any]]) -> str:
        """Extract plain text"""
        if not rich_texts:
            return ""

        return ''.join(rt.get('plain_text', '') for rt in rich_texts)

    def _escape_html(self, s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
        )

    def _rewrite_notion_link(self, url: str) -> str:
        """Rewrite Notion page links to local Hugo permalinks when possible.
        Supports URLs like https://www.notion.so/...-<id> or notion://... and raw IDs.
        """
        try:
            # Preserve URL fragment (e.g., #<block-id>) so anchor jumps still work
            from urllib.parse import urlparse
            parsed = urlparse(url)
            fragment = (parsed.fragment or '').strip()

            # If it's a pure same-page anchor, normalize Notion block id fragments
            if (url.startswith('#') or (not parsed.scheme and not parsed.netloc and not parsed.path)) and fragment:
                if re.fullmatch(r"[0-9a-fA-F\-]{36}", fragment) or re.fullmatch(r"[0-9a-fA-F]{32}", fragment):
                    return f"#{fragment.replace('-', '').lower()}"
                return f"#{fragment}"
            # compact id pattern (32 hex) or hyphenated uuid
            import re
            patterns = [
                r"([0-9a-f]{32})$",
                r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
                r"([0-9a-f]{32})(?:\?.*)?$",
            ]
            matched_id = None
            # Remove fragment for page id detection
            url_wo_fragment = url.split('#', 1)[0]
            for pat in patterns:
                m = re.search(pat, url_wo_fragment, re.IGNORECASE)
                if m:
                    matched_id = m.group(1)
                    break

            if matched_id and self.id_to_slug:
                slug = self.id_to_slug.get(matched_id) or self.id_to_slug.get(matched_id.replace('-', ''))
                if slug:
                    # Append fragment if provided; normalize Notion-style uuids to compact lowercase
                    if fragment:
                        if re.fullmatch(r"[0-9a-fA-F\-]{36}", fragment) or re.fullmatch(r"[0-9a-fA-F]{32}", fragment):
                            norm_fragment = fragment.replace('-', '').lower()
                            return f"/posts/{slug}/#{norm_fragment}"
                        return f"/posts/{slug}/#{fragment}"
                    return f"/posts/{slug}/"
        except Exception:
            pass
        return url

    def _has_mermaid(self, blocks: List[Dict[str, Any]]) -> bool:
        """Detect if content contains Mermaid diagrams"""
        for block in blocks:
            block_type = block.get('type', '')
            if block_type == 'code':
                code_info = block.get('code', {})
                language = code_info.get('language', '').lower()
                if language == 'mermaid':
                    return True
                text = self._rich_text_to_plain_text(code_info.get('rich_text', []))
                if 'graph TD' in text or 'flowchart' in text or 'sequenceDiagram' in text:
                    return True
            # Search children as well
            if block.get('children'):
                if self._has_mermaid(block['children']):
                    return True
        return False

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
