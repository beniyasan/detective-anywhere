# 🚀 AIミステリー散歩 - ローカルテスト クイックスタート

## 📋 概要

このドキュメントは、**AIミステリー散歩**プロジェクトをローカル環境でテストするための完全ガイドです。Google Cloud環境を完全にローカルで再現し、開発・デバッグを効率的に行えます。

## ⚡ 1分でスタート

```bash
# 1. リポジトリクローン
git clone https://github.com/beniyasan/detective-anywhere.git
cd detective-anywhere

# 2. 環境設定
cp .env.example .env
# .envファイルを編集してAPI キーを設定

# 3. 開発環境起動
./local-dev.sh

# 4. 動作確認
python test-local.py
```

## 🎯 3つの開発環境オプション

### オプション1: 完全環境 (推奨) 🌟

**最も本番環境に近い完全な開発環境**

```bash
./local-dev.sh
# → 「1」を選択
```

**含まれる機能:**
- ✅ **Firestore エミュレーター** - 本番データベース環境を完全再現
- ✅ **Redis キャッシュ** - 高速データアクセス
- ✅ **Nginx リバースプロキシ** - 本番同等のルーティング
- ✅ **ホットリロード** - コード変更の即座反映

**アクセスポイント:**
- API サーバー: http://localhost:8000
- Firestore UI: http://localhost:4000  
- API ドキュメント: http://localhost:8000/docs

### オプション2: 軽量環境 ⚡

**高速起動・軽量リソースでの開発環境**

```bash
./local-dev.sh
# → 「2」を選択
```

**特徴:**
- ✅ **モックデータ使用** - 外部API不要
- ✅ **高速起動** - 30秒以内で起動完了
- ✅ **軽量リソース** - メモリ使用量最小化
- ✅ **API機能フォーカス** - コア機能のみテスト

### オプション3: ネイティブPython環境 🐍

**従来のPython開発環境**

```bash
./local-dev.sh
# → 「3」を選択
```

**特徴:**
- ✅ **ネイティブPython** - システムPython環境使用
- ✅ **仮想環境自動作成** - 依存関係の分離
- ✅ **IDE対応** - PyCharm/VSCode完全対応
- ✅ **デバッグ機能** - ブレークポイント等フル活用

## 🧪 自動テストスイート

### 包括的テスト実行

```bash
python test-local.py
```

**実行されるテスト:**

| テスト項目 | 内容 | 期待結果 |
|---|---|---|
| **ヘルスチェック** | サーバー起動状態確認 | ✅ HTTP 200 |
| **POI検索** | 東京タワー周辺POI取得 | ✅ 複数POI発見 |
| **ゲーム作成** | 新規ミステリーゲーム生成 | ✅ シナリオ・証拠生成 |
| **ゲーム状態** | 進行状況取得 | ✅ 正常な状態遷移 |
| **位置検証** | GPS座標の有効性確認 | ✅ エリア適合性判定 |

### テスト結果例

```
🚀 ローカル環境テスト開始
==================================================
🏥 ヘルスチェックテスト...
✅ ヘルスチェック成功: healthy

📍 POI検索テスト...
✅ POI検索成功: 12件のPOIを発見
   例: 東京タワー (landmark)

🎮 ゲーム開始テスト...
✅ ゲーム開始成功!
   ゲームID: abc123...
   シナリオ: カフェに響く悲鳴
   証拠数: 5個

📊 テスト結果サマリー:
   health: ✅ PASS
   poi_search: ✅ PASS
   game_start: ✅ PASS
   game_status: ✅ PASS
   location_validation: ✅ PASS

🎯 総合結果: 5/5 テスト通過
🎉 すべてのテストに合格しました！
```

## 🌐 アクセスポイント一覧

起動完了後、以下のURLでアクセス可能：

| サービス | URL | 説明 |
|---|---|---|
| **メインAPI** | http://localhost:8000 | FastAPIサーバー |
| **APIドキュメント** | http://localhost:8000/docs | Swagger UI |
| **ヘルスチェック** | http://localhost:8000/health | サーバー状態 |
| **Firestore UI** | http://localhost:4000 | データベース管理画面 |
| **Redis** | localhost:6379 | キャッシュサーバー |

## 🔧 環境設定

### 必要な環境変数

`.env`ファイルを作成し、以下を設定：

