# Notion-Hugo Blog Sync

A powerful automation tool that syncs your Notion database to a Hugo static site and deploys it to Cloudflare Pages. Write in Notion, publish everywhere.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Hugo](https://img.shields.io/badge/hugo-0.110+-ff4088.svg)](https://gohugo.io/)
[![Notion API](https://img.shields.io/badge/Notion%20API-v2.2.0-black)](https://developers.notion.com/)

## ✨ Features

- 📝 **Full Notion Support**: Paragraphs, headings, lists, code blocks, quotes, toggles, callouts, and more
- 🖼️ **Rich Media Handling**: Automatically downloads and optimizes images, videos, and audio files
- 🔢 **Math Support**: Renders LaTeX equations using KaTeX/MathJax
- 🎥 **Embed Support**: YouTube, Vimeo, Twitter/X, GitHub Gists, and more
- ⚡ **Smart Caching**: Only updates changed content, avoiding redundant downloads
- 🔄 **Automated Deployment**: GitHub Actions workflow for continuous deployment
- 🌐 **Cloudflare Pages**: Fast, global CDN deployment
- 🎨 **Hugo Flexibility**: Compatible with any Hugo theme
- 🚀 **Performance Optimized**: Concurrent downloads, image optimization, and progress tracking

## 📋 Prerequisites

- Python 3.8 or higher
- Hugo (extended version recommended)
- A Notion account with an integration token
- A Cloudflare account (for deployment)
- A GitHub repository

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/trainsh/notion-hugo-blog.git
cd notion-hugo-blog
```

### 2. Set Up Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the Internal Integration Token
4. Create a Notion database with these properties:
   - **Title** (Title): Post title
   - **Slug** (Text): URL-friendly post identifier
   - **Date** (Date): Publication date
   - **Tags** (Multi-select): Post categories
   - **Published** (Checkbox): Whether to publish the post
5. Share the database with your integration

### 3. Install Dependencies

```bash
uv venv --python 3.10
uv pip install -r scripts/requirements.txt
```

### 4. Configure Environment

Create a `.env` file:

```bash
# Notion Configuration
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id

# Hugo Configuration
HUGO_CONTENT_DIR=./content
HUGO_STATIC_DIR=./static

# Optional Settings
MAX_CONCURRENT_DOWNLOADS=5
OPTIMIZE_IMAGES=true
MAX_IMAGE_WIDTH=1920
```

### 5. Run Locally

```bash
# Sync content from Notion
python scripts/notion_sync.py --clean

# Start Hugo development server
hugo server -D
```

## 🔧 Configuration

### Hugo Configuration

Edit `config.toml` to customize your site:

```toml
baseURL = "https://your-blog.pages.dev/"
languageCode = "en-us"
title = "My Blog"
theme = "ananke"

[params]
  math = true  # Enable math support
  description = "My personal blog powered by Notion"

[markup]
  [markup.goldmark]
    [markup.goldmark.renderer]
      unsafe = true  # Allow raw HTML for embeds
```

### Math Support

Add KaTeX support to your theme by including in `layouts/partials/math.html`:

```html
{{ if .Params.math }}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
{{ end }}
```

## 🚢 Deployment

### GitHub Actions Setup

1. Add secrets to your GitHub repository:
   - `NOTION_TOKEN`: Your Notion integration token
   - `NOTION_DATABASE_ID`: Your Notion database ID
   - `CLOUDFLARE_API_TOKEN`: Your Cloudflare API token
   - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare account ID

2. The workflow runs automatically on:
   - Push to main branch
   - Every 6 hours (configurable)
   - Manual trigger

### Cloudflare Pages Setup

1. Create a new Pages project in Cloudflare Dashboard
2. Choose "Direct Upload" deployment method
3. Note the project name for GitHub Actions configuration

## 🐳 Docker Support

Run the entire stack in Docker:

```bash
# Build and run
docker-compose up

# Or use the Docker image directly
docker build -t notion-hugo-sync .
docker run -e NOTION_TOKEN=your_token -e NOTION_DATABASE_ID=your_id notion-hugo-sync
```

## 📁 Project Structure

```
notion-hugo-blog/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── scripts/
│   ├── notion_sync.py          # Main sync script
│   ├── notion_client.py        # Notion API client
│   ├── hugo_converter.py       # Notion to Hugo converter
│   ├── media_handler.py        # Media download handler
│   └── requirements.txt        # Python dependencies
├── content/
│   └── posts/                  # Generated blog posts
├── static/
│   ├── images/                 # Downloaded images
│   ├── videos/                 # Downloaded videos
│   └── audio/                  # Downloaded audio files
├── themes/                     # Hugo themes
├── config.toml                 # Hugo configuration
├── Dockerfile                  # Docker configuration
└── docker-compose.yml          # Docker Compose configuration
```

## 🛠️ Advanced Usage

### Custom Block Types

Extend `hugo_converter.py` to support custom Notion blocks:

```python
def _convert_custom_block(self, block: Dict[str, Any]) -> str:
    # Your custom conversion logic
    return markdown_output
```

### Media Processing

Customize image optimization in `media_handler.py`:

```python
def _optimize_image(self, file_path: str, max_width: int = 1920):
    # Custom image processing logic
    pass
```

### Caching Strategy

The tool includes intelligent caching to:
- Skip unchanged posts
- Reuse downloaded media files
- Store sync metadata

## 🐛 Troubleshooting

### Common Issues

1. **Math formulas not rendering**
   - Ensure your Hugo theme supports KaTeX/MathJax
   - Check that `math: true` is set in the post's front matter

2. **Media download failures**
   - Check your internet connection
   - Verify Notion media URLs are accessible
   - Increase retry attempts in configuration

3. **Notion API rate limits**
   - The tool includes rate limiting
   - Reduce sync frequency if needed

4. **Large media files**
   - Consider using external hosting for very large files
   - Adjust `MAX_CONCURRENT_DOWNLOADS` for better performance

### Debug Mode

Run with verbose logging:

```bash
python scripts/notion_sync.py --log-level DEBUG
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Copyright 2025 Binbin Shen

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## 🙏 Acknowledgments

- [Hugo](https://gohugo.io/) - The world's fastest framework for building websites
- [Notion API](https://developers.notion.com/) - Official Notion API
- [Cloudflare Pages](https://pages.cloudflare.com/) - Fast, secure hosting
- [KaTeX](https://katex.org/) - Fast math typesetting library

## 📮 Support

- Create an [Issue](https://github.com/trainsh/notion-hugo-blog/issues) for bug reports
- Start a [Discussion](https://github.com/trainsh/notion-hugo-blog/discussions) for questions

---

Made with ❤️ by [Binbin Shen](https://github.com/trainsh)
