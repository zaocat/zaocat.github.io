FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV HUGO_VERSION=0.148.0
ENV PATH="/root/.local/bin:${PATH}"

# Install uv and Hugo
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget curl ca-certificates git \
    && update-ca-certificates \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && wget -O /tmp/hugo.deb https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb \
    && dpkg -i /tmp/hugo.deb \
    && rm -f /tmp/hugo.deb \
    && apt-get purge -y --auto-remove curl wget \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy dependencies and install with uv
COPY requirements.txt ./
RUN uv venv --python 3.10 \
    && source .venv/bin/activate \
    && uv pip install -r requirements.txt

# Ensure venv is used by default
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy project files
COPY . .

# Download PaperInk theme
RUN mkdir -p themes \
    && if [ ! -d themes/PaperInk ]; then \
        echo "PaperInk theme not found. Cloning..." && \
        git clone https://github.com/binbinsh/hugo-paperink.git themes/PaperInk; \
       else \
        echo "PaperInk theme already present."; \
       fi

# Default command
CMD ["python", "scripts/notion_sync.py"]
