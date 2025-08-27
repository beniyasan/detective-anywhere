# GCP デプロイメント手順

## 前提条件

1. Google Cloud アカウントとプロジェクトの作成
2. Google Cloud SDK (gcloud CLI) のインストール
3. 必要なAPI キーの準備:
   - Gemini API Key
   - Google Maps API Key

## ステップ1: Google Cloud プロジェクトの設定

```bash
# Google Cloud にログイン
gcloud auth login

# プロジェクトを作成（既存の場合はスキップ）
gcloud projects create detective-anywhere-app --name="Detective Anywhere"

# プロジェクトを設定
export GOOGLE_CLOUD_PROJECT=detective-anywhere-app
gcloud config set project $GOOGLE_CLOUD_PROJECT

# 課金アカウントをリンク（必須）
gcloud billing accounts list
gcloud billing projects link $GOOGLE_CLOUD_PROJECT --billing-account=YOUR_BILLING_ACCOUNT_ID
```

## ステップ2: 環境変数の設定

```bash
# 必須環境変数を設定
export GOOGLE_CLOUD_PROJECT=detective-anywhere-app
export GEMINI_API_KEY=your_gemini_api_key_here
export GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

## ステップ3: 自動デプロイメントの実行

```bash
# デプロイスクリプトを実行可能にする
chmod +x deploy.sh

# デプロイを実行
./deploy.sh
```

## ステップ4: 手動デプロイメント（オプション）

自動スクリプトが失敗した場合の手動手順：

### 4.1 必要なAPIの有効化

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    firestore.googleapis.com \
    secretmanager.googleapis.com
```

### 4.2 Firestore データベースの作成

```bash
gcloud firestore databases create \
    --location=asia-northeast1
```

### 4.3 Secret Manager でAPI キーを保存

```bash
# Gemini API Key
echo "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-

# Google Maps API Key  
echo "$GOOGLE_MAPS_API_KEY" | gcloud secrets create google-maps-api-key --data-file=-
```

### 4.4 Cloud Build でデプロイ

```bash
gcloud builds submit . --config=cloudbuild.yaml
```

## ステップ5: デプロイ後の確認

```bash
# サービスURLを取得
SERVICE_URL=$(gcloud run services describe detective-anywhere \
    --region=asia-northeast1 \
    --format="value(status.url)")

echo "Service URL: $SERVICE_URL"

# ヘルスチェック
curl "$SERVICE_URL/health"

# API ドキュメント
open "$SERVICE_URL/docs"
```

## トラブルシューティング

### 課金エラー
プロジェクトに課金アカウントが設定されていない場合、Cloud Run へのデプロイが失敗します。

### 権限エラー
必要な権限が不足している場合：

```bash
# 基本的な権限を確認
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# 必要に応じて権限を追加
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="user:your-email@example.com" \
    --role="roles/editor"
```

### ログの確認

```bash
# Cloud Run ログを確認
gcloud logs read --service=detective-anywhere --region=asia-northeast1

# Cloud Build ログを確認
gcloud builds list
gcloud builds log BUILD_ID
```

## カスタマイズ

### Cloud Run の設定変更

`cloudbuild.yaml` または `deploy.sh` で以下の設定を変更可能：

- `--memory`: メモリサイズ（デフォルト: 2Gi）
- `--cpu`: CPU 数（デフォルト: 2）  
- `--min-instances`: 最小インスタンス数（デフォルト: 0）
- `--max-instances`: 最大インスタンス数（デフォルト: 10）

### 環境変数の追加

新しい環境変数を追加する場合は：

1. `.env.production` に追加
2. `cloudbuild.yaml` の `--set-env-vars` に追加
3. 必要に応じて Secret Manager に保存

## コスト最適化

- `--min-instances=0` で未使用時のコストを削減
- `--memory=1Gi --cpu=1` でリソースを削減（トラフィックが少ない場合）
- Firestore の使用量を監視