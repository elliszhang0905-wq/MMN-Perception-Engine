FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MMN_HOST=0.0.0.0 \
    MMN_PORT=8765 \
    MMN_AUTO_OPEN_BROWSER=false \
    MMN_DESKTOP_BRIDGE_ENABLED=false \
    MMN_DATA_DIR=/app/data \
    MMN_DB_PATH=/app/data/commercial_demo.db

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libreoffice-writer libreoffice-impress libreoffice-calc \
       tesseract-ocr tesseract-ocr-chi-sim fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-bf-factory.txt /tmp/requirements-bf-factory.txt
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r /tmp/requirements-bf-factory.txt

COPY . /app

RUN mkdir -p /app/data /app/backups /app/logs

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:%s/api/health' % os.environ.get('MMN_PORT', '8765'), timeout=4).read()" || exit 1

CMD ["python", "server.py"]
