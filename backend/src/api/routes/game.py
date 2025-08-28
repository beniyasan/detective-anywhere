"""
ゲーム関連APIルーター
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from ...services.game_service import game_service
from ...services.database_service import database_service
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

@router.post("/start-async", response_model=Dict[str, str])
async def start_game_async(request: GameStartRequest):
    """
    新しいミステリーゲームを非同期で開始（高速レスポンス）
    
    - 即座にゲームIDを返し、バックグラウンドでシナリオを生成
    - クライアントは /game/{game_id}/status で進捗を確認
    """
    from ..errors import APIError
    import asyncio
    
    try:
        # 基本的な検証のみ実行
        if request.radius not in [200, 500, 1000, 2000]:
            raise ValueError("検索半径は200m, 500m, 1000m, 2000mのいずれかを指定してください")
        
        # ゲームIDを即座に生成
        import uuid
        game_id = str(uuid.uuid4())
        
        # バックグラウンドでゲーム生成を開始
        asyncio.create_task(
            game_service.start_new_game_background(
                game_id=game_id,
                player_id=request.player_id,
                player_location=request.location,
                difficulty=request.difficulty,
                radius=request.radius
            )
        )
        
        return {
            "game_id": game_id,
            "status": "generating",
            "message": "ゲーム生成を開始しました。進捗は /api/v1/game/{game_id}/status で確認してください。"
        }
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise APIError.internal_server_error(message=f"ゲーム開始に失敗: {str(e)}")

@router.post("/start-instant", response_model=GameStartResponse)
async def start_game_instant(request: GameStartRequest):
    """
    即座にゲーム開始（プリセットシナリオ使用）
    
    - 5秒以内に完成されたゲームを返す
    - プリセットシナリオとプレイヤー位置周辺の証拠を生成
    - テスト・デモ用途に最適
    """
    from ..errors import APIError
    import uuid
    
    try:
        # 基本検証
        if request.radius not in [200, 500, 1000, 2000]:
            raise ValueError("検索半径は200m, 500m, 1000m, 2000mのいずれかを指定してください")
        
        # 即座にプリセットゲームを生成
        game_session = await game_service.create_instant_game(
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
                "search_radius": request.radius
            }
        )
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise APIError.internal_server_error(message=f"即座ゲーム開始に失敗: {str(e)}")

@router.post("/start-progressive", response_model=GameStartResponse)
async def start_game_progressive(request: GameStartRequest):
    """
    段階的AI生成ゲーム開始（真の無限シナリオ）
    
    - Phase 1: 軽量AI生成で即座開始（5-10秒）
    - Phase 2: バックグラウンドで詳細化
    - 本来のAI生成価値を保持しつつ高速開始を実現
    """
    from ..errors import APIError, GameAPIError
    
    try:
        # 段階的AI生成ゲーム開始
        game_session = await game_service.start_progressive_ai_game(
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
                "search_radius": request.radius,
                "generation_mode": "progressive_ai"  # AI生成であることを明示
            }
        )
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise GameAPIError.scenario_generation_failed(details=str(e))

@router.get("/debug/api-key-status")
async def debug_api_key_status():
    """
    デバッグ用: APIキーの設定状況確認
    """
    from ..errors import APIError
    import os
    
    try:
        from ...config.secrets import get_api_key
        
        # APIキー取得テスト
        gemini_key = get_api_key("gemini")
        has_gemini_key = bool(gemini_key)
        
        # 環境変数チェック
        env_gemini_key = os.getenv("GEMINI_API_KEY")
        has_env_key = bool(env_gemini_key)
        
        # AIサービス状態
        from ...services.lazy_service_manager import lazy_service_manager
        ai_service = await lazy_service_manager.get_ai_service()
        ai_has_key = bool(ai_service.gemini_api_key)
        
        return {
            "debug_info": {
                "gemini_api_key_detected": has_gemini_key,
                "gemini_key_length": len(gemini_key) if gemini_key else 0,
                "env_key_detected": has_env_key,
                "env_key_length": len(env_gemini_key) if env_gemini_key else 0,
                "ai_service_has_key": ai_has_key,
                "ai_service_key_length": len(ai_service.gemini_api_key) if ai_service.gemini_api_key else 0
            },
            "message": "APIキー状況確認完了"
        }
        
    except Exception as e:
        raise APIError.internal_server_error(message=f"デバッグ情報取得エラー: {str(e)}")


@router.get("/{game_id}/status")
async def get_game_status(
    game_id: str = Path(..., description="ゲームセッションID")
):
    """
    ゲーム状態を取得
    
    - 現在のゲーム進行状況
    - 発見済み証拠
    - 残り証拠（位置情報のみ）
    - 生成中の場合は生成状況
    """
    from ..errors import GameAPIError
    
    # まずデータベースから直接状態を確認
    game_data = await database_service.get_game_session(game_id)
    
    if not game_data:
        raise GameAPIError.game_not_found(game_id)
    
    # 生成中またはエラー状態の場合
    if isinstance(game_data, dict):
        if game_data.get("status") == "generating":
            return {
                "game_id": game_id,
                "status": "generating",
                "message": "ゲームシナリオを生成中です..."
            }
        elif game_data.get("status") == "error":
            return {
                "game_id": game_id,
                "status": "error", 
                "message": f"ゲーム生成に失敗しました: {game_data.get('error', '不明なエラー')}"
            }
    
    # 完成されたゲームの場合
    try:
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
    except Exception as e:
        logger.error(f"Failed to get game status for {game_id}: {e}")
        return {
            "game_id": game_id,
            "status": "error",
            "message": f"ゲーム状態の取得に失敗: {str(e)}"
        }


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