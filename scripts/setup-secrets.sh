#!/bin/bash
# Google Cloud Secret Manager セットアップスクリプト

set -e

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Google Cloud Secret Manager セットアップスクリプト${NC}"
echo "=================================================="

# プロジェクトID確認
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Google Cloud プロジェクトが設定されていません${NC}"
    echo "次のコマンドでプロジェクトを設定してください："
    echo "gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ プロジェクトID: $PROJECT_ID${NC}"

# 必要なAPIの有効化
echo -e "${YELLOW}🔧 必要なAPIを有効化中...${NC}"

REQUIRED_APIS=(
    "secretmanager.googleapis.com"
    "firestore.googleapis.com"
    "places.googleapis.com"
    "geocoding.googleapis.com"
    "aiplatform.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    echo "  - $api を有効化中..."
    gcloud services enable $api --quiet
done

echo -e "${GREEN}✅ 必要なAPIの有効化完了${NC}"

# サービスアカウント作成
SERVICE_ACCOUNT="detective-anywhere-service"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"

echo -e "${YELLOW}👤 サービスアカウントを作成中...${NC}"

# 既存のサービスアカウント確認
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --quiet >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  サービスアカウント $SERVICE_ACCOUNT は既に存在します${NC}"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT \
        --display-name="Detective Anywhere Service Account" \
        --description="AIミステリー散歩アプリケーション用サービスアカウント"
    echo -e "${GREEN}✅ サービスアカウント作成完了${NC}"
fi

# IAMロールの付与
echo -e "${YELLOW}🔑 IAMロールを付与中...${NC}"

ROLES=(
    "roles/secretmanager.secretAccessor"
    "roles/datastore.user"
    "roles/aiplatform.user"
)

for role in "${ROLES[@]}"; do
    echo "  - $role を付与中..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet
done

echo -e "${GREEN}✅ IAMロール付与完了${NC}"

# シークレットの作成関数
create_secret() {
    local SECRET_NAME=$1
    local SECRET_DESCRIPTION=$2
    
    echo -e "${YELLOW}🔐 シークレット $SECRET_NAME を作成中...${NC}"
    
    if gcloud secrets describe $SECRET_NAME --quiet >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  シークレット $SECRET_NAME は既に存在します${NC}"
        read -p "新しい値で更新しますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "新しい値を入力してください："
            read -s SECRET_VALUE
            echo $SECRET_VALUE | gcloud secrets versions add $SECRET_NAME --data-file=-
            echo -e "${GREEN}✅ シークレット $SECRET_NAME を更新しました${NC}"
        fi
    else
        # 新規作成
        gcloud secrets create $SECRET_NAME --replication-policy="automatic"
        echo "$SECRET_DESCRIPTION"
        echo "値を入力してください："
        read -s SECRET_VALUE
        echo $SECRET_VALUE | gcloud secrets versions add $SECRET_NAME --data-file=-
        echo -e "${GREEN}✅ シークレット $SECRET_NAME を作成しました${NC}"
    fi
}

# 必須シークレットの作成
echo -e "${BLUE}📝 APIキーの設定${NC}"
echo "以下のシークレットを設定します："
echo

echo -e "${YELLOW}1. Gemini API キー${NC}"
echo "取得先: https://aistudio.google.com/app/apikey"
create_secret "GEMINI_API_KEY" "Gemini API キーを入力してください"

echo -e "${YELLOW}2. Google Maps API キー${NC}"
echo "取得先: https://console.cloud.google.com/apis/credentials"
echo "必要な権限: Places API (New), Geocoding API"
create_secret "GOOGLE_MAPS_API_KEY" "Google Maps API キーを入力してください"

echo -e "${YELLOW}3. JWT秘密鍵${NC}"
echo "ランダムな文字列を自動生成しますか？ (Y/n): "
read -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    create_secret "JWT_SECRET_KEY" "JWT秘密鍵を入力してください"
else
    JWT_SECRET=$(openssl rand -base64 32)
    if gcloud secrets describe "JWT_SECRET_KEY" --quiet >/dev/null 2>&1; then
        echo $JWT_SECRET | gcloud secrets versions add "JWT_SECRET_KEY" --data-file=-
        echo -e "${GREEN}✅ JWT秘密鍵を更新しました${NC}"
    else
        gcloud secrets create "JWT_SECRET_KEY" --replication-policy="automatic"
        echo $JWT_SECRET | gcloud secrets versions add "JWT_SECRET_KEY" --data-file=-
        echo -e "${GREEN}✅ JWT秘密鍵を作成しました${NC}"
    fi
fi

# サービスアカウントキーの生成（オプション）
echo -e "${YELLOW}🔑 サービスアカウントキーを生成しますか？ (y/N): ${NC}"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    KEY_FILE="detective-anywhere-service-key.json"
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo -e "${GREEN}✅ サービスアカウントキーを $KEY_FILE に保存しました${NC}"
    echo -e "${RED}⚠️  このファイルは機密情報です。安全に保管してください${NC}"
fi

# 設定確認
echo -e "${BLUE}📋 設定確認${NC}"
echo "作成されたシークレット："
gcloud secrets list --filter="name:GEMINI_API_KEY OR name:GOOGLE_MAPS_API_KEY OR name:JWT_SECRET_KEY"

echo -e "${BLUE}🎯 セットアップ完了！${NC}"
echo "次のステップ："
echo "1. アプリケーションの環境変数を設定"
echo "   export GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID"
echo "   export USE_SECRET_MANAGER=true"
echo "2. アプリケーションをデプロイまたは起動"
echo "3. ヘルスチェックでAPI接続を確認"

echo -e "${GREEN}✨ Google Cloud Secret Manager のセットアップが完了しました！${NC}"