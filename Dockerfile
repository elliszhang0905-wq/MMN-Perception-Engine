FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MMN_HOST=0.0.0.0 \
    MMN_PORT=8765 \
    MMN_AUTO_OPEN_BROWSER=false \
    MMN_DESKTOP_BRIDGE_ENABLED=false \
    MMN_DATA_ROOT=/app/data \
    MMN_DATA_DIR=/app/data \
    MMN_BACKUP_ROOT=/app/backups \
    MMN_DB_PATH=/app/data/commercial_demo.db \
    MMN_DOUYIN_COLLECTOR_NODE=/usr/bin/node \
    MMN_DOUYIN_COLLECTOR_NODE_MODULES=/app/node_modules \
    MMN_DOUYIN_BROWSER_EXECUTABLE=/usr/bin/chromium

WORKDIR /app

RUN sed -i \
       -e 's|http://deb.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
       -e 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' \
       -e 's|http://security.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' \
       /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 install -y --no-install-recommends \
       libreoffice-writer libreoffice-impress libreoffice-calc \
       tesseract-ocr tesseract-ocr-chi-sim fonts-noto-cjk \
       nodejs npm chromium \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --no-save --ignore-scripts playwright-core@1.53.0 \
    && npm cache clean --force

COPY requirements-bf-factory.txt /tmp/requirements-bf-factory.txt
COPY requirements-creator-distillation.txt /tmp/requirements-creator-distillation.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r /tmp/requirements-bf-factory.txt -r /tmp/requirements-creator-distillation.txt

COPY . /app

RUN mkdir -p /app/data /app/backups /app/logs

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:%s/api/health' % os.environ.get('MMN_PORT', '8765'), timeout=4).read()" || exit 1

CMD ["python", "server.py"]
