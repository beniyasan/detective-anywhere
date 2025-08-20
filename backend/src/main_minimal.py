"""
AIミステリー散歩 - 最小テスト用メインアプリケーション
Google Cloud依存関係なしでローカルテスト
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random
import uuid
from datetime import datetime
import os

# 環境変数読み込み
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="AIミステリー散歩 API (テスト版)",
    description="ローカルテスト用の簡略版API",
    version="1.0.0-test"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データモデル
class Location(BaseModel):
    lat: float
    lng: float

class GameStartRequest(BaseModel):
    player_id: str
    location: Location
    difficulty: str

class Character(BaseModel):
    name: str
    age: int
    occupation: str
    personality: str
    temperament: str
    relationship: str
    alibi: Optional[str] = None
    motive: Optional[str] = None

class Scenario(BaseModel):
    title: str
    description: str
    victim: Character
    suspects: List[Character]
    culprit: str

class Evidence(BaseModel):
    evidence_id: str
    name: str
    description: str
    location: Location
    poi_name: str
    poi_type: str
    importance: str

class GameStartResponse(BaseModel):
    game_id: str
    scenario: Scenario
    evidence: List[Evidence]
    game_rules: Dict[str, Any]

# モックデータ
MOCK_SCENARIOS = [
    {
        "title": "カフェに響く悲鳴",
        "description": "午後3時、渋谷の人気カフェ『ブルーマウンテン』で女性の悲鳴が響いた。店内にいた常連客の田中太郎(45歳・会社員)が倒れており、救急車で運ばれたが既に息を引き取っていた。現場には不審な点が多く、警察は事件性が高いと判断。あなたは現場に居合わせた探偵として、この謎の解明を任された。",
        "victim": {
            "name": "田中太郎",
            "age": 45,
            "occupation": "会社員",
            "personality": "真面目で人当たりが良い",
            "temperament": "calm",
            "relationship": "被害者"
        },
        "suspects": [
            {
                "name": "佐藤花子",
                "age": 32,
                "occupation": "カフェ店員",
                "personality": "明るく社交的だが、時々感情的になる",
                "temperament": "volatile",
                "relationship": "被害者の担当店員",
                "alibi": "事件時はキッチンでコーヒーを淹れていた",
                "motive": "最近、田中から度々クレームを受けていた"
            },
            {
                "name": "山田次郎",
                "age": 28,
                "occupation": "IT企業勤務",
                "personality": "内向的で皮肉な言い回しを好む",
                "temperament": "sarcastic",
                "relationship": "同じテーブルにいた客",
                "alibi": "ノートパソコンで作業していた",
                "motive": "田中に仕事のプレゼンで恥をかかされた"
            },
            {
                "name": "鈴木美香",
                "age": 39,
                "occupation": "主婦",
                "personality": "気が弱く、人前で話すのが苦手",
                "temperament": "nervous",
                "relationship": "田中の元同僚",
                "alibi": "お手洗いに行っていた",
                "motive": "田中に昔の秘密を暴露されそうになっていた"
            }
        ],
        "culprit": "山田次郎"
    }
]

MOCK_POIS = [
    {"name": "東京タワー", "type": "landmark", "lat": 35.6586, "lng": 139.7454},
    {"name": "スターバックス 芝公園店", "type": "cafe", "lat": 35.6580, "lng": 139.7520},
    {"name": "芝公園", "type": "park", "lat": 35.6566, "lng": 139.7502},
    {"name": "コンビニエンスストア", "type": "shop", "lat": 35.6590, "lng": 139.7480},
    {"name": "地下鉄 神谷町駅", "type": "station", "lat": 35.6564, "lng": 139.7456},
    {"name": "カフェ ブルーマウンテン", "type": "cafe", "lat": 35.6575, "lng": 139.7490},
    {"name": "愛宕神社", "type": "landmark", "lat": 35.6603, "lng": 139.7461}
]

# ゲームセッションストレージ（メモリ内）
game_sessions = {}

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "AIミステリー散歩 API (テスト版)",
        "version": "1.0.0-test",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "firestore": "mocked",
            "gemini": "mocked"
        }
    }

@app.get("/api/v1/poi/nearby")
async def get_nearby_pois(lat: float, lng: float, radius: int = 1000, limit: int = 10):
    """周辺POI検索（モック）"""
    # 簡単な距離計算（実際は不正確だが、テスト用）
    pois_with_distance = []
    for poi in MOCK_POIS:
        # 簡略化した距離計算
        distance = abs(lat - poi["lat"]) + abs(lng - poi["lng"])
        distance_m = distance * 111000  # 大雑把な緯度経度→メートル変換
        
        if distance_m <= radius:
            pois_with_distance.append({
                "poi_id": f"mock_{poi['name'].replace(' ', '_')}",
                "name": poi["name"],
                "type": poi["type"],
                "location": {"lat": poi["lat"], "lng": poi["lng"]},
                "distance": round(distance_m, 1),
                "suitable_for_evidence": poi["type"] in ["cafe", "park", "landmark", "shop"]
            })
    
    # 距離でソート
    pois_with_distance.sort(key=lambda x: x["distance"])
    
    return {
        "pois": pois_with_distance[:limit],
        "center_location": {"lat": lat, "lng": lng},
        "search_radius": radius,
        "total_found": len(pois_with_distance)
    }

@app.post("/api/v1/poi/validate-area")
async def validate_game_area(lat: float, lng: float, radius: int = 1000):
    """ゲーム作成可能エリア検証（モック）"""
    # 東京タワー周辺かチェック
    tokyo_tower_lat, tokyo_tower_lng = 35.6586, 139.7454
    distance = abs(lat - tokyo_tower_lat) + abs(lng - tokyo_tower_lng)
    
    if distance < 0.01:  # 大雑把に東京タワー周辺
        return {
            "valid": True,
            "total_pois": len(MOCK_POIS),
            "suitable_pois": 5,
            "min_required_total": 5,
            "min_required_suitable": 3,
            "reason": "検証完了",
            "recommendations": ["この地域でゲームを作成できます"],
            "poi_types_available": ["landmark", "cafe", "park", "shop", "station"]
        }
    else:
        return {
            "valid": False,
            "total_pois": 2,
            "suitable_pois": 1,
            "reason": "POIが不足しています",
            "recommendations": ["東京タワー周辺に移動してください"]
        }

@app.post("/api/v1/game/start", response_model=GameStartResponse)
async def start_game(request: GameStartRequest):
    """ゲーム開始（モック）"""
    try:
        # ランダムにシナリオを選択
        scenario_data = random.choice(MOCK_SCENARIOS)
        
        # ゲームIDを生成
        game_id = str(uuid.uuid4())
        
        # シナリオオブジェクトを作成
        scenario = Scenario(
            title=scenario_data["title"],
            description=scenario_data["description"],
            victim=Character(**scenario_data["victim"]),
            suspects=[Character(**suspect) for suspect in scenario_data["suspects"]],
            culprit=scenario_data["culprit"]
        )
        
        # 証拠を生成（POIに配置）
        evidence_list = []
        selected_pois = random.sample(MOCK_POIS, min(5, len(MOCK_POIS)))
        
        evidence_templates = [
            {"name": "血のついたコーヒーカップ", "importance": "critical"},
            {"name": "謎のメモ", "importance": "important"},
            {"name": "目撃者の証言", "importance": "important"},
            {"name": "防犯カメラの映像", "importance": "critical"},
            {"name": "不審な領収書", "importance": "misleading"}
        ]
        
        for i, poi in enumerate(selected_pois):
            if i < len(evidence_templates):
                template = evidence_templates[i]
                evidence = Evidence(
                    evidence_id=f"evidence_{i+1}",
                    name=template["name"],
                    description="詳しい情報は現地で発見してください",
                    location=Location(lat=poi["lat"], lng=poi["lng"]),
                    poi_name=poi["name"],
                    poi_type=poi["type"],
                    importance=template["importance"]
                )
                evidence_list.append(evidence)
        
        # ゲームセッションを保存
        game_sessions[game_id] = {
            "game_id": game_id,
            "player_id": request.player_id,
            "scenario": scenario_data,
            "evidence": [ev.model_dump() for ev in evidence_list],
            "discovered_evidence": [],
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        return GameStartResponse(
            game_id=game_id,
            scenario=scenario,
            evidence=evidence_list,
            game_rules={
                "discovery_radius": 50.0,
                "time_limit": None,
                "max_evidence": len(evidence_list)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": {
                "code": "SCENARIO_GENERATION_FAILED",
                "message": "シナリオ生成に失敗しました",
                "details": str(e)
            }
        })

@app.get("/api/v1/game/{game_id}")
async def get_game_status(game_id: str):
    """ゲーム状態取得"""
    if game_id not in game_sessions:
        raise HTTPException(status_code=404, detail={
            "error": {
                "code": "GAME_NOT_FOUND",
                "message": "ゲームセッションが見つかりません"
            }
        })
    
    session = game_sessions[game_id]
    total_evidence = len(session["evidence"])
    discovered_count = len(session["discovered_evidence"])
    
    return {
        "game_id": game_id,
        "status": session["status"],
        "scenario": session["scenario"],
        "discovered_evidence": session["discovered_evidence"],
        "progress": {
            "total_evidence": total_evidence,
            "discovered_count": discovered_count,
            "completion_rate": discovered_count / total_evidence if total_evidence > 0 else 0,
            "time_elapsed": 0
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)