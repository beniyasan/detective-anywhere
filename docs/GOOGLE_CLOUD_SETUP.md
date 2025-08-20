# Google Cloud API Keys セットアップガイド

このドキュメントでは、AIミステリー散歩の本番環境で必要なGoogle Cloud APIキーの取得と設定方法を説明します。

## 📋 必要なAPIキー

### 1. Gemini API キー
- **用途**: AIシナリオ生成
- **取得先**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **権限**: Gemini API へのアクセス

### 2. Google Maps API キー  
- **用途**: POI検索、ジオコーディング
- **取得先**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **必要なAPI**: Places API (New), Geocoding API

## 🚀 セットアップ手順

### Step 1: Google Cloud プロジェクトの作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
   - プロジェクト名: `detective-anywhere-prod`
   - プロジェクトID: `detective-anywhere-prod` (ユニークである必要があります)
3. 請求先アカウントを設定

### Step 2: 必要なAPIの有効化

Google Cloud Console で以下のAPIを有効にします：

```bash
# Google Cloud CLI を使用する場合
gcloud services enable aiplatform.googleapis.com
gcloud services enable places.googleapis.com
gcloud services enable geocoding.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable firestore.googleapis.com
```

または、Console UIで手動で有効化：
- Vertex AI API
- Places API (New) 
- Geocoding API
- Secret Manager API
- Cloud Firestore API

### Step 3: Gemini API キーの取得

1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 「Create API Key」をクリック
3. 作成されたAPIキーをコピー
4. **重要**: APIキーを安全に保管

### Step 4: Google Maps API キーの取得

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) にアクセス
2. 「認証情報を作成」→「APIキー」をクリック
3. 作成されたAPIキーの「制限」を設定：
   - **アプリケーションの制限**: なし（または適切なHTTP参照元を設定）
   - **API の制限**: 
     - Places API (New)
     - Geocoding API

### Step 5: Secret Manager でのキー管理

#### 5.1 Secret Manager の有効化
```bash
gcloud services enable secretmanager.googleapis.com
```

#### 5.2 シークレットの作成
```bash
# Gemini API キー
gcloud secrets create GEMINI_API_KEY --data-file=gemini_key.txt

# Google Maps API キー  
gcloud secrets create GOOGLE_MAPS_API_KEY --data-file=maps_key.txt

# JWT秘密鍵（ランダム文字列）
echo "$(openssl rand -base64 32)" | gcloud secrets create JWT_SECRET_KEY --data-file=-
```

#### 5.3 サービスアカウントの設定
```bash
# サービスアカウント作成
gcloud iam service-accounts create detective-anywhere-service \
    --display-name="Detective Anywhere Service Account"

# Secret Manager アクセス権限付与
gcloud projects add-iam-policy-binding detective-anywhere-prod \
    --member="serviceAccount:detective-anywhere-service@detective-anywhere-prod.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Firestore アクセス権限付与
gcloud projects add-iam-policy-binding detective-anywhere-prod \
    --member="serviceAccount:detective-anywhere-service@detective-anywhere-prod.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
```

### Step 6: 環境変数の設定

本番環境では `.env.production` ファイルの設定値を使用します：

```env
# Google Cloud設定
GOOGLE_CLOUD_PROJECT_ID=detective-anywhere-prod
GOOGLE_CLOUD_LOCATION=asia-northeast1

# Secret Manager使用
USE_SECRET_MANAGER=true

# 本番環境設定
ENV=production
DEBUG=false
USE_MOCK_DATA=false
```

## 🔧 開発環境での検証

### 1. ローカルテスト
```bash
# APIキーが正しく設定されているか確認
python test-google-maps-simple.py

# 統合テスト実行
python test-integrated-api.py
```

### 2. Secret Manager テスト
```bash
# シークレット取得テスト
python -c "
from backend.src.config.secrets import get_api_key
print('Gemini:', bool(get_api_key('gemini')))
print('Maps:', bool(get_api_key('google_maps')))
"
```

## 🔐 セキュリティ対策

### APIキー制限設定

1. **Google Maps API キー制限**:
   - HTTPリファラー制限を設定
   - 不要なAPIへのアクセスを無効化
   - 使用量監視アラートを設定

2. **Gemini API キー制限**:
   - 使用量制限を設定
   - IPアドレス制限（可能な場合）

### 監視とアラート

```bash
# 使用量監視アラートの作成例
gcloud alpha monitoring policies create --policy-from-file=api_usage_alert.yaml
```

## 💰 コスト管理

### API使用量の目安
- **Places API**: $17/1000リクエスト
- **Geocoding API**: $5/1000リクエスト  
- **Gemini API**: モデルと使用量により変動

### 予算アラート設定
```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Detective Anywhere API Budget" \
  --budget-amount=100USD \
  --threshold-rule=percent=80,basis=current-spend
```

## ❗ トラブルシューティング

### よくあるエラー

1. **"API key not authorized"**
   - APIキーの制限設定を確認
   - 必要なAPIが有効になっているか確認

2. **"REQUEST_DENIED"**
   - 請求先アカウントが設定されているか確認
   - APIキーの権限を確認

3. **Secret Manager エラー**
   - サービスアカウントの権限を確認
   - Secret Manager APIが有効になっているか確認

### デバッグコマンド
```bash
# プロジェクト設定確認
gcloud config get-value project

# 有効なAPI確認
gcloud services list --enabled

# Secret Manager シークレット一覧
gcloud secrets list
```

## 📚 参考リンク

- [Google AI Studio](https://aistudio.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Places API (New) Documentation](https://developers.google.com/maps/documentation/places/web-service/overview)
- [Geocoding API Documentation](https://developers.google.com/maps/documentation/geocoding/overview)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)