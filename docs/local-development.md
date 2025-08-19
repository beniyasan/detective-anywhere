# ローカル開発環境ガイド

## 概要
Google Cloud環境をローカルで開発・テストするための環境構築ガイド。

## 🚀 クイックスタート

### 1. 前提条件
```bash
# 必要なソフトウェア
- Docker & Docker Compose
- Python 3.11+
- Git
```

### 2. 環境設定
```bash
# リポジトリクローン
git clone https://github.com/beniyasan/detective-anywhere.git
cd detective-anywhere

# 環境変数設定
cp .env.example .env
# .envファイルを編集してAPI キーを設定

# 実行権限付与
chmod +x local-dev.sh
chmod +x test-local.py
```

### 3. 開発環境起動
```bash
# 自動セットアップスクリプト実行
./local-dev.sh

# または手動で選択
# 1: 完全環境 (Firestore エミュレーター + Redis)
# 2: 軽量環境 (モックデータのみ)  
# 3: ローカル Python 環境
```

## 📋 開発環境オプション

### オプション1: 完全環境 (推奨)
```bash
docker-compose up --build
```

**特徴:**
- ✅ Firestore エミュレーター
- ✅ Redis キャッシュ
- ✅ Nginx リバースプロキシ
- ✅ ホットリロード対応

**アクセス:**
- API: http://localhost:8000
- Firestore UI: http://localhost:4000
- Redis: localhost:6379

### オプション2: 軽量環境
```bash
docker-compose -f docker-compose.dev.yml up --build
```

**特徴:**
- ✅ モックデータ使用
- ✅ 高速起動
- ✅ API 機能フォーカス

### オプション3: ローカル Python 環境
```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# サーバー起動
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🧪 テスト実行

### 自動テスト
```bash
# 全エンドポイントテスト
python test-local.py

# 特定テスト実行
cd backend
pytest tests/ -v
```

### 手動テスト
```bash
# ヘルスチェック
curl http://localhost:8000/health

# API ドキュメント
open http://localhost:8000/docs

# POI検索テスト
curl "http://localhost:8000/api/v1/poi/nearby?lat=35.6762&lng=139.6503&radius=1000"
```

## 🛠️ 開発ワークフロー

### 1. コード変更の確認
```bash
# ホットリロード有効（Docker環境）
# ファイル保存で自動リロード

# ローカル Python環境
uvicorn src.main:app --reload
```

### 2. デバッグ
```bash
# ログ確認
docker-compose logs -f detective-api

# コンテナ内でデバッグ
docker-compose exec detective-api bash
```

### 3. データベース操作
```bash
# Firestore エミュレーター UI
open http://localhost:4000

# データクリア
docker-compose down -v
```

## 🔧 環境別設定

### 開発環境 (.env.development)
```env
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
USE_FIRESTORE_EMULATOR=true
USE_MOCK_DATA=false
```

### テスト環境 (.env.test)
```env
ENV=test
DEBUG=false
LOG_LEVEL=INFO
USE_FIRESTORE_EMULATOR=true
USE_MOCK_DATA=true
```

### モック環境 (.env.mock)
```env
ENV=development
DEBUG=true
USE_FIRESTORE_EMULATOR=false
USE_MOCK_DATA=true
GEMINI_API_KEY=mock_key
GOOGLE_MAPS_API_KEY=mock_key
```

## 📊 監視・ログ

### ログ確認
```bash
# すべてのサービス
docker-compose logs -f

# 特定サービス
docker-compose logs -f detective-api

# リアルタイムログ
tail -f backend/logs/app.log
```

### メトリクス
```bash
# API レスポンス時間
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health

# リソース使用量
docker stats
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. Dockerコンテナが起動しない
```bash
# ポート確認
lsof -i :8000

# ログ確認
docker-compose logs detective-api

# 再ビルド
docker-compose down
docker-compose up --build
```

#### 2. Firestore エミュレーター接続エラー
```bash
# エミュレーター状態確認
curl http://localhost:8080

# 環境変数確認
echo $FIRESTORE_EMULATOR_HOST

# 手動起動
gcloud emulators firestore start --host-port=0.0.0.0:8080
```

#### 3. API キーエラー
```bash
# 環境変数確認
source .env
echo $GEMINI_API_KEY
echo $GOOGLE_MAPS_API_KEY

# モックモード切り替え
export USE_MOCK_DATA=true
```

#### 4. Python 依存関係エラー
```bash
# 仮想環境リセット
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## 🎯 パフォーマンス最適化

### 1. Docker 最適化
```dockerfile
# マルチステージビルド使用
# .dockerignore 適切設定
# レイヤーキャッシュ活用
```

### 2. 開発効率向上
```bash
# ボリュームマウント使用
# ホットリロード有効
# 並列処理設定
```

### 3. API 最適化
```python
# 非同期処理
# キャッシュ活用
# バッチ処理
```

## 🔒 セキュリティ注意事項

- ✅ `.env` ファイルをGitignoreに追加済み
- ✅ API キーの環境変数管理
- ✅ 開発環境でのみデバッグ情報表示
- ⚠️ 本番API キーをローカルで使用しない
- ⚠️ Firestore エミュレーターデータは永続化されない

## 📚 参考資料

- [Google Cloud エミュレーター](https://cloud.google.com/sdk/gcloud/reference/emulators)
- [Firestore エミュレーター](https://firebase.google.com/docs/emulator-suite/connect_firestore)
- [FastAPI 開発](https://fastapi.tiangolo.com/tutorial/debugging/)
- [Docker Compose](https://docs.docker.com/compose/)