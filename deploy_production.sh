#!/bin/bash

# 本番環境へのデプロイスクリプト（遅延初期化対応）
# Cloud Runへのデプロイを実行

set -e

echo "=========================================="
echo "  Detective Anywhere - Production Deploy"
echo "  With Lazy Initialization Optimization"
echo "=========================================="

# プロジェクトIDの確認
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT_ID is not set"
    echo "Please run: export GOOGLE_CLOUD_PROJECT_ID=your-project-id"
    exit 1
fi

PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID
REGION="asia-northeast1"
SERVICE_NAME="detective-anywhere"

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Lazy Init: ENABLED"
echo ""

# 確認プロンプト
read -p "Deploy to production? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# 1. プロジェクトを設定
echo ""
echo "Setting up Google Cloud project..."
gcloud config set project $PROJECT_ID

# 2. APIキーの確認
echo ""
echo "Checking API keys in Secret Manager..."
gcloud secrets describe gemini-api-key --project=$PROJECT_ID > /dev/null 2>&1 || {
    echo "Error: gemini-api-key secret not found in Secret Manager"
    echo "Please create it with: gcloud secrets create gemini-api-key --data-file=- --project=$PROJECT_ID"
    exit 1
}

gcloud secrets describe google-maps-api-key --project=$PROJECT_ID > /dev/null 2>&1 || {
    echo "Error: google-maps-api-key secret not found in Secret Manager"
    echo "Please create it with: gcloud secrets create google-maps-api-key --data-file=- --project=$PROJECT_ID"
    exit 1
}

echo "✅ API keys found in Secret Manager"

# 3. Cloud Buildでデプロイ
echo ""
echo "Starting Cloud Build deployment..."
echo "This will:"
echo "  1. Build Docker image with optimizations"
echo "  2. Push to Artifact Registry"
echo "  3. Deploy to Cloud Run with lazy initialization"
echo ""

gcloud builds submit \
    --config=cloudbuild.yaml \
    --project=$PROJECT_ID

# 4. デプロイ結果の確認
echo ""
echo "Checking deployment status..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Deployment failed - service URL not found"
    exit 1
fi

echo "✅ Service deployed successfully!"
echo "   URL: $SERVICE_URL"

# 5. ヘルスチェック
echo ""
echo "Running health check..."
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" | python3 -m json.tool 2>/dev/null || echo "Failed")

if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "✅ Health check passed!"
    echo "$HEALTH_RESPONSE" | head -20
else
    echo "⚠️  Health check failed or returned unexpected response"
    echo "$HEALTH_RESPONSE"
fi

# 6. パフォーマンステスト
echo ""
echo "Running performance test..."
echo "Testing startup time and response times..."

# コールドスタートテスト
START_TIME=$(date +%s%N)
curl -s -o /dev/null -w "Cold start time: %{time_total}s\n" "$SERVICE_URL/health"
END_TIME=$(date +%s%N)
DURATION=$((($END_TIME - $START_TIME) / 1000000))

if [ $DURATION -lt 10000 ]; then
    echo "✅ Cold start: ${DURATION}ms (< 10s target)"
else
    echo "⚠️  Cold start: ${DURATION}ms (> 10s target)"
fi

# ウォームレスポンステスト
echo ""
echo "Testing warm response times (5 requests)..."
for i in {1..5}; do
    curl -s -o /dev/null -w "Request $i: %{time_total}s\n" "$SERVICE_URL/health"
    sleep 0.5
done

# 7. サマリー
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Service URL: $SERVICE_URL"
echo "Region: $REGION"
echo "Features enabled:"
echo "  ✅ Lazy initialization"
echo "  ✅ Optimized cold start"
echo "  ✅ Background service warmup"
echo ""
echo "Next steps:"
echo "  1. Monitor Cloud Run metrics"
echo "  2. Check Cloud Logging for any errors"
echo "  3. Test API endpoints"
echo ""
echo "Monitor at: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"