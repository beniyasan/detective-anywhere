# AIミステリー散歩 - Flutter Mobile App

GPS連動のAI生成ミステリーゲームのFlutterアプリケーション

## 概要

このアプリは、現在地を中心としたミステリーゲームを提供します。AIが生成するシナリオの中で、GPSを使って実際に歩き回りながら証拠を発見し、推理で事件を解決するゲームです。

## 主な機能

### 📱 実装済み画面

1. **ホーム画面** (`lib/screens/home_screen.dart`)
   - GPS許可の確認と取得
   - 難易度選択（簡単・普通・難しい）
   - ゲーム開始機能

2. **シナリオ表示画面** (`lib/screens/scenario_screen.dart`)
   - ミステリーのあらすじ表示
   - 被害者情報の表示
   - 容疑者一覧の表示

3. **探索マップ画面** (`lib/screens/exploration_screen.dart`)
   - Google Mapsによる現在地表示
   - 証拠マーカーの表示
   - 証拠発見状況の進捗表示
   - 証拠一覧（ドラッグ可能なボトムシート）

4. **証拠発見画面** (`lib/screens/evidence_screen.dart`)
   - 証拠詳細の表示
   - GPS距離による発見判定
   - 証拠調査機能

5. **推理入力画面** (`lib/screens/deduction_screen.dart`)
   - 発見済み証拠の確認
   - 容疑者選択
   - 推理根拠の入力

6. **結果表示画面** (`lib/screens/result_screen.dart`)
   - 推理結果の表示（正解・不正解）
   - 真相の解説
   - ゲーム統計とスコア

### 🏗️ アーキテクチャ

- **状態管理**: Provider パターン
- **API通信**: Dio
- **GPS機能**: geolocator + permission_handler
- **マップ**: google_maps_flutter

### 📁 プロジェクト構造

```
lib/
├── main.dart                 # アプリエントリーポイント
├── models/                   # データモデル
│   └── game_models.dart     # ゲーム関連モデル
├── providers/               # 状態管理
│   ├── game_provider.dart   # ゲーム状態管理
│   └── location_provider.dart # 位置情報管理
├── screens/                 # 画面
│   ├── home_screen.dart
│   ├── scenario_screen.dart
│   ├── exploration_screen.dart
│   ├── evidence_screen.dart
│   ├── deduction_screen.dart
│   └── result_screen.dart
├── services/                # API通信
│   └── api_service.dart
└── utils/                   # ユーティリティ
    └── theme.dart          # アプリテーマ
```

## セットアップ

### 1. 必要な環境

- Flutter 3.10.0+
- Dart 3.0.0+
- Android Studio または VS Code
- Google Maps API Key

### 2. 依存関係のインストール

```bash
cd mobile
flutter pub get
```

### 3. Google Maps API Keyの設定

1. Google Cloud Consoleで Maps SDK for Android を有効化
2. `android/app/src/main/AndroidManifest.xml` の `YOUR_GOOGLE_MAPS_API_KEY` を実際のAPIキーに置き換え

### 4. 実行

```bash
# デバッグモードで実行
flutter run

# リリースモードで実行
flutter run --release
```

## API連携

### バックエンドAPI

- **ベースURL**: `http://10.0.2.2:8000` (Android エミュレータ用)
- **実機の場合**: `http://[開発マシンのIP]:8000`

### 主要エンドポイント

- `GET /health` - ヘルスチェック
- `GET /api/v1/poi/nearby` - 周辺POI検索
- `POST /api/v1/poi/validate-area` - ゲーム作成可能エリア検証
- `POST /api/v1/game/start` - ゲーム開始
- `GET /api/v1/game/{game_id}` - ゲーム状態取得
- `POST /api/v1/evidence/discover` - 証拠発見
- `POST /api/v1/deduction/submit` - 推理提出

## 機能詳細

### GPS機能
- 現在位置の取得と継続監視
- 証拠発見範囲の判定（デフォルト: 50m）
- 位置情報権限の適切な管理

### ゲームフロー
1. GPS許可と現在位置取得
2. 難易度選択してゲーム作成
3. シナリオ確認
4. マップで証拠を探索
5. 証拠発見（GPS範囲内で調査）
6. 推理提出
7. 結果表示とスコア算出

### 状態管理
- **GameProvider**: ゲーム状態、証拠管理
- **LocationProvider**: 位置情報管理、権限管理

## 今後の拡張予定

- [ ] プッシュ通知（証拠発見時など）
- [ ] ゲーム履歴の保存
- [ ] ソーシャル機能（スコア共有）
- [ ] 多言語対応
- [ ] オフラインモード対応

## トラブルシューティング

### よくある問題

1. **位置情報が取得できない**
   - Android設定で位置情報が有効になっているか確認
   - アプリの位置情報権限が許可されているか確認

2. **Google Mapが表示されない**
   - Google Maps API Keyが正しく設定されているか確認
   - Maps SDK for Android が有効になっているか確認

3. **API通信エラー**
   - バックエンドサーバーが起動しているか確認
   - IPアドレスが正しく設定されているか確認

## ライセンス

このプロジェクトはAIミステリー散歩プロジェクトの一部です。