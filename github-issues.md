# GitHub Issues - AIミステリー散歩

## 🔴 優先度: Critical (P0) - 即座に対応必要

### Issue #1: Google Cloud APIキーの本番環境設定
**タイトル**: [P0] Setup production API keys for Google Cloud services
**ラベル**: `critical`, `backend`, `configuration`
**内容**:
```markdown
## 概要
本番環境で必要なAPIキーの取得と設定

## タスク
- [ ] Gemini API キーの取得
- [ ] Google Maps API キーの取得
- [ ] Google Cloud プロジェクトの作成
- [ ] Secret Managerへのキー登録

## 影響範囲
- シナリオ生成機能
- POI検索機能
- 全体的なゲーム動作

## 参考
- https://aistudio.google.com/app/apikey
- https://console.cloud.google.com/apis/credentials
```

### Issue #2: Flutter モバイルアプリの基本実装
**タイトル**: [P0] Implement Flutter mobile application MVP
**ラベル**: `critical`, `mobile`, `feature`
**内容**:
```markdown
## 概要
Flutterを使用したモバイルアプリのMVP実装

## 必須画面
- [ ] ホーム画面（GPS許可・ゲーム開始）
- [ ] シナリオ表示画面
- [ ] 探索マップ画面
- [ ] 証拠発見画面
- [ ] 推理入力画面
- [ ] 結果表示画面

## 技術要件
- Flutter 3.x
- geolocator package
- dio package for API通信
- Provider/Riverpod for状態管理

## 期限
2週間以内
```

## 🟠 優先度: High (P1) - 数日以内に対応

### Issue #3: 実際のGemini API統合
**タイトル**: [P1] Integrate real Gemini API for scenario generation
**ラベル**: `high`, `backend`, `ai`
**内容**:
```markdown
## 概要
モックデータからGemini APIへの切り替え

## タスク
- [ ] AIサービスクラスの完全実装
- [ ] プロンプトエンジニアリング最適化
- [ ] エラーハンドリング強化
- [ ] レート制限対応

## ファイル
- backend/src/services/ai_service.py
```

### Issue #4: Firestore データベース実装
**タイトル**: [P1] Implement Firestore database integration
**ラベル**: `high`, `backend`, `database`
**内容**:
```markdown
## 概要
Firestoreを使用したデータ永続化

## タスク
- [ ] Firestore初期設定
- [ ] データモデルのマッピング
- [ ] CRUD操作の実装
- [ ] インデックス設定

## 影響範囲
- ゲームセッション管理
- プレイヤー履歴保存
- ランキング機能
```

### Issue #5: 証拠発見機能の完全実装
**タイトル**: [P1] Complete evidence discovery feature with GPS validation
**ラベル**: `high`, `backend`, `feature`
**内容**:
```markdown
## 概要
GPS座標による証拠発見機能の実装

## タスク
- [ ] 距離計算アルゴリズムの改善
- [ ] 発見判定ロジック
- [ ] 発見時のイベント処理
- [ ] ヒント機能実装

## エンドポイント
- POST /api/v1/evidence/discover
- GET /api/v1/evidence/{id}/hint
```

## 🟡 優先度: Medium (P2) - 1週間以内に対応

### Issue #6: Google Maps API統合
**タイトル**: [P2] Integrate Google Maps API for real POI data
**ラベル**: `medium`, `backend`, `maps`
**内容**:
```markdown
## 概要
実際のPOIデータ取得のためのGoogle Maps API統合

## タスク
- [ ] Places API設定
- [ ] リアルタイムPOI検索
- [ ] キャッシュ戦略実装
- [ ] 料金最適化

## ファイル
- backend/src/services/poi_service.py
```

### Issue #7: 推理判定システムの改善
**タイトル**: [P2] Improve deduction judgment system
**ラベル**: `medium`, `backend`, `feature`
**内容**:
```markdown
## 概要
推理判定とキャラクター反応生成の改善

## タスク
- [ ] 自由入力の犯人名判定
- [ ] 部分一致対応
- [ ] 複数のエンディングパターン
- [ ] キャラクター反応のバリエーション増加
```

### Issue #8: ユーザー認証システム
**タイトル**: [P2] Implement user authentication
**ラベル**: `medium`, `backend`, `security`
**内容**:
```markdown
## 概要
Firebase Authenticationを使用したユーザー認証

## タスク
- [ ] Firebase Auth設定
- [ ] JWT トークン検証
- [ ] ゲストモード実装
- [ ] ソーシャルログイン（オプション）
```

