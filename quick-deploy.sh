#!/bin/bash
# クイックデプロイスクリプト
set -e

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Detective Anywhere - クイックデプロイ${NC}"

# 必須環境変数の確認
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo -e "${RED}❌ GOOGLE_CLOUD_PROJECT 環境変数が必要です${NC}"
    echo "例: export GOOGLE_CLOUD_PROJECT=your-project-id"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ GEMINI_API_KEY 環境変数が必要です${NC}"
    exit 1
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo -e "${RED}❌ GOOGLE_MAPS_API_KEY 環境変数が必要です${NC}"
    exit 1
fi

PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION="asia-northeast1"

echo -e "${GREEN}✅ プロジェクト: $PROJECT_ID${NC}"

# 1. プロジェクトを設定
echo -e "${YELLOW}🔧 プロジェクトを設定中...${NC}"
gcloud config set project $PROJECT_ID

# 2. 必要なAPIを有効化
echo -e "${YELLOW}📡 必要なAPIを有効化中...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com

# 3. Artifact Registry リポジトリを作成
echo -e "${YELLOW}📦 Artifact Registry リポジトリを作成中...${NC}"
gcloud artifacts repositories create detective-anywhere \
    --repository-format=docker \
    --location=$REGION || echo "既に存在します"

# 4. Firestore を初期化
echo -e "${YELLOW}🗄️ Firestore を初期化中...${NC}"
gcloud firestore databases create \
    --location=$REGION || echo "既に存在します"

# 5. シークレットを作成
echo -e "${YELLOW}🔐 API キーをSecret Managerに保存中...${NC}"
echo "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
    --data-file=- || gcloud secrets versions add gemini-api-key --data-file=<(echo "$GEMINI_API_KEY")

echo "$GOOGLE_MAPS_API_KEY" | gcloud secrets create google-maps-api-key \
    --data-file=- || gcloud secrets versions add google-maps-api-key --data-file=<(echo "$GOOGLE_MAPS_API_KEY")

# 6. Cloud Build でデプロイ
echo -e "${YELLOW}🏗️ アプリケーションをデプロイ中...${NC}"
gcloud builds submit . --config=cloudbuild.yaml

# 7. 結果を確認
echo -e "${YELLOW}🔍 デプロイ結果を確認中...${NC}"
SERVICE_URL=$(gcloud run services describe detective-anywhere \
    --region=$REGION \
    --format="value(status.url)")

echo -e "${GREEN}✅ デプロイ完了！${NC}"
echo -e "${GREEN}🌐 アプリURL: $SERVICE_URL${NC}"
echo -e "${GREEN}📱 モバイル版: $SERVICE_URL/mobile-app.html${NC}"
echo -e "${GREEN}🖥️ デスクトップ版: $SERVICE_URL/web-demo.html${NC}"
echo -e "${GREEN}📚 API ドキュメント: $SERVICE_URL/docs${NC}"

# 8. ヘルスチェック
echo -e "${YELLOW}🏥 ヘルスチェック実行中...${NC}"
sleep 5
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ アプリケーションは正常に動作中${NC}"
else
    echo -e "${RED}❌ ヘルスチェック失敗 - ログを確認してください${NC}"
    echo "gcloud logs read --service=detective-anywhere --region=$REGION"
fi

echo -e "${GREEN}🎉 デプロイ完了！${NC}"