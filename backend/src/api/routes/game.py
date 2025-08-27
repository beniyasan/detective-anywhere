"""
ゲーム関連APIルーター
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from ...services.game_service import game_service
from shared.models.game import GameSession, GameStatus, Difficulty
from shared.models.location import Location
from shared.models.scenario import Scenario
from shared.models.evidence import Evidence


router = APIRouter()


# リクエスト/レスポンス モデル
class GameStartRequest(BaseModel):
    """ゲーム開始リクエスト"""
    player_id: str
    location: Location
    difficulty: Difficulty
    radius: Optional[int] = 1000  # 証拠検索半径（メートル）、デフォルト1km


class GameStartResponse(BaseModel):
    """ゲーム開始レスポンス"""
    game_id: str
    scenario: Scenario
    evidence: List[Dict[str, Any]]  # 段階的表示のため辞書形式に変更
    game_rules: dict
    
    class Config:
        json_encoders = {
            Difficulty: lambda v: v.value
        }


class GameStatusResponse(BaseModel):
    """ゲーム状態レスポンス"""
    game_id: str
    status: GameStatus
    scenario: Scenario
    discovered_evidence: List[str]
    remaining_evidence: List[Evidence]
    progress: dict
    
    class Config:
        json_encoders = {
            GameStatus: lambda v: v.value
        }


@router.post("/start", response_model=GameStartResponse)
async def start_game(request: GameStartRequest):
    """
    新しいミステリーゲームを開始
    
    - プレイヤーの現在地周辺のPOIを使用してシナリオを生成
    - 証拠をPOIに配置
    - ゲームセッションを作成
    """
    from ..errors import APIError, GameAPIError
    
    try:
        # 新しいゲームセッション開始（半径パラメータを追加）
        game_session = await game_service.start_new_game(
            player_id=request.player_id,
            player_location=request.location,
            difficulty=request.difficulty,
            radius=request.radius
        )
        
        return GameStartResponse(
            game_id=game_session.game_id,
            scenario=game_session.scenario,
            evidence=[
                ev.to_display_dict() for ev in game_session.evidence_list
            ],
            game_rules={
                "discovery_radius": game_session.game_rules.discovery_radius,
                "time_limit": game_session.game_rules.time_limit,
                "max_evidence": game_session.game_rules.max_evidence,
                "search_radius": request.radius  # 検索半径情報を追加
            }
        )
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise GameAPIError.scenario_generation_failed(details=str(e))


@router.get("/{game_id}", response_model=GameStatusResponse)
async def get_game_status(
    game_id: str = Path(..., description="ゲームセッションID")
):
    """
    ゲーム状態を取得
    
    - 現在のゲーム進行状況
    - 発見済み証拠
    - 残り証拠（位置情報のみ）
    """
    from ..errors import GameAPIError
    
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    progress_info = game_session.progress
    
    return GameStatusResponse(
        game_id=game_session.game_id,
        status=game_session.status,
        scenario=game_session.scenario,
        discovered_evidence=game_session.discovered_evidence,
        remaining_evidence=[
            Evidence(
                evidence_id=ev.evidence_id,
                name=ev.name,
                description="発見してください",
                discovery_text="",
                importance=ev.importance,
                location=ev.location,
                poi_name=ev.poi_name,
                poi_type=ev.poi_type
            ) for ev in game_session.remaining_evidence
        ],
        progress={
            "total_evidence": progress_info.total_evidence,
            "discovered_count": progress_info.discovered_count,
            "completion_rate": progress_info.completion_rate,
            "time_elapsed": progress_info.time_elapsed
        }
    )


@router.get("/{game_id}/nearby-evidence")
async def get_nearby_evidence(
    game_id: str = Path(..., description="ゲームセッションID"),
    lat: float = Query(..., description="現在位置の緯度"),
    lng: float = Query(..., description="現在位置の経度")
):
    """
    プレイヤー付近の未発見証拠を取得
    
    - 発見可能な範囲内にある証拠をリスト
    - 距離情報も含む
    """
    
    player_location = Location(lat=lat, lng=lng)
    
    nearby_evidence = await game_service.get_player_nearby_evidence(
        game_id, player_location
    )
    
    evidence_info = []
    for evidence in nearby_evidence:
        distance = player_location.distance_to(evidence.location)
        evidence_info.append({
            "evidence_id": evidence.evidence_id,
            "name": evidence.name,
            "poi_name": evidence.poi_name,
            "distance": round(distance, 1),
            "discoverable": distance <= 50.0  # 発見可能範囲
        })
    
    return {
        "game_id": game_id,
        "player_location": {"lat": lat, "lng": lng},
        "nearby_evidence": evidence_info
    }


@router.delete("/{game_id}")
async def abandon_game(
    game_id: str = Path(..., description="ゲームセッションID"),
    player_id: str = Query(..., description="プレイヤーID")
):
    """
    ゲームを中断・放棄
    
    - ゲーム状態を'abandoned'に変更
    - データは保持される
    """
    from ..errors import APIError, GameAPIError
    
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    if game_session.player_id != player_id:
        raise APIError.forbidden(
            code="FORBIDDEN",
            message="このゲームを操作する権限がありません"
        )
    
    # TODO: ゲーム放棄処理の実装
    # game_session.status = GameStatus.ABANDONED
    # await game_service._save_game_session(game_session)
    
    return {
        "message": "ゲームを中断しました",
        "game_id": game_id
    }