FROM python:3.11-slim

# 安装 Hugo
ENV HUGO_VERSION 0.119.0
RUN apt-get update && \\
    apt-get install -y wget && \\
    wget -O hugo.deb https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb && \\
    dpkg -i hugo.deb && \\
    rm hugo.deb && \\
    apt-get clean

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY scripts/requirements.txt ./scripts/
RUN pip install --no-cache-dir -r scripts/requirements.txt

# 复制项目文件
COPY . .

# 运行脚本
CMD ["python", "scripts/notion_sync.py"]
