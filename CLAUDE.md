# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands
- **Setup**: `./setup.sh` – creates environment, directories, virtualenv, and installs dependencies.
- **Sync Notion content**: `python scripts/notion_sync.py --clean`
- **Run Hugo dev server**: `hugo server -D`
- **Build static site**: `hugo --minify`
- **Docker build/run**:
  ```bash
  docker build -t notion-hugo-sync .
  docker run \
    -e NOTION_TOKEN=... \
    -e NOTION_DATABASE_ID=... \
    -v "$PWD/content":/app/content \
    -v "$PWD/static":/app/static \
    notion-hugo-sync
  ```
- **Deploy via GitHub Actions**: workflow located at `/.github/workflows/deploy.yml`.

## Project Architecture
- **Content Generation**: `scripts/notion_sync.py` fetches Notion database entries and writes Markdown files under `content/posts/`. It uses the Notion API client in `scripts/notion_service.py`.
- **Conversion**: `scripts/hugo_converter.py` converts Notion blocks to Hugo-compatible Markdown, handling media via `scripts/media_handler.py`.
- **Caching & Downloads**: `scripts/cache_manager.py` tracks previously downloaded assets; concurrent downloads are performed by `scripts/concurrent_downloader.py` with retries from `scripts/retry_decorator.py`.
- **Logging**: Configurable via `LOG_LEVEL` environment variable and handled in `scripts/logging_utils.py`.
- **Static Assets**: Images, videos, audio stored under `static/` and referenced by generated Markdown.

## Testing
No unit tests are provided in this repository.
