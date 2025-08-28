"""
ルート生成関連APIルーター
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# LazyServiceManagerを使用
from ...services.lazy_service_manager import lazy_service_manager
from ...services.game_service import game_service
from shared.models.route import (
    RouteGenerationRequest, RouteGenerationResult, OptimalRoute
)
from shared.models.location import Location
from ..errors import APIError, GameAPIError

router = APIRouter()


# リクエスト・レスポンスモデル
class RouteGenerationRequestModel(BaseModel):
    """ルート生成リクエスト"""
    game_id: str
    player_id: str
    user_preferences: Optional[Dict[str, Any]] = None


class RouteGenerationResponse(BaseModel):
    """ルート生成レスポンス"""
    success: bool
    route: Optional[OptimalRoute]
    generation_time_ms: int
    error_message: Optional[str] = None
    warnings: List[str] = []


class RouteInfoResponse(BaseModel):
    """ルート情報レスポンス"""
    game_id: str
    route: OptimalRoute
    is_suitable: bool
    recommendations: List[str] = []


@router.post("/generate", response_model=RouteGenerationResponse)
async def generate_route(request: RouteGenerationRequestModel) -> RouteGenerationResponse:
    """
    ゲーム用の最適ルートを生成
    
    - ゲームセッションから証拠地点を取得
    - TSPアルゴリズムで最適順序を計算
    - Google Maps APIで詳細ルート生成
    """
    
    try:
        # ゲームセッションを取得
        game_session = await game_service.get_game_session(request.game_id)
        if not game_session:
            raise GameAPIError.game_not_found(request.game_id)
        
        # プレイヤーID検証
        if game_session.player_id != request.player_id:
            raise APIError.forbidden("プレイヤーIDが一致しません")
        
        # 証拠地点を取得
        if len(game_session.evidence_list) < 3:
            raise APIError.bad_request(
                "証拠地点が不足しています。最低3つの証拠が必要です。"
            )
        
        evidence_locations = [
            evidence.location 
            for evidence in game_session.evidence_list[:3]  # 最初の3つを使用
        ]
        
        # ルート生成リクエストを作成
        route_request = RouteGenerationRequest(
            start_location=game_session.player_location,
            evidence_locations=evidence_locations,
            user_preferences=request.user_preferences or {},
            difficulty_level=game_session.difficulty.value
        )
        
        # ルート生成サービスを取得（遅延初期化）
        route_generation_service = await lazy_service_manager.get_route_service()
        
        # ルート生成実行
        result = await route_generation_service.generate_optimal_route(route_request)
        
        if not result.success:
            return RouteGenerationResponse(
                success=False,
                route=None,
                generation_time_ms=result.generation_time_ms,
                error_message=result.error_message,
                warnings=result.warnings
            )
        
        return RouteGenerationResponse(
            success=True,
            route=result.optimal_route,
            generation_time_ms=result.generation_time_ms,
            warnings=result.warnings
        )
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise APIError.internal_server_error(
            code="ROUTE_GENERATION_FAILED",
            message="ルート生成処理に失敗しました",
            details=str(e)
        )


@router.get("/{game_id}/current", response_model=RouteInfoResponse)
async def get_current_route(game_id: str) -> RouteInfoResponse:
    """
    現在のゲームの生成済みルート情報を取得
    
    - 既に生成されたルート情報の表示
    - ルートの適合性評価
    - 改善提案の提示
    """
    
    # TODO: ゲームセッションにルート情報を保存する機能を実装後に有効化
    raise HTTPException(
        status_code=501,
        detail="この機能は現在開発中です。ルート情報の永続化機能実装後に有効になります。"
    )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_route(
    locations: List[Location],
    max_distance: Optional[float] = Query(3000, description="最大距離（メートル）"),
    max_time: Optional[int] = Query(45, description="最大時間（分）")
) -> Dict[str, Any]:
    """
    指定された地点でのルート生成可能性を事前検証
    
    - 距離・時間の事前チェック
    - 安全性の簡易評価
    - ルート生成の実行可能性判定
    """
    
    try:
        if len(locations) < 4:
            raise APIError.bad_request(
                "最低4つの地点（開始地点+証拠3地点）が必要です"
            )
        
        # 簡易TSP計算で距離を推定
        from ...services.route_generation_service import TSPSolver
        
        solver = TSPSolver()
        distance_matrix = solver.calculate_distance_matrix(locations)
        tsp_solution = solver.solve_brute_force(distance_matrix)
        
        estimated_distance = tsp_solution.total_distance
        estimated_time = int(estimated_distance / 80)  # 4.8km/h想定
        
        # 適合性チェック
        is_valid = (
            estimated_distance <= max_distance and
            estimated_time <= max_time and
            estimated_distance >= 1000  # 最小距離1km
        )
        
        recommendations = []
        if estimated_distance > max_distance:
            recommendations.append(f"距離が長すぎます（{estimated_distance:.0f}m > {max_distance}m）")
        if estimated_time > max_time:
            recommendations.append(f"時間が長すぎます（{estimated_time}分 > {max_time}分）")
        if estimated_distance < 1000:
            recommendations.append("距離が短すぎます。より遠い地点を選択してください")
        
        return {
            "is_valid": is_valid,
            "estimated_distance": estimated_distance,
            "estimated_time": estimated_time,
            "tsp_computation_time_ms": tsp_solution.computation_time_ms,
            "recommendations": recommendations,
            "visit_order": tsp_solution.visit_order
        }
        
    except Exception as e:
        raise APIError.internal_server_error(
            code="ROUTE_VALIDATION_FAILED",
            message="ルート検証に失敗しました",
            details=str(e)
        )


@router.get("/test/tsp", response_model=Dict[str, Any])
async def test_tsp_algorithm(
    lat1: float = Query(..., description="地点1の緯度"),
    lng1: float = Query(..., description="地点1の経度"), 
    lat2: float = Query(..., description="地点2の緯度"),
    lng2: float = Query(..., description="地点2の経度"),
    lat3: float = Query(..., description="地点3の緯度"),
    lng3: float = Query(..., description="地点3の経度"),
    lat4: float = Query(..., description="地点4の緯度"),
    lng4: float = Query(..., description="地点4の経度")
) -> Dict[str, Any]:
    """
    TSPアルゴリズムのテスト用エンドポイント
    
    - 4つの座標を指定してTSPを実行
    - 総当たり法と最近傍法の結果比較
    - 計算時間・精度の確認
    """
    
    try:
        locations = [
            Location(lat=lat1, lng=lng1),
            Location(lat=lat2, lng=lng2),
            Location(lat=lat3, lng=lng3),
            Location(lat=lat4, lng=lng4)
        ]
        
        from ...services.route_generation_service import TSPSolver
        
        solver = TSPSolver()
        distance_matrix = solver.calculate_distance_matrix(locations)
        
        # 両方のアルゴリズムを実行
        brute_force_solution = solver.solve_brute_force(distance_matrix)
        nearest_neighbor_solution = solver.solve_nearest_neighbor(distance_matrix)
        
        return {
            "locations": [{"lat": loc.lat, "lng": loc.lng} for loc in locations],
            "distance_matrix": distance_matrix,
            "brute_force": {
                "visit_order": brute_force_solution.visit_order,
                "total_distance": brute_force_solution.total_distance,
                "computation_time_ms": brute_force_solution.computation_time_ms,
                "algorithm": brute_force_solution.algorithm_used
            },
            "nearest_neighbor": {
                "visit_order": nearest_neighbor_solution.visit_order,
                "total_distance": nearest_neighbor_solution.total_distance,
                "computation_time_ms": nearest_neighbor_solution.computation_time_ms,
                "algorithm": nearest_neighbor_solution.algorithm_used
            },
            "improvement": {
                "distance_improvement": nearest_neighbor_solution.total_distance - brute_force_solution.total_distance,
                "time_ratio": brute_force_solution.computation_time_ms / max(nearest_neighbor_solution.computation_time_ms, 1)
            }
        }
        
    except Exception as e:
        raise APIError.internal_server_error(
            code="TSP_TEST_FAILED",
            message="TSPアルゴリズムテストに失敗しました",
            details=str(e)
        )