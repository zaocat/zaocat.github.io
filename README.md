# Notion-Hugo Blog Sync

Sync your Notion database to a Hugo static site. Write in Notion, publish with Hugo.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Hugo](https://img.shields.io/badge/hugo-0.148.0%2B-ff4088.svg)](https://gohugo.io/)
[![Notion API](https://img.shields.io/badge/Notion%20API-v2.4.0-black)](https://developers.notion.com/)

## ✨ Features

- **Full Notion support**: Paragraphs, headings, lists, code blocks, quotes, toggles, callouts
- **Rich media handling**: Downloads and optimizes images, videos, audio
- **Math support**: KaTeX/MathJax via `layouts/partials/math.html`
- **Smart caching**: Updates only changed content
- **Hugo flexibility**: Works with any theme (e.g., PaperMod)
- **Performance**: Concurrent downloads, progress tracking

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Hugo**: Extended version recommended
- **Notion**: Integration token and a database

## 🚀 Quick Start

### 1) Clone

```bash
git clone https://github.com/trainsh/notion-hugo-blog.git
cd notion-hugo-blog
```

### 2) One-time setup (recommended)

```bash
./setup.sh
```

This will:
- Create `.env` from `.env.example` if present (otherwise create it manually)
- Create required directories (`content/`, `static/`, `themes/`)
- Create a virtualenv and install dependencies from root `requirements.txt`

### 3) Notion integration

1. Go to `https://www.notion.so/my-integrations`
2. Create an integration and copy the Internal Integration Token
3. Create a Notion database with properties:
   - **Title** (Title)
   - **Slug** (Text)
   - **Date** (Date)
   - **Tags** (Multi-select)
   - **Published** (Checkbox)
4. Share the database with your integration

### 4) Environment variables

Create `.env` in the project root with:

```bash
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id
```

### 5) Install dependencies (if you didn’t run setup.sh)

```bash
uv venv --python 3.10
uv pip install -r requirements.txt
```

### 6) Run locally

```bash
# Sync content from Notion (clears existing posts first)
python scripts/notion_sync.py --clean

# Start Hugo dev server
hugo server -D
```

## 🔧 Configuration

### Hugo config

Adjust `config.toml`:

```toml
baseURL = "https://your-blog.example/"
languageCode = "en-us"
title = "My Blog"
theme = "PaperMod"

[params]
  math = true
  description = "My personal blog powered by Notion"

[markup]
  [markup.highlight]
    style = 'monokai'
  [markup.goldmark.renderer]
    unsafe = true
```

### Math support

This repo provides `layouts/partials/math.html`. Ensure your theme includes it (e.g., from `baseof.html`).

Minimal include if you need to add it to a theme:

```html
{{ if .Params.math }}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
{{ end }}
```

## 🐳 Docker

Build and run with Docker Compose:

```bash
docker-compose up
```

Compose uses `${NOTION_TOKEN}` and `${NOTION_DATABASE_ID}` from your shell or `.env` file. It will sync and then build the site with `hugo --minify`.

Run the image directly:

```bash
docker build -t notion-hugo-sync .
docker run \
  -e NOTION_TOKEN=your_token \
  -e NOTION_DATABASE_ID=your_db_id \
  -v "$PWD/content":/app/content \
  -v "$PWD/static":/app/static \
  notion-hugo-sync
```

## 🚢 Deployment: Cloudflare Pages (GitHub Actions)

This repo includes a GitHub Actions workflow at `/.github/workflows/deploy.yml` that:

- Syncs content from Notion
- Builds the Hugo site using the PaperMod theme
- Deploys to Cloudflare Pages using `cloudflare/wrangler-action@v3` and `wrangler pages deploy`

Configure the following in your GitHub repository settings:

- Secrets
  - `NOTION_TOKEN`: Notion internal integration token
  - `NOTION_DATABASE_ID`: Database ID from Notion
  - `CLOUDFLARE_API_TOKEN`: Cloudflare API token with Pages write permissions
  - `CLOUDFLARE_ACCOUNT_ID`: Your Cloudflare Account ID
- Variables
  - `CLOUDFLARE_PAGES_PROJECT`: Your Cloudflare Pages project name

The workflow is triggered on pushes to `main`, on a 6-hourly schedule, and via manual dispatch. Output directory `public` is deployed via Wrangler.

## 📁 Project Structure

```
notion-hugo-blog/
├── config.toml                 # Hugo config example
├── content/                    # Generated posts
│   └── posts/
├── layouts/
│   └── partials/
│       └── math.html           # KaTeX support
├── scripts/
│   ├── cache_manager.py
│   ├── concurrent_downloader.py
│   ├── hugo_converter.py
│   ├── logging_utils.py
│   ├── media_handler.py
│   ├── notion_service.py       # Notion API client/service
│   ├── notion_sync.py          # Main sync script
│   └── retry_decorator.py
├── static/
│   ├── images/
│   ├── videos/
│   └── audio/
├── themes/                     # Hugo themes
├── requirements.txt            # Python dependencies (root)
├── Dockerfile                  # Docker build
├── docker-compose.yml          # Docker Compose
└── setup.sh                    # One-time setup helper
```

## 🛠️ Advanced

- **Custom blocks**: Extend `scripts/hugo_converter.py`
- **Media processing**: Adjust `scripts/media_handler.py`
- **Caching**: See `scripts/cache_manager.py`

## 🐛 Troubleshooting

- **Math not rendering**: Ensure `math: true` in front matter and the partial is included by your theme
- **Media download failures**: Check network, increase retries, verify Notion URLs
- **Notion rate limits**: Slow down sync frequency

### Debug logging

Set the log level via environment variable (handled by `scripts/logging_utils.py`):

```bash
LOG_LEVEL=DEBUG python scripts/notion_sync.py
```

## 🤝 Contributing

Contributions are welcome! Please open an issue to discuss major changes first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit (`git commit -m "feat: add YourFeature"`)
4. Push (`git push origin feature/YourFeature`)
5. Open a Pull Request

## 📄 License

Copyright 2025 Binbin Shen

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at `http://www.apache.org/licenses/LICENSE-2.0`.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## 🙏 Acknowledgments

- [Hugo](https://gohugo.io/)
- [Notion API](https://developers.notion.com/)
- [KaTeX](https://katex.org/)

## 📮 Support

- Create an Issue: `https://github.com/trainsh/notion-hugo-blog/issues`
- Start a Discussion: `https://github.com/trainsh/notion-hugo-blog/discussions`

---

Made with ❤️ by [Binbin Shen](https://github.com/trainsh)
