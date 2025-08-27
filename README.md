# AIミステリー散歩 (AI Mystery Walk)

日常の散歩や通勤を、AIが即興で生成するミステリー体験に変えるゲームアプリ

## 🎯 概要

ユーザーがスマホを持って歩くだけで、AIが舞台設定・事件・容疑者・証拠を生成。実際のGPS情報をもとに、証拠が配置された場所に行くと発見イベントが発生し、最後にプレイヤーは「犯人は誰か」を推理するGPS連動ミステリーゲームです。

## 🌟 実装済み機能

### Phase 1: コア機能
- ✅ **AIシナリオ生成**: Gemini APIによる動的なミステリーシナリオ生成
- ✅ **GPS連動証拠発見**: 実際の位置情報に基づく証拠発見システム
- ✅ **推理・判定システム**: AIによる推理判定とキャラクター反応生成
- ✅ **Firestore統合**: リアルタイムデータベース連携
- ✅ **PWA対応**: モバイル・デスクトップ両対応のWebアプリ
- ✅ **統一設定管理**: 環境別設定の中央管理
- ✅ **構造化ログ**: 本格的なログ管理システム

### リアルタイム機能
- ✅ **GPS精度検証**: 実際のGPS精度に基づく適応的発見半径
- ✅ **位置偽装検出**: GPS spoofing検出機能
- ✅ **動的POI検索**: Google Maps API統合による実在POI活用
- ✅ **証拠配置最適化**: 地理的制約を考慮した証拠配置

## 🔑 主要機能

### 🎭 AIシナリオ生成
- **動的生成**: ユーザーの現在地に基づいたオリジナルミステリー
- **複雑な設定**: 被害者・容疑者（3〜8名）・関係性・証拠をAIが生成
- **難易度調整**: Easy/Normal/Hardによる複雑さとボリューム調整
- **ドラマチック演出**: 短編小説レベルの導入文・発見時の描写

### 📍 GPS連動証拠発見
- **実在POI活用**: Google Maps APIから実際のランドマーク・カフェ・公園を取得
- **適応的発見半径**: GPS精度に応じた動的な発見範囲調整
- **証拠配置戦略**: 徒歩圏内で適切に分散された証拠配置
- **リアルタイム検証**: 実際の移動パターンを考慮した検証

### 🕵️ 推理・判定システム
- **自由入力推理**: プレイヤーは犯人名と推理根拠を入力
- **AI判定**: Gemini APIによる推理の正誤判定
- **キャラクター反応**: 各容疑者の性格に応じた動的反応生成
- **結果フィードバック**: 詳細な解説と得点システム

## 🛠️ 技術構成

### バックエンド
- **FastAPI**: 高性能Web API フレームワーク
- **Google Cloud Run**: サーバーレス実行環境
- **Gemini 2.0 Flash**: AIシナリオ生成エンジン
- **Cloud Firestore**: NoSQLリアルタイムデータベース
- **Google Maps API**: POI検索・位置情報サービス

### フロントエンド
- **PWA**: プログレッシブWebアプリ
- **モバイルファースト**: レスポンシブデザイン
- **Service Worker**: オフライン対応
- **Web Manifest**: ネイティブアプリ風体験

### 開発・運用
- **構造化ログ**: JSON形式ログでモニタリング
- **統一設定管理**: 環境別設定の中央管理
- **型ヒント**: Python型アノテーション完備
- **包括的テスト**: 単体・統合・E2Eテスト体制

### アーキテクチャ
```
[PWA Client] ←→ [Cloud Run API] ←→ [Gemini 2.0 Flash]
     ↓              ↓                     ↓
[GPS Service] [Cloud Firestore]    [Vertex AI]
     ↓              ↓
[Maps API]   [Secret Manager]
```

## 📂 プロジェクト構造