### Issue #9: エラーハンドリング強化
**タイトル**: [P2] Enhance error handling across the application
**ラベル**: `medium`, `backend`, `quality`
**内容**:
```markdown
## 概要
包括的なエラーハンドリングの実装

## タスク
- [ ] カスタム例外クラス作成
- [ ] エラーログ記録
- [ ] ユーザーフレンドリーなエラーメッセージ
- [ ] リトライロジック
```

## 🟢 優先度: Low (P3) - 2週間以降

### Issue #10: ランキング・統計機能
**タイトル**: [P3] Add ranking and statistics features
**ラベル**: `low`, `feature`, `enhancement`
**内容**:
```markdown
## 概要
プレイヤーランキングと統計機能の追加

## タスク
- [ ] スコア計算アルゴリズム改善
- [ ] 週間/月間ランキング
- [ ] 個人統計ダッシュボード
- [ ] 実績システム
```

### Issue #11: 難易度モード拡張
**タイトル**: [P3] Expand difficulty modes and customization
**ラベル**: `low`, `feature`, `enhancement`
**内容**:
```markdown
## 概要
難易度モードの拡張とカスタマイズ

## タスク
- [ ] Normal/Hardモード実装
- [ ] カスタム難易度設定
- [ ] 時間制限モード
- [ ] ヒント制限モード
```

### Issue #12: 音声・効果音機能
**タイトル**: [P3] Add audio and sound effects
**ラベル**: `low`, `mobile`, `enhancement`
**内容**:
```markdown
## 概要
音声合成と効果音の追加

## タスク
- [ ] TTS（Text-to-Speech）統合
- [ ] BGM実装
- [ ] 効果音ライブラリ
- [ ] ボリューム設定
```

## 🐛 バグ修正

### Issue #13: Pydantic deprecation警告の修正
**タイトル**: [Bug] Fix Pydantic v2 deprecation warnings
**ラベル**: `bug`, `backend`, `low`
**内容**:
```markdown
## 概要
Pydantic v2の非推奨メソッド使用による警告

## 修正箇所
- backend/src/main_minimal.py:266
- .dict() → .model_dump() に変更

## 影響
軽微（警告のみ、動作に影響なし）
```

### Issue #14: requirements.txtの依存関係修正
**タイトル**: [Bug] Fix dependency issues in requirements.txt
**ラベル**: `bug`, `backend`, `medium`
**内容**:
```markdown
## 概要
Python 3.13との互換性問題

## 修正内容
- googlemaps packageバージョン修正済み
- pydantic-coreビルド問題の対応
- 最小要件ファイルの作成

## ファイル
- backend/requirements.txt
- backend/requirements-minimal.txt
```

## 📝 ドキュメント

### Issue #15: API ドキュメントの充実
**タイトル**: [Docs] Enhance API documentation
**ラベル**: `documentation`, `low`
**内容**:
```markdown
## 概要
API仕様書とサンプルコードの追加

## タスク
- [ ] OpenAPI仕様の完全化
- [ ] サンプルリクエスト/レスポンス追加
- [ ] エラーコード一覧の整理
- [ ] 使用例の追加
```

### Issue #16: デプロイメントガイド作成
**タイトル**: [Docs] Create comprehensive deployment guide
**ラベル**: `documentation`, `medium`
**内容**:
```markdown
## 概要
本番環境へのデプロイ手順書作成

## 内容
- [ ] Google Cloud設定手順
- [ ] CI/CDパイプライン設定
- [ ] 環境変数設定ガイド
- [ ] トラブルシューティング
```

## 🔄 継続的改善

### Issue #17: パフォーマンス最適化
**タイトル**: [Performance] Optimize API response times
**ラベル**: `performance`, `medium`
**内容**:
```markdown
## 概要
APIレスポンス時間の改善

## タスク
- [ ] データベースクエリ最適化
- [ ] キャッシュ戦略改善
- [ ] 非同期処理の活用
- [ ] CDN設定
```

### Issue #18: テストカバレッジ向上
**タイトル**: [Test] Increase test coverage to 80%
**ラベル**: `testing`, `quality`, `medium`
**内容**:
```markdown
## 概要
単体テスト・統合テストの追加

## タスク
- [ ] バックエンドAPI単体テスト
- [ ] サービスクラステスト
- [ ] E2Eテスト
- [ ] CI/CDへのテスト統合

## 目標
カバレッジ80%以上
```