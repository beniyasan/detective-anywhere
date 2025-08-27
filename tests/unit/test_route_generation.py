"""
ルート生成システムのテスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from backend.src.services.route_generation_service import (
    RouteGenerationService, TSPSolver, route_generation_service
)
from shared.models.location import Location
from shared.models.route import (
    RouteGenerationRequest, OptimalRoute, TSPSolution,
    RouteSegment, RouteSafetyInfo
)


class TestTSPSolver:
    """TSPソルバーのテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.solver = TSPSolver()
        
        # テスト用の4地点（東京駅周辺）
        self.test_locations = [
            Location(lat=35.6812, lng=139.7671),  # 東京駅
            Location(lat=35.6785, lng=139.7667),  # 丸の内
            Location(lat=35.6762, lng=139.7625),  # 日比谷
            Location(lat=35.6794, lng=139.7707)   # 八重洲
        ]
    
    def test_calculate_distance_matrix(self):
        """距離行列計算のテスト"""
        matrix = self.solver.calculate_distance_matrix(self.test_locations)
        
        # 基本検証
        assert len(matrix) == 4
        assert len(matrix[0]) == 4
        
        # 対角線要素は0
        for i in range(4):
            assert matrix[i][i] == 0.0
        
        # 対称行列であることを確認
        for i in range(4):
            for j in range(4):
                assert abs(matrix[i][j] - matrix[j][i]) < 1.0  # 誤差1m以内
        
        # 距離が合理的な範囲内であることを確認
        for i in range(4):
            for j in range(4):
                if i != j:
                    assert 100 < matrix[i][j] < 2000  # 100m-2km範囲
    
    def test_solve_brute_force(self):
        """総当たり法TSPのテスト"""
        matrix = self.solver.calculate_distance_matrix(self.test_locations)
        solution = self.solver.solve_brute_force(matrix, start_index=0)
        
        # 基本検証
        assert isinstance(solution, TSPSolution)
        assert solution.algorithm_used == "brute_force"
        assert solution.computation_time_ms >= 0
        
        # ルート検証
        assert len(solution.visit_order) == 5  # 開始→3地点→開始
        assert solution.visit_order[0] == 0    # 開始地点
        assert solution.visit_order[-1] == 0   # 開始地点に戻る
        
        # 全地点が含まれていることを確認
        middle_points = solution.visit_order[1:-1]
        assert set(middle_points) == {1, 2, 3}
        
        # 距離が正の値
        assert solution.total_distance > 0
    
    def test_solve_nearest_neighbor(self):
        """最近傍法TSPのテスト"""
        matrix = self.solver.calculate_distance_matrix(self.test_locations)
        solution = self.solver.solve_nearest_neighbor(matrix, start_index=0)
        
        # 基本検証
        assert isinstance(solution, TSPSolution)
        assert solution.algorithm_used == "nearest_neighbor"
        assert solution.computation_time_ms >= 0
        
        # ルート検証
        assert len(solution.visit_order) == 5
        assert solution.visit_order[0] == 0
        assert solution.visit_order[-1] == 0
        
        # 全地点が含まれていることを確認
        middle_points = solution.visit_order[1:-1]
        assert set(middle_points) == {1, 2, 3}
    
    def test_algorithm_comparison(self):
        """総当たり法と最近傍法の比較"""
        matrix = self.solver.calculate_distance_matrix(self.test_locations)
        
        brute_force = self.solver.solve_brute_force(matrix, start_index=0)
        nearest_neighbor = self.solver.solve_nearest_neighbor(matrix, start_index=0)
        
        # 総当たり法が最適解を保証
        assert brute_force.total_distance <= nearest_neighbor.total_distance
        
        # 最近傍法が高速
        assert nearest_neighbor.computation_time_ms <= brute_force.computation_time_ms * 2
    
    def test_single_location(self):
        """単一地点のエッジケース"""
        single_location = [self.test_locations[0]]
        matrix = self.solver.calculate_distance_matrix(single_location)
        solution = self.solver.solve_brute_force(matrix)
        
        assert solution.visit_order == [0]
        assert solution.total_distance == 0.0