```
detective-anywhere/
├── backend/                    # FastAPI バックエンド
│   ├── src/
│   │   ├── api/               # API ルーター
│   │   │   ├── routes/        # エンドポイント定義
│   │   │   └── errors.py      # 統一エラーハンドリング
│   │   ├── services/          # ビジネスロジック
│   │   │   ├── ai_service.py      # Gemini API連携
│   │   │   ├── game_service.py    # ゲームロジック
│   │   │   ├── gps_service.py     # GPS検証
│   │   │   ├── poi_service.py     # POI管理
│   │   │   └── database_service.py # DB操作
│   │   ├── core/              # 共通機能
│   │   │   ├── logging.py     # 構造化ログ
│   │   │   └── database.py    # DB接続
│   │   ├── config/            # 設定管理
│   │   │   ├── settings.py    # 統一設定
│   │   │   └── secrets.py     # シークレット管理
│   │   └── main.py           # アプリケーションエントリー
│   ├── TYPE_HINTS_DOCUMENTATION.md # 型ヒント文書
│   └── requirements.txt       # Python依存関係
├── shared/                    # 共通データモデル
│   └── models/               # Pydanticモデル定義
├── tests/                    # テストスイート
│   ├── api/                  # APIテスト
│   ├── unit/                 # 単体テスト
│   ├── integration/          # 統合テスト
│   └── e2e/                  # E2Eテスト
├── mobile-app.html           # PWA メインアプリ
├── web-demo.html            # Webデモ版
├── manifest.json            # PWA設定
├── service-worker.js        # Service Worker
├── Dockerfile               # Docker設定
├── cloudbuild.yaml          # CI/CD設定
└── README_DEPLOYMENT.md     # デプロイ手順
```

## 🚀 セットアップ & 実行

### 1. 前提条件
- Python 3.11+
- Google Cloud プロジェクト
- 必要なAPI有効化:
  - Gemini API
  - Google Maps API
  - Cloud Firestore
  - Secret Manager

### 2. 開発環境構築

```bash
# リポジトリクローン
git clone https://github.com/beniyasan/detective-anywhere.git
cd detective-anywhere

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 3. 実行方法

#### ローカル開発
```bash
# バックエンド起動
python -m uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# PWAアプリアクセス
# http://localhost:8000/mobile-app.html
```

#### Docker実行
```bash
# Docker ビルド & 実行
docker build -t detective-anywhere .
docker run -p 8000:8000 detective-anywhere
```

#### Cloud Run デプロイ
```bash
# Google Cloud SDK認証
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Cloud Run デプロイ
gcloud builds submit --config cloudbuild.yaml
```

## 🎮 使用方法

1. **ゲーム開始**: モバイルアプリで「新しいゲームを開始」
2. **シナリオ生成**: 現在地周辺でAIがミステリーを生成
3. **証拠探索**: 地図上のマーカーに向かって実際に移動
4. **証拠発見**: 対象地点に到達すると証拠が解放
5. **推理**: 全証拠収集後、犯人を推理して回答
6. **結果**: AIが推理を判定し、キャラクターが反応

## 🧪 テスト

```bash
# 全テスト実行
pytest tests/

# カテゴリ別実行
pytest tests/unit/          # 単体テスト
pytest tests/integration/   # 統合テスト
pytest tests/api/          # APIテスト
```

## 📊 監視・ログ

- **構造化ログ**: JSON形式でCloud Loggingに出力
- **ヘルスチェック**: `/health` エンドポイントで状態確認
- **メトリクス**: ゲーム進行・API使用量・エラー率を監視

## 🔒 セキュリティ

- **Secret Manager**: APIキーの安全な管理
- **GPS偽装検出**: 位置情報の信頼性検証
- **入力検証**: 全APIエンドポイントでバリデーション
- **レート制限**: API使用量制限機能

## 🛣️ ロードマップ

### Phase 2 (次期予定)
- [ ] **マルチプレイ機能**: 協力・競争モード
- [ ] **カスタムシナリオ**: ユーザー作成シナリオ
- [ ] **AR連携**: カメラを使った証拠発見演出
- [ ] **音声対応**: TTS/STTによる音声体験

### Phase 3 (将来予定)
- [ ] **ソーシャル機能**: フレンド・ランキング
- [ ] **詳細分析**: プレイパターン解析
- [ ] **国際対応**: 多言語・海外POI対応
- [ ] **VR対応**: 没入型ミステリー体験

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

プルリクエスト・Issue報告を歓迎します！開発に参加する際は、まずIssueで議論してからPRを作成してください。

## 📬 サポート

- **GitHub Issues**: バグ報告・機能要望
- **Wiki**: 詳細な技術文書
- **Discussions**: 質問・アイデア交換

---

**現在のバージョン**: 1.0.0  
**最終更新**: 2025年1月