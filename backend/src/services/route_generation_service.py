"""
ルート生成サービス - TSPアルゴリズムとGoogle Maps API統合
"""

import asyncio
import time
import uuid
import itertools
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from geopy.distance import geodesic
import googlemaps

from ..core.logging import get_logger, LogCategory
from ..config.secrets import get_api_key
from shared.models.location import Location
from shared.models.route import (
    OptimalRoute, RouteCandidate, RouteGenerationRequest, RouteGenerationResult,
    TSPSolution, RouteSegment, RouteSegmentType, RouteSafetyInfo
)

logger = get_logger(__name__, LogCategory.GAME_SERVICE)


class TSPSolver:
    """巡回セールスマン問題（TSP）ソルバー"""
    
    @staticmethod
    def calculate_distance_matrix(locations: List[Location]) -> List[List[float]]:
        """地点間の距離行列を計算"""
        n = len(locations)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance = geodesic(
                        (locations[i].lat, locations[i].lng),
                        (locations[j].lat, locations[j].lng)
                    ).meters
                    matrix[i][j] = distance
        
        return matrix
    
    @staticmethod
    def solve_brute_force(distance_matrix: List[List[float]], start_index: int = 0) -> TSPSolution:
        """総当たり法でTSPを解く（4地点なので実用的）"""
        start_time = time.time()
        n = len(distance_matrix)
        
        if n <= 1:
            return TSPSolution(
                visit_order=[0],
                total_distance=0.0,
                computation_time_ms=int((time.time() - start_time) * 1000),
                algorithm_used="brute_force"
            )
        
        # 開始地点以外の地点の全順列を生成
        other_points = [i for i in range(n) if i != start_index]
        best_distance = float('inf')
        best_order = None
        
        for perm in itertools.permutations(other_points):
            # 開始地点 → 各地点 → 開始地点に戻る
            route = [start_index] + list(perm) + [start_index]
            total_distance = 0.0
            
            for i in range(len(route) - 1):
                total_distance += distance_matrix[route[i]][route[i + 1]]
            
            if total_distance < best_distance:
                best_distance = total_distance
                best_order = route
        
        computation_time = int((time.time() - start_time) * 1000)
        
        return TSPSolution(
            visit_order=best_order,
            total_distance=best_distance,
            computation_time_ms=computation_time,
            algorithm_used="brute_force"
        )
    
    @staticmethod
    def solve_nearest_neighbor(distance_matrix: List[List[float]], start_index: int = 0) -> TSPSolution:
        """最近傍法でTSPを解く（高速だが準最適）"""
        start_time = time.time()
        n = len(distance_matrix)
        
        if n <= 1:
            return TSPSolution(
                visit_order=[0],
                total_distance=0.0,
                computation_time_ms=int((time.time() - start_time) * 1000),
                algorithm_used="nearest_neighbor"
            )
        
        visited = [False] * n
        route = [start_index]
        visited[start_index] = True
        total_distance = 0.0
        current = start_index
        
        # 各ステップで最近の未訪問地点を選択
        for _ in range(n - 1):
            nearest_distance = float('inf')
            nearest_index = -1
            
            for i in range(n):
                if not visited[i] and distance_matrix[current][i] < nearest_distance:
                    nearest_distance = distance_matrix[current][i]
                    nearest_index = i
            
            route.append(nearest_index)
            visited[nearest_index] = True
            total_distance += nearest_distance
            current = nearest_index
        
        # 開始地点に戻る
        route.append(start_index)
        total_distance += distance_matrix[current][start_index]
        
        computation_time = int((time.time() - start_time) * 1000)
        
        return TSPSolution(
            visit_order=route,
            total_distance=total_distance,
            computation_time_ms=computation_time,
            algorithm_used="nearest_neighbor"
        )


