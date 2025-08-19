# AIミステリー散歩 バックエンド Dockerfile

FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 共有モデルのコピー
COPY ../shared ./shared

# アプリケーションコードのコピー
COPY src ./src

# ヘルスチェック用スクリプト
COPY healthcheck.py .

# ポート公開
EXPOSE 8000

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python healthcheck.py

# 環境変数の設定
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# アプリケーション起動
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]