```env
# 必須API キー
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# オプション設定
GOOGLE_CLOUD_PROJECT_ID=detective-anywhere-dev
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
```

### API キー取得方法

1. **Gemini API キー**
   - [Google AI Studio](https://aistudio.google.com/app/apikey) でAPI キー取得
   - 無料枠あり（月60回まで）

2. **Google Maps API キー**
   - [Google Cloud Console](https://console.cloud.google.com/apis/credentials) でAPI キー作成
   - Places API、Geocoding APIを有効化

## 🐳 Docker環境詳細

### 完全環境の構成

```yaml
# docker-compose.yml
services:
  detective-api:     # メインAPIサーバー
  firestore-emulator: # Firestoreエミュレーター
  redis:             # キャッシュサーバー
  nginx:             # リバースプロキシ
```

### コンテナ操作コマンド

```bash
# 起動
docker-compose up -d

# ログ確認
docker-compose logs -f detective-api

# 停止・削除
docker-compose down -v

# 再ビルド
docker-compose up --build
```

## 🚨 トラブルシューティング

### よくある問題と解決方法

#### 1. ポート競合エラー

```bash
# 使用中ポートの確認
lsof -i :8000

# プロセス終了
kill -9 <PID>

# または別ポート使用
docker-compose up -e PORT=8001
```

#### 2. API キーエラー

```bash
# 環境変数確認
source .env
echo $GEMINI_API_KEY

# モックモード切り替え
export USE_MOCK_DATA=true
```

#### 3. Dockerエラー

```bash
# Docker再起動
sudo systemctl restart docker

# イメージ再ビルド
docker-compose build --no-cache

# ボリューム削除
docker-compose down -v
```

#### 4. Firestore接続エラー

```bash
# エミュレーター状態確認
curl http://localhost:8080

# 手動起動
gcloud emulators firestore start --host-port=0.0.0.0:8080
```

## 🎯 開発ワークフロー

### 1. 機能開発

```bash
# 1. 環境起動
./local-dev.sh

# 2. コード編集
vim backend/src/api/routes/game.py

# 3. 自動リロード確認
# → ファイル保存で即座に反映

# 4. テスト実行
python test-local.py

# 5. 手動テスト
curl http://localhost:8000/api/v1/game/start
```

### 2. デバッグ

```bash
# ログ監視
docker-compose logs -f detective-api

# コンテナ内アクセス
docker-compose exec detective-api bash

# Python デバッガー
import pdb; pdb.set_trace()
```

### 3. データ確認

```bash
# Firestore UI でデータ確認
open http://localhost:4000

# API経由でデータ確認
curl http://localhost:8000/api/v1/game/{game_id}
```

## 📊 パフォーマンス監視

### リソース使用量確認

```bash
# Docker統計情報
docker stats

# APIレスポンス時間測定
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health
```

### ベンチマーク

```bash
# 同時接続テスト
ab -n 100 -c 10 http://localhost:8000/health

# ゲーム作成負荷テスト
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/game/start \
    -H "Content-Type: application/json" \
    -d '{"player_id":"test'$i'","location":{"lat":35.6762,"lng":139.6503},"difficulty":"easy"}' &
done
```

## 🔒 セキュリティ注意事項

- ✅ `.env`ファイルはGitで管理されません
- ✅ 開発環境でのみデバッグ情報を表示
- ⚠️ 本番APIキーをローカルで使用しない
- ⚠️ Fireteoreエミュレーターのデータは永続化されません
- ⚠️ ローカル環境は外部からアクセス不可

## 🎉 次のステップ

ローカル環境が正常に動作したら：

1. **Flutter アプリ開発** - モバイルアプリの実装開始
2. **本番デプロイ** - `./deploy.sh`でGoogle Cloudにデプロイ
3. **機能拡張** - 新しいAPIエンドポイントや機能の追加
4. **テスト追加** - より包括的なテストスイート作成

## 📚 関連ドキュメント

- [システム設計書](docs/system-design.md)
- [API仕様書](docs/api-spec.md) 
- [MVP実装プラン](docs/mvp-implementation-plan.md)
- [ローカル開発詳細ガイド](docs/local-development.md)

---

**🚀 これで完全なローカル開発環境が整いました！**  
**Google Cloudの全機能をローカルでテスト・開発できます。**