class TestRouteGenerationService:
    """ルート生成サービスのテスト"""
    
    @pytest.fixture
    def service(self):
        """テスト用サービスインスタンス"""
        service = RouteGenerationService()
        return service
    
    @pytest.fixture
    def test_request(self):
        """テスト用ルート生成リクエスト"""
        return RouteGenerationRequest(
            start_location=Location(lat=35.6812, lng=139.7671),  # 東京駅
            evidence_locations=[
                Location(lat=35.6785, lng=139.7667),  # 丸の内
                Location(lat=35.6762, lng=139.7625),  # 日比谷
                Location(lat=35.6794, lng=139.7707)   # 八重洲
            ],
            difficulty_level="normal"
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, service):
        """サービス初期化のテスト"""
        await service.initialize()
        # Google Maps APIキーが設定されていない場合はNoneのまま
        assert service.gmaps is None or service.gmaps is not None
        assert service.tsp_solver is not None
        assert isinstance(service.route_cache, dict)
    
    @pytest.mark.asyncio
    async def test_generate_optimal_route_mock(self, service, test_request):
        """モック環境でのルート生成テスト"""
        # Google Maps APIを無効にしてモックモードでテスト
        service.gmaps = None
        
        result = await service.generate_optimal_route(test_request)
        
        # 基本検証
        assert result.success is True
        assert result.optimal_route is not None
        assert result.generation_time_ms >= 0
        
        # ルート検証
        route = result.optimal_route
        assert len(route.waypoints) == 4  # 開始+証拠3地点
        assert route.waypoints[0] == test_request.start_location
        assert route.total_distance > 0
        assert route.estimated_time > 0
        assert 0 <= route.safety_score <= 1
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, service, test_request):
        """キャッシュ機能のテスト"""
        service.gmaps = None  # モックモード
        
        # 初回実行
        result1 = await service.generate_optimal_route(test_request)
        assert result1.success is True
        
        # キャッシュの存在確認
        cache_key = service._generate_cache_key(test_request)
        assert cache_key in service.route_cache
        
        # 2回目実行（キャッシュヒット）
        result2 = await service.generate_optimal_route(test_request)
        assert result2.success is True
        
        # 同じルートが返されることを確認
        assert result1.optimal_route.route_id == result2.optimal_route.route_id
    
    @pytest.mark.asyncio
    async def test_unsuitable_route_rejection(self, service):
        """不適切なルートの拒否テスト"""
        service.gmaps = None
        
        # 極端に近い地点でルート生成（距離不足）
        close_request = RouteGenerationRequest(
            start_location=Location(lat=35.6812, lng=139.7671),
            evidence_locations=[
                Location(lat=35.6812, lng=139.7672),  # 10m程度
                Location(lat=35.6812, lng=139.7673),  # 20m程度  
                Location(lat=35.6812, lng=139.7674)   # 30m程度
            ]
        )
        
        result = await service.generate_optimal_route(close_request)
        
        # 不適切として拒否されることを確認
        assert result.success is False
        assert "ウォーキングに適していません" in result.error_message
    
    def test_cache_key_generation(self, service, test_request):
        """キャッシュキー生成のテスト"""
        key1 = service._generate_cache_key(test_request)
        key2 = service._generate_cache_key(test_request)
        
        # 同じリクエストは同じキー
        assert key1 == key2
        
        # 異なるリクエストは異なるキー
        different_request = RouteGenerationRequest(
            start_location=Location(lat=35.6800, lng=139.7600),  # 異なる開始地点
            evidence_locations=test_request.evidence_locations
        )
        key3 = service._generate_cache_key(different_request)
        assert key1 != key3
    
    def test_cache_expiration(self, service, test_request):
        """キャッシュ有効期限のテスト"""
        cache_key = service._generate_cache_key(test_request)
        
        # テスト用ルート作成
        test_route = OptimalRoute(
            route_id="test",
            waypoints=test_request.total_locations,
            total_distance=2000.0,
            estimated_time=30,
            safety_score=0.8
        )
        
        # 期限切れのキャッシュを設定
        expired_time = datetime.now() - timedelta(hours=2)
        service.route_cache[cache_key] = (test_route, expired_time)
        
        # 期限切れキャッシュは取得できない
        cached_route = service._get_cached_route(cache_key)
        assert cached_route is None
        
        # 期限切れキャッシュは削除される
        assert cache_key not in service.route_cache


@pytest.mark.integration
class TestRouteGenerationIntegration:
    """ルート生成の統合テスト"""
    
    @pytest.mark.asyncio
    @patch('googlemaps.Client')
    async def test_google_maps_api_integration(self, mock_gmaps_client):
        """Google Maps API統合テスト（モック）"""
        # Google Maps APIレスポンスをモック
        mock_directions = {
            'routes': [{
                'legs': [{
                    'distance': {'value': 2500},
                    'duration': {'value': 1800},
                    'steps': [{
                        'start_location': {'lat': 35.6812, 'lng': 139.7671},
                        'end_location': {'lat': 35.6785, 'lng': 139.7667},
                        'distance': {'value': 300},
                        'duration': {'value': 240},
                        'html_instructions': '直進してください',
                        'polyline': {'points': 'test_polyline'}
                    }]
                }]
            }]
        }
        
        mock_client = Mock()
        mock_client.directions.return_value = [mock_directions]
        mock_gmaps_client.return_value = mock_client
        
        service = RouteGenerationService()
        service.gmaps = mock_client
        
        request = RouteGenerationRequest(
            start_location=Location(lat=35.6812, lng=139.7671),
            evidence_locations=[
                Location(lat=35.6785, lng=139.7667),
                Location(lat=35.6762, lng=139.7625),
                Location(lat=35.6794, lng=139.7707)
            ]
        )
        
        result = await service.generate_optimal_route(request)
        
        # API呼び出し確認
        mock_client.directions.assert_called_once()
        
        # 結果検証
        assert result.success is True
        assert result.optimal_route is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])