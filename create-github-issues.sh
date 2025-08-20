#!/bin/bash
# GitHub Issues 自動作成スクリプト

# GitHub CLIがインストールされているか確認
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) がインストールされていません。"
    echo "インストール: https://cli.github.com/"
    exit 1
fi

# リポジトリ情報
REPO="beniyasan/detective-anywhere"

echo "🚀 GitHub Issues を作成中..."

# Issue #1: Critical - API Keys
gh issue create \
  --repo $REPO \
  --title "[P0] Setup production API keys for Google Cloud services" \
  --body "## 概要
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
- https://console.cloud.google.com/apis/credentials" \
  --label "critical,backend,configuration"

# Issue #2: Critical - Flutter App
gh issue create \
  --repo $REPO \
  --title "[P0] Implement Flutter mobile application MVP" \
  --body "## 概要
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
2週間以内" \
  --label "critical,mobile,feature"

# Issue #3: High - Gemini API
gh issue create \
  --repo $REPO \
  --title "[P1] Integrate real Gemini API for scenario generation" \
  --body "## 概要
モックデータからGemini APIへの切り替え

## タスク
- [ ] AIサービスクラスの完全実装
- [ ] プロンプトエンジニアリング最適化
- [ ] エラーハンドリング強化
- [ ] レート制限対応

## ファイル
- backend/src/services/ai_service.py" \
  --label "high,backend,ai"

# Issue #4: High - Firestore
gh issue create \
  --repo $REPO \
  --title "[P1] Implement Firestore database integration" \
  --body "## 概要
Firestoreを使用したデータ永続化

## タスク
- [ ] Firestore初期設定
- [ ] データモデルのマッピング
- [ ] CRUD操作の実装
- [ ] インデックス設定

## 影響範囲
- ゲームセッション管理
- プレイヤー履歴保存
- ランキング機能" \
  --label "high,backend,database"

# Issue #5: High - Evidence Discovery
gh issue create \
  --repo $REPO \
  --title "[P1] Complete evidence discovery feature with GPS validation" \
  --body "## 概要
GPS座標による証拠発見機能の実装

## タスク
- [ ] 距離計算アルゴリズムの改善
- [ ] 発見判定ロジック
- [ ] 発見時のイベント処理
- [ ] ヒント機能実装

## エンドポイント
- POST /api/v1/evidence/discover
- GET /api/v1/evidence/{id}/hint" \
  --label "high,backend,feature"

# Issue #6: Medium - Google Maps
gh issue create \
  --repo $REPO \
  --title "[P2] Integrate Google Maps API for real POI data" \
  --body "## 概要
実際のPOIデータ取得のためのGoogle Maps API統合

## タスク
- [ ] Places API設定
- [ ] リアルタイムPOI検索
- [ ] キャッシュ戦略実装
- [ ] 料金最適化

## ファイル
- backend/src/services/poi_service.py" \
  --label "medium,backend,maps"

# Issue #7: Medium - Deduction System
gh issue create \
  --repo $REPO \
  --title "[P2] Improve deduction judgment system" \
  --body "## 概要
推理判定とキャラクター反応生成の改善

## タスク
- [ ] 自由入力の犯人名判定
- [ ] 部分一致対応
- [ ] 複数のエンディングパターン
- [ ] キャラクター反応のバリエーション増加" \
  --label "medium,backend,feature"

# Issue #8: Medium - Authentication
gh issue create \
  --repo $REPO \
  --title "[P2] Implement user authentication" \
  --body "## 概要
Firebase Authenticationを使用したユーザー認証

## タスク
- [ ] Firebase Auth設定
- [ ] JWT トークン検証
- [ ] ゲストモード実装
- [ ] ソーシャルログイン（オプション）" \
  --label "medium,backend,security"

# Issue #9: Bug - Pydantic
gh issue create \
  --repo $REPO \
  --title "[Bug] Fix Pydantic v2 deprecation warnings" \
  --body "## 概要
Pydantic v2の非推奨メソッド使用による警告

## 修正箇所
- backend/src/main_minimal.py:266
- .dict() → .model_dump() に変更

## 影響
軽微（警告のみ、動作に影響なし）" \
  --label "bug,backend,low"

# Issue #10: Performance
gh issue create \
  --repo $REPO \
  --title "[Performance] Optimize API response times" \
  --body "## 概要
APIレスポンス時間の改善

## タスク
- [ ] データベースクエリ最適化
- [ ] キャッシュ戦略改善
- [ ] 非同期処理の活用
- [ ] CDN設定" \
  --label "performance,medium"

echo "✅ GitHub Issues の作成が完了しました！"
echo "確認: https://github.com/$REPO/issues"