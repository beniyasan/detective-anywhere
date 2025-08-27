# テスト構造

このディレクトリには、Detective Anywhereプロジェクトのテストファイルが整理されています。

## 📁 ディレクトリ構造

```
tests/
├── api/              # APIエンドポイントのテスト
├── integration/      # 外部サービスとの統合テスト
├── unit/            # 単体テスト（個別機能のテスト）
├── e2e/             # エンドツーエンドテスト（完全なユーザーフロー）
├── fixtures/        # テストデータとデモファイル
└── README.md        # このファイル
```

## 📂 各ディレクトリの説明

### `/api` - APIテスト
FastAPI エンドポイントの動作確認
- `test_api_workflow.py` - API ワークフローテスト
- `test_evidence_discovery_api.py` - 証拠発見API
- `test_evidence_discovery_detailed.py` - 証拠発見詳細テスト
- `test-integrated-api.py` - 統合APIテスト
- `test-real-api-keys.py` - 実際のAPIキーでのテスト
- `test-api-keys-only.py` - APIキーのみのテスト

### `/integration` - 統合テスト
外部サービス（Firestore、Google Maps、Gemini API等）との連携テスト
- `test-firestore-integration.py` - Firestore統合
- `test-firestore-simple.py` - Firestore基本機能
- `test_firestore_real.py` - 実Firestore環境テスト
- `test_evidence_discovery_integration.py` - 証拠発見統合テスト
- `test_database_integration.py` - データベース統合テスト
- `test-gemini-integration.py` - Gemini API統合
- `test-google-maps.py` - Google Maps API統合
- `test-google-maps-simple.py` - Google Maps基本テスト

### `/unit` - 単体テスト
個別機能・コンポーネントのテスト
- `test-gps-validation.py` - GPS検証機能
- `test-enhanced-poi.py` - 拡張POI機能
- `test-development-secrets.py` - 開発環境シークレット
- `test-production-config.py` - 本番環境設定
- `test-evidence-discovery-complete.py` - 証拠発見完全テスト
- `test_evidence_backend.py` - バックエンド証拠処理

### `/e2e` - エンドツーエンドテスト
実際のユーザー体験に近い完全なフローテスト
- `test-center-kita-game.py` - センター北でのゲーム
- `test-center-kita-custom-scenario.py` - センター北カスタムシナリオ
- `test-shin-yokohama.py` - 新横浜エリアテスト
- `test-custom-location.py` - カスタム場所テスト
- `test-local.py` - ローカル環境テスト

### `/fixtures` - テストデータ・デモ
テスト用のサンプルデータとデモンストレーション
- `demo_evidence_discovery.py` - 証拠発見デモ
- `demo_firestore_integration.py` - Firestore統合デモ

## 🚀 テスト実行方法

### 全テスト実行
```bash
# プロジェクトルートから
python -m pytest tests/
```

### カテゴリ別実行
```bash
# APIテストのみ
python -m pytest tests/api/

# 統合テストのみ
python -m pytest tests/integration/

# 単体テストのみ
python -m pytest tests/unit/

# E2Eテストのみ
python -m pytest tests/e2e/
```

### 個別テスト実行
```bash
# 特定のテストファイル
python tests/api/test_api_workflow.py

# デモ実行
python tests/fixtures/demo_evidence_discovery.py
```

## ⚙️ テスト環境設定

### 必要な環境変数
```bash
# .env ファイルに設定
GOOGLE_MAPS_API_KEY=your_key
GEMINI_API_KEY=your_key
FIRESTORE_PROJECT_ID=your_project
```

### 開発用設定
```bash
# ローカル開発用
ENV=development

# テスト用Firestore エミュレーター
FIRESTORE_EMULATOR_HOST=localhost:8080
```

## 📝 テスト作成ガイドライン

1. **命名規則**: `test_` または `test-` で開始
2. **場所**: 機能に応じて適切なディレクトリに配置
3. **依存関係**: 外部サービスを使用する場合は `/integration` に
4. **モック**: 単体テストでは外部依存をモック化
5. **ドキュメント**: 複雑なテストはコメントで説明

## 🔍 トラブルシューティング

### よくある問題
- **APIキーエラー**: `.env` ファイルの設定を確認
- **Firestore接続エラー**: エミュレーターまたは認証情報を確認
- **インポートエラー**: `PYTHONPATH` の設定を確認

### ログ確認
```bash
# 詳細ログでテスト実行
python -m pytest tests/ -v -s
```