class RouteGenerationService:
    """ルート生成サービス"""
    
    def __init__(self):
        self.gmaps: Optional[googlemaps.Client] = None
        self.tsp_solver = TSPSolver()
        self.route_cache: Dict[str, Tuple[OptimalRoute, datetime]] = {}
        self.cache_duration = timedelta(hours=1)
    
    async def initialize(self) -> None:
        """サービス初期化"""
        google_maps_api_key = get_api_key('google_maps')
        if google_maps_api_key:
            self.gmaps = googlemaps.Client(key=google_maps_api_key)
            logger.info("Google Maps API initialized for route generation")
        else:
            logger.warning("Google Maps API key not found. Using mock route generation.")
    
    async def generate_optimal_route(
        self,
        request: RouteGenerationRequest
    ) -> RouteGenerationResult:
        """最適ルートを生成"""
        start_time = time.time()
        
        try:
            # キャッシュチェック
            cache_key = self._generate_cache_key(request)
            cached_route = self._get_cached_route(cache_key)
            if cached_route:
                logger.info("Using cached route", cache_key=cache_key)
                return RouteGenerationResult(
                    success=True,
                    optimal_route=cached_route,
                    generation_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # TSPソルバーで最適順序を計算
            tsp_solution = await self._solve_tsp(request.total_locations)
            
            # Google Maps APIでルート詳細を取得
            if self.gmaps:
                optimal_route = await self._create_detailed_route(
                    request, tsp_solution
                )
            else:
                optimal_route = self._create_mock_route(request, tsp_solution)
            
            # ルート評価とフィルタリング
            if not optimal_route.is_suitable_for_walking:
                logger.warning(
                    "Generated route not suitable for walking",
                    distance=optimal_route.total_distance,
                    time=optimal_route.estimated_time
                )
                return RouteGenerationResult(
                    success=False,
                    error_message="生成されたルートがウォーキングに適していません",
                    generation_time_ms=int((time.time() - start_time) * 1000),
                    warnings=[
                        f"距離: {optimal_route.total_distance:.0f}m",
                        f"推定時間: {optimal_route.estimated_time}分"
                    ]
                )
            
            # キャッシュに保存
            self._cache_route(cache_key, optimal_route)
            
            generation_time = int((time.time() - start_time) * 1000)
            logger.info(
                "Route generation completed",
                distance=optimal_route.total_distance,
                time=optimal_route.estimated_time,
                safety_score=optimal_route.safety_score,
                generation_time_ms=generation_time
            )
            
            return RouteGenerationResult(
                success=True,
                optimal_route=optimal_route,
                generation_time_ms=generation_time
            )
            
        except Exception as e:
            error_time = int((time.time() - start_time) * 1000)
            logger.error("Route generation failed", exception=e)
            return RouteGenerationResult(
                success=False,
                error_message=f"ルート生成に失敗しました: {str(e)}",
                generation_time_ms=error_time
            )
    
    async def _solve_tsp(self, locations: List[Location]) -> TSPSolution:
        """TSPを解いて最適な訪問順序を求める"""
        distance_matrix = self.tsp_solver.calculate_distance_matrix(locations)
        
        # 4地点なので総当たり法を使用（3! = 6通りの順列のみ）
        if len(locations) <= 5:
            return self.tsp_solver.solve_brute_force(distance_matrix, start_index=0)
        else:
            # 将来の拡張で地点数が増えた場合は最近傍法を使用
            return self.tsp_solver.solve_nearest_neighbor(distance_matrix, start_index=0)
    
    async def _create_detailed_route(
        self,
        request: RouteGenerationRequest,
        tsp_solution: TSPSolution
    ) -> OptimalRoute:
        """Google Maps APIを使用して詳細なルートを作成"""
        ordered_locations = tsp_solution.get_ordered_locations(request.total_locations)
        
        # Google Maps Directions APIで詳細ルート取得
        directions_result = await asyncio.to_thread(
            self.gmaps.directions,
            origin=(ordered_locations[0].lat, ordered_locations[0].lng),
            destination=(ordered_locations[-1].lat, ordered_locations[-1].lng),
            waypoints=[
                (loc.lat, loc.lng) for loc in ordered_locations[1:-1]
            ],
            mode="walking",
            optimize_waypoints=False,  # すでにTSPで最適化済み
            language="ja"
        )
        
        if not directions_result:
            raise ValueError("Google Maps APIからルート情報を取得できませんでした")
        
        route_data = directions_result[0]
        
        # ルート詳細を解析
        total_distance = route_data['legs'][0]['distance']['value']
        total_duration = route_data['legs'][0]['duration']['value']
        
        # セグメント情報を作成
        segments = self._parse_route_segments(route_data)
        
        # 安全性情報を評価
        safety_info = self._evaluate_route_safety(ordered_locations)
        
        return OptimalRoute(
            route_id=str(uuid.uuid4()),
            waypoints=ordered_locations,
            total_distance=float(total_distance),
            estimated_time=int(total_duration / 60),  # 分単位に変換
            safety_score=safety_info.pedestrian_friendly_score,
            segments=segments,
            safety_info=safety_info
        )
    
    def _create_mock_route(
        self,
        request: RouteGenerationRequest,
        tsp_solution: TSPSolution
    ) -> OptimalRoute:
        """モックルートを作成（Google Maps API未使用時）"""
        ordered_locations = tsp_solution.get_ordered_locations(request.total_locations)
        
        # 簡単な推定値を計算
        total_distance = tsp_solution.total_distance
        estimated_time = int(total_distance / 80)  # 約4.8km/hの歩行速度
        
        # モック安全性情報
        safety_info = RouteSafetyInfo(
            pedestrian_friendly_score=0.75,
            lighting_score=0.7,
            traffic_safety_score=0.8,
            sidewalk_coverage=0.8,
            warnings=["モックデータです"]
        )
        
        return OptimalRoute(
            route_id=str(uuid.uuid4()),
            waypoints=ordered_locations,
            total_distance=total_distance,
            estimated_time=estimated_time,
            safety_score=0.75,
            safety_info=safety_info
        )
    
    def _parse_route_segments(self, route_data: Dict[str, Any]) -> List[RouteSegment]:
        """Google Maps ルートデータからセグメント情報を解析"""
        segments = []
        
        for leg in route_data['legs']:
            for step in leg['steps']:
                # 基本的なセグメント情報を作成
                segment = RouteSegment(
                    start_location=Location(
                        lat=step['start_location']['lat'],
                        lng=step['start_location']['lng']
                    ),
                    end_location=Location(
                        lat=step['end_location']['lat'],
                        lng=step['end_location']['lng']
                    ),
                    distance=step['distance']['value'],
                    duration=step['duration']['value'],
                    instruction=step['html_instructions'],
                    segment_type=self._determine_segment_type(step['html_instructions']),
                    polyline=step.get('polyline', {}).get('points')
                )
                segments.append(segment)
        
        return segments
    
    def _determine_segment_type(self, instruction: str) -> RouteSegmentType:
        """道案内指示からセグメントタイプを判定"""
        instruction_lower = instruction.lower()
        
        if "left" in instruction_lower or "左" in instruction:
            return RouteSegmentType.TURN_LEFT
        elif "right" in instruction_lower or "右" in instruction:
            return RouteSegmentType.TURN_RIGHT
        elif "roundabout" in instruction_lower or "ラウンドアバウト" in instruction:
            return RouteSegmentType.ROUNDABOUT
        elif "stairs" in instruction_lower or "階段" in instruction:
            return RouteSegmentType.STAIRS
        elif "crosswalk" in instruction_lower or "横断歩道" in instruction:
            return RouteSegmentType.CROSSWALK
        else:
            return RouteSegmentType.STRAIGHT
    
    def _evaluate_route_safety(self, locations: List[Location]) -> RouteSafetyInfo:
        """ルートの安全性を評価"""
        # 現在は簡単な評価。将来的にはより詳細な評価を実装
        return RouteSafetyInfo(
            pedestrian_friendly_score=0.8,
            lighting_score=0.7,
            traffic_safety_score=0.75,
            sidewalk_coverage=0.85,
            warnings=[]
        )
    
    def _generate_cache_key(self, request: RouteGenerationRequest) -> str:
        """キャッシュキーを生成"""
        locations_str = "_".join([
            f"{loc.lat:.4f},{loc.lng:.4f}" 
            for loc in request.total_locations
        ])
        return f"route_{hash(locations_str)}"
    
    def _get_cached_route(self, cache_key: str) -> Optional[OptimalRoute]:
        """キャッシュからルートを取得"""
        if cache_key in self.route_cache:
            route, cached_time = self.route_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return route
            else:
                del self.route_cache[cache_key]
        return None
    
    def _cache_route(self, cache_key: str, route: OptimalRoute) -> None:
        """ルートをキャッシュに保存"""
        self.route_cache[cache_key] = (route, datetime.now())
        
        # キャッシュサイズ制限（最大100エントリ）
        if len(self.route_cache) > 100:
            oldest_key = min(
                self.route_cache.keys(),
                key=lambda k: self.route_cache[k][1]
            )
            del self.route_cache[oldest_key]


# グローバルサービスインスタンス
route_generation_service = RouteGenerationService()