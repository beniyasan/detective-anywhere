# API仕様書 - AIミステリー散歩

## ベースURL
- 開発環境: `http://localhost:8000/api/v1`
- 本番環境: `https://detective-anywhere.run.app/api/v1`

## 認証
- ヘッダー: `Authorization: Bearer {token}`
- プレイヤーIDベースの簡易認証

## エンドポイント一覧

### 1. ゲーム開始
```http
POST /game/start
```

**説明**: 新しいミステリーゲームセッションを開始し、現在地周辺のPOIを使用してシナリオを生成

**リクエスト**:
```json
{
  "playerId": "string",
  "location": {
    "lat": 35.6762,
    "lng": 139.6503
  },
  "difficulty": "easy|normal|hard"
}
```

**レスポンス**:
```json
{
  "gameId": "uuid",
  "scenario": {
    "title": "string",
    "description": "string",
    "suspects": [
      {
        "name": "string",
        "age": 28,
        "occupation": "string",
        "personality": "string",
        "relationship": "string"
      }
    ]
  },
  "evidence": [
    {
      "evidenceId": "uuid",
      "name": "string",
      "description": "string",
      "location": {
        "lat": 35.6762,
        "lng": 139.6503,
        "poiName": "string",
        "poiType": "restaurant|park|landmark|cafe|station"
      }
    }
  ],
  "gameRules": {
    "discoveryRadius": 50,
    "timeLimit": null,
    "maxEvidence": 5
  }
}
```

### 2. ゲーム状態取得
```http
GET /game/{gameId}
```

**説明**: 進行中のゲームセッションの状態を取得

**パラメータ**:
- `gameId`: ゲームセッションID

**レスポンス**:
```json
{
  "gameId": "uuid",
  "status": "active|completed",
  "scenario": { /* Scenario object */ },
  "discoveredEvidence": ["evidenceId1", "evidenceId2"],
  "remainingEvidence": [
    { /* Evidence object */ }
  ],
  "progress": {
    "totalEvidence": 5,
    "discoveredCount": 2,
    "completionRate": 0.4
  }
}
```

### 3. 証拠発見
```http
POST /evidence/discover
```

**説明**: プレイヤーが特定の場所に到着したときに証拠を発見

**リクエスト**:
```json
{
  "gameId": "uuid",
  "playerId": "string",
  "currentLocation": {
    "lat": 35.6762,
    "lng": 139.6503
  },
  "evidenceId": "uuid"
}
```

**レスポンス**:
```json
{
  "success": true,
  "evidence": {
    "evidenceId": "uuid",
    "name": "string",
    "description": "string",
    "discoveryText": "string",
    "importance": "critical|important|misleading"
  },
  "distance": 23.5,
  "nextClue": "string?"
}
```

### 4. 推理回答提出
```http
POST /deduction/submit
```

**説明**: プレイヤーの推理（犯人予想）を判定し、キャラクターの反応を生成

**リクエスト**:
```json
{
  "gameId": "uuid",
  "playerId": "string",
  "suspectName": "string",
  "reasoning": "string?"
}
```

**レスポンス**:
```json
{
  "correct": true,
  "culprit": "string",
  "reactions": [
    {
      "character": "string",
      "reaction": "string",
      "type": "confession|denial|surprise|praise",
      "temperament": "calm|volatile|sarcastic|defensive|nervous"
    }
  ],
  "gameCompleted": true,
  "score": {
    "evidenceFound": 5,
    "totalEvidence": 5,
    "correctDeduction": true,
    "totalScore": 100
  }
}
```

### 5. POI検索
```http
GET /poi/nearby
```

**説明**: 指定座標周辺のPOI（興味のある場所）を取得

**クエリパラメータ**:
- `lat`: 緯度
- `lng`: 経度
- `radius`: 検索半径（メートル、デフォルト: 1000）
- `type`: POIタイプフィルター（オプション）

**レスポンス**:
```json
{
  "pois": [
    {
      "poiId": "string",
      "name": "string",
      "type": "restaurant|park|landmark|cafe|station",
      "location": {
        "lat": 35.6762,
        "lng": 139.6503
      },
      "address": "string",
      "distance": 150.5
    }
  ]
}
```

### 6. ゲーム履歴
```http
GET /player/{playerId}/games
```

**説明**: プレイヤーの過去のゲーム履歴を取得

**パラメータ**:
- `playerId`: プレイヤーID

**クエリパラメータ**:
- `limit`: 取得件数（デフォルト: 10）
- `offset`: オフセット（デフォルト: 0）

**レスポンス**:
```json
{
  "games": [
    {
      "gameId": "uuid",
      "title": "string",
      "completedAt": "2024-01-01T10:00:00Z",
      "score": 85,
      "difficulty": "normal",
      "location": "渋谷駅周辺"
    }
  ],
  "total": 25,
  "hasMore": true
}
```

## エラーレスポンス

すべてのエラーは以下の形式で返される：

```json
{
  "error": {
    "code": "INVALID_LOCATION",
    "message": "指定された位置情報が無効です",
    "details": {
      "field": "location.lat",
      "reason": "値が範囲外です"
    }
  }
}
```

### エラーコード一覧

| コード | HTTPステータス | 説明 |
|--------|----------------|------|
| `INVALID_REQUEST` | 400 | リクエスト形式が無効 |
| `INVALID_LOCATION` | 400 | 位置情報が無効 |
| `GAME_NOT_FOUND` | 404 | ゲームセッションが見つからない |
| `EVIDENCE_NOT_FOUND` | 404 | 証拠が見つからない |
| `TOO_FAR_FROM_EVIDENCE` | 400 | 証拠の場所から離れすぎている |
| `GAME_ALREADY_COMPLETED` | 409 | ゲームは既に完了している |
| `SCENARIO_GENERATION_FAILED` | 500 | AIシナリオ生成に失敗 |
| `EXTERNAL_API_ERROR` | 502 | 外部API（Google Maps等）エラー |

## レート制限

- 一般API: 100 requests/分/IP
- シナリオ生成: 10 requests/分/IP
- 証拠発見: 20 requests/分/プレイヤー

## WebSocket（将来拡張）

リアルタイム通知用のWebSocket接続：

```
wss://detective-anywhere.run.app/ws/{gameId}
```

**メッセージ形式**:
```json
{
  "type": "location_update|evidence_nearby|hint",
  "data": { /* Type-specific data */ }
}
```