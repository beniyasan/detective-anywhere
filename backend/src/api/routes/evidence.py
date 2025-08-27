"""
証拠発見関連APIルーター
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from ...services.game_service import game_service
from ...services.gps_service import GPSReading, GPSAccuracy
from ....shared.models.location import Location
from ....shared.models.evidence import Evidence, EvidenceDiscoveryResult
from ..errors import APIError, EvidenceAPIError, GameAPIError


router = APIRouter()


# リクエスト/レスポンス モデル
class GPSAccuracyInfo(BaseModel):
    """GPS精度情報"""
    horizontal_accuracy: float
    vertical_accuracy: Optional[float] = None
    timestamp: datetime
    provider: str = "unknown"

class GPSInfo(BaseModel):
    """GPS情報"""
    location: Location
    accuracy: GPSAccuracyInfo
    speed: Optional[float] = None
    bearing: Optional[float] = None
    altitude: Optional[float] = None

class EvidenceDiscoveryRequest(BaseModel):
    """証拠発見リクエスト（GPS情報付き）"""
    game_id: str
    player_id: str
    current_location: Location
    evidence_id: str
    gps_info: Optional[GPSInfo] = None


class EvidenceDiscoveryResponse(BaseModel):
    """証拠発見レスポンス"""
    success: bool
    evidence: Optional[Evidence]
    distance: float
    next_clue: Optional[str]
    message: str
    discovery_bonus: int


@router.post("/discover", response_model=EvidenceDiscoveryResponse)
async def discover_evidence(request: EvidenceDiscoveryRequest):
    """
    証拠を発見する（GPS検証付き）
    
    - プレイヤーが証拠の場所に到達した時に呼び出し
    - GPS精度を考慮した距離チェックを行い、範囲内なら証拠を発見
    - GPS偽造検出機能も含む
    - 発見時は詳細な証拠情報と次のヒントを返却
    """
    
    try:
        # GPS情報をGPSReadingオブジェクトに変換（提供されている場合）
        gps_reading = None
        if request.gps_info:
            gps_reading = GPSReading(
                location=request.gps_info.location,
                accuracy=GPSAccuracy(
                    horizontal_accuracy=request.gps_info.accuracy.horizontal_accuracy,
                    vertical_accuracy=request.gps_info.accuracy.vertical_accuracy,
                    timestamp=request.gps_info.accuracy.timestamp,
                    provider=request.gps_info.accuracy.provider
                ),
                speed=request.gps_info.speed,
                bearing=request.gps_info.bearing,
                altitude=request.gps_info.altitude
            )
        
        # 証拠発見処理（GPS検証付き）
        result = await game_service.discover_evidence(
            game_id=request.game_id,
            player_id=request.player_id,
            player_location=request.current_location,
            evidence_id=request.evidence_id,
            gps_reading=gps_reading
        )
        
        return EvidenceDiscoveryResponse(
            success=result.success,
            evidence=result.evidence,
            distance=result.distance,
            next_clue=result.next_clue,
            message=result.message,
            discovery_bonus=result.discovery_bonus
        )
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise APIError.internal_server_error(
            code="EVIDENCE_DISCOVERY_FAILED",
            message="証拠発見処理に失敗しました",
            details=str(e)
        )


@router.get("/{evidence_id}/hint")
async def get_evidence_hint(
    evidence_id: str = Path(..., description="証拠ID"),
    game_id: str = None,
    player_id: str = None
):
    """
    証拠に関するヒントを取得
    
    - 証拠の場所に関する間接的なヒント
    - ヒント使用はゲームスコアに影響
    """
    
    if not game_id or not player_id:
        raise APIError.bad_request(
            code="MISSING_PARAMETERS",
            message="game_idとplayer_idが必要です"
        )
    
    # ゲームセッション取得
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    if game_session.player_id != player_id:
        raise APIError.forbidden(
            message="このゲームのヒントを取得する権限がありません"
        )
    
    # 該当証拠を検索
    evidence = None
    for ev in game_session.evidence_list:
        if ev.evidence_id == evidence_id:
            evidence = ev
            break
    
    if not evidence:
        raise EvidenceAPIError.evidence_not_found(evidence_id)
    
    # 既に発見済みの場合
    if evidence_id in game_session.discovered_evidence:
        return {
            "hint": "この証拠は既に発見済みです",
            "evidence_id": evidence_id,
            "discovered": True
        }
    
    # ヒント生成
    hint_text = f"{evidence.poi_name}の近くを探してみてください。"
    
    # POIタイプに基づく追加ヒント
    type_hints = {
        "restaurant": "美味しい料理の香りがするところです",
        "cafe": "コーヒーの香りが漂うところです",
        "park": "緑豊かで自然を感じられるところです",
        "station": "多くの人が行き交う交通の要所です",
        "landmark": "この地域で有名な場所です",
        "shop": "買い物ができるところです"
    }
    
    additional_hint = type_hints.get(evidence.poi_type, "")
    if additional_hint:
        hint_text += f" {additional_hint}。"
    
    # TODO: ヒント使用回数をゲームセッションに記録
    
    return {
        "hint": hint_text,
        "evidence_id": evidence_id,
        "poi_name": evidence.poi_name,
        "poi_type": evidence.poi_type,
        "discovered": False,
        "hint_penalty": 5  # ヒント使用によるスコア減点
    }


@router.get("/{evidence_id}/location")
async def get_evidence_location_info(
    evidence_id: str = Path(..., description="証拠ID"),
    game_id: str = None
):
    """
    証拠の位置情報を取得
    
    - デバッグ用エンドポイント
    - 本番環境では無効化される可能性
    """
    
    if not game_id:
        raise APIError.bad_request(
            code="MISSING_GAME_ID",
            message="game_idが必要です"
        )
    
    # 開発環境でのみ有効
    import os
    from ...config.settings import get_settings
    settings = get_settings()
    if not settings.is_development:
        raise APIError.forbidden(
            code="DEBUG_ONLY",
            message="このエンドポイントは開発環境でのみ利用可能です"
        )
    
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    evidence = None
    for ev in game_session.evidence_list:
        if ev.evidence_id == evidence_id:
            evidence = ev
            break
    
    if not evidence:
        raise EvidenceAPIError.evidence_not_found(evidence_id)
    
    return {
        "evidence_id": evidence_id,
        "name": evidence.name,
        "location": {
            "lat": evidence.location.lat,
            "lng": evidence.location.lng
        },
        "poi_name": evidence.poi_name,
        "poi_type": evidence.poi_type,
        "discovered": evidence_id in game_session.discovered_evidence
    }