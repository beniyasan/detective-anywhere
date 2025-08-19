#!/bin/bash
# AIミステリー散歩 - デプロイメントスクリプト

set -e

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION="asia-northeast1"
SERVICE_NAME="detective-anywhere-api"
REPOSITORY_NAME="detective-anywhere"

echo -e "${GREEN}🚀 AIミステリー散歩 デプロイメント開始${NC}"

# 1. 環境変数チェック
echo -e "${YELLOW}📋 環境変数をチェック中...${NC}"

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ GOOGLE_CLOUD_PROJECT が設定されていません${NC}"
    exit 1
fi

echo -e "${GREEN}✅ プロジェクトID: $PROJECT_ID${NC}"

# 2. 必要なサービスの有効化
echo -e "${YELLOW}🔧 Google Cloud サービスを有効化中...${NC}"

gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com \
    --project=$PROJECT_ID

# 3. Artifact Registry リポジトリの作成
echo -e "${YELLOW}📦 Artifact Registry リポジトリを作成中...${NC}"

gcloud artifacts repositories create $REPOSITORY_NAME \
    --repository-format=docker \
    --location=$REGION \
    --project=$PROJECT_ID \
    || echo "リポジトリは既に存在します"

# 4. Firestore データベースの初期化
echo -e "${YELLOW}🗄️ Firestore データベースを初期化中...${NC}"

gcloud firestore databases create \
    --location=$REGION \
    --project=$PROJECT_ID \
    || echo "Firestore データベースは既に存在します"

# 5. Secret Manager でシークレットを作成
echo -e "${YELLOW}🔐 Secret Manager でシークレットを設定中...${NC}"

# Gemini API キーの設定
if [ ! -z "$GEMINI_API_KEY" ]; then
    echo "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
        --data-file=- \
        --project=$PROJECT_ID \
        || echo "Gemini API Key シークレットは既に存在します"
else
    echo -e "${YELLOW}⚠️ GEMINI_API_KEY 環境変数が設定されていません${NC}"
fi

# Google Maps API キーの設定
if [ ! -z "$GOOGLE_MAPS_API_KEY" ]; then
    echo "$GOOGLE_MAPS_API_KEY" | gcloud secrets create google-maps-api-key \
        --data-file=- \
        --project=$PROJECT_ID \
        || echo "Google Maps API Key シークレットは既に存在します"
else
    echo -e "${YELLOW}⚠️ GOOGLE_MAPS_API_KEY 環境変数が設定されていません${NC}"
fi

# 6. サービスアカウントの作成
echo -e "${YELLOW}🔑 サービスアカウントを作成中...${NC}"

gcloud iam service-accounts create $SERVICE_NAME \
    --display-name="Detective Anywhere API Service Account" \
    --project=$PROJECT_ID \
    || echo "サービスアカウントは既に存在します"

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# 7. Cloud Build でビルド・デプロイ
echo -e "${YELLOW}🏗️ Cloud Build でビルド・デプロイ中...${NC}"

gcloud builds submit . \
    --config=backend/cloudbuild.yaml \
    --project=$PROJECT_ID \
    --substitutions=_SERVICE_NAME=$SERVICE_NAME,_REGION=$REGION

# 8. Cloud Run サービスの設定更新
echo -e "${YELLOW}⚙️ Cloud Run サービスを設定中...${NC}"

# シークレットを環境変数として設定
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --set-env-vars="GEMINI_API_KEY=\$(gcloud secrets versions access latest --secret=gemini-api-key)" \
    --set-env-vars="GOOGLE_MAPS_API_KEY=\$(gcloud secrets versions access latest --secret=google-maps-api-key)" \
    --service-account="$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    || echo "サービス更新をスキップ"

# 9. デプロイ結果の確認
echo -e "${YELLOW}🔍 デプロイ結果を確認中...${NC}"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

echo -e "${GREEN}✅ デプロイメント完了!${NC}"
echo -e "${GREEN}🌐 サービスURL: $SERVICE_URL${NC}"
echo -e "${GREEN}📚 API ドキュメント: $SERVICE_URL/docs${NC}"

# 10. ヘルスチェック
echo -e "${YELLOW}🏥 ヘルスチェック実行中...${NC}"

sleep 10  # サービスの起動を待つ

if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ サービスは正常に動作しています${NC}"
else
    echo -e "${RED}❌ サービスのヘルスチェックに失敗しました${NC}"
    echo -e "${YELLOW}ログを確認してください:${NC}"
    echo "gcloud logs read --service=$SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
fi

echo -e "${GREEN}🎉 デプロイメント処理が完了しました!${NC}"