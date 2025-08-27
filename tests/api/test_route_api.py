"""
ルート生成APIのテスト
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from backend.src.main import app
from shared.models.location import Location
from shared.models.route import OptimalRoute


@pytest.fixture
def client():
    """テスト用HTTPクライアント"""
    return TestClient(app)


@pytest.fixture
def mock_game_session():
    """テスト用ゲームセッション"""
    from shared.models.game import GameSession, Difficulty
    from shared.models.evidence import Evidence, EvidenceImportance
    
    return GameSession(
        game_id="test_game_123",
        player_id="test_player_456",
        difficulty=Difficulty.NORMAL,
        player_location=Location(lat=35.6812, lng=139.7671),
        evidence_list=[
            Evidence(
                evidence_id="evidence_1",
                name="証拠1",
                description="テスト証拠1",
                discovery_text="テスト発見文1",
                importance=EvidenceImportance.IMPORTANT,
                location=Location(lat=35.6785, lng=139.7667),
                poi_name="丸の内",
                poi_type="landmark"
            ),
            Evidence(
                evidence_id="evidence_2", 
                name="証拠2",
                description="テスト証拠2",
                discovery_text="テスト発見文2",
                importance=EvidenceImportance.CRITICAL,
                location=Location(lat=35.6762, lng=139.7625),
                poi_name="日比谷",
                poi_type="park"
            ),
            Evidence(
                evidence_id="evidence_3",
                name="証拠3",
                description="テスト証拠3", 
                discovery_text="テスト発見文3",
                importance=EvidenceImportance.BACKGROUND,
                location=Location(lat=35.6794, lng=139.7707),
                poi_name="八重洲",
                poi_type="station"
            )
        ]
    )


class TestRouteGenerationAPI:
    """ルート生成APIのテスト"""
    
    @patch('backend.src.services.game_service.game_service.get_game_session')
    @patch('backend.src.services.route_generation_service.route_generation_service.generate_optimal_route')
    def test_generate_route_success(self, mock_generate_route, mock_get_game_session, client, mock_game_session):
        """ルート生成成功のテスト"""
        # モック設定
        mock_get_game_session.return_value = mock_game_session
        
        mock_optimal_route = OptimalRoute(
            route_id="test_route_123",
            waypoints=[
                Location(lat=35.6812, lng=139.7671),  # 開始地点
                Location(lat=35.6785, lng=139.7667),  # 証拠1
                Location(lat=35.6762, lng=139.7625),  # 証拠2
                Location(lat=35.6794, lng=139.7707),  # 証拠3
                Location(lat=35.6812, lng=139.7671)   # 開始地点に戻る
            ],
            total_distance=2500.0,
            estimated_time=35,
            safety_score=0.8
        )
        
        from shared.models.route import RouteGenerationResult
        mock_generate_route.return_value = RouteGenerationResult(
            success=True,
            optimal_route=mock_optimal_route,
            generation_time_ms=150
        )
        
        # APIリクエスト実行
        response = client.post("/api/v1/route/generate", json={
            "game_id": "test_game_123",
            "player_id": "test_player_456",
            "user_preferences": {"safety_priority": True}
        })
        
        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["route"] is not None
        assert data["generation_time_ms"] == 150
        assert data["error_message"] is None
        
        # ルート詳細検証
        route = data["route"]
        assert route["route_id"] == "test_route_123"
        assert len(route["waypoints"]) == 5
        assert route["total_distance"] == 2500.0
        assert route["estimated_time"] == 35
        assert route["safety_score"] == 0.8
        
        # サービス呼び出し確認
        mock_get_game_session.assert_called_once_with("test_game_123")
        mock_generate_route.assert_called_once()
    
    @patch('backend.src.services.game_service.game_service.get_game_session')
    def test_generate_route_game_not_found(self, mock_get_game_session, client):
        """ゲーム未発見エラーのテスト"""
        mock_get_game_session.return_value = None
        
        response = client.post("/api/v1/route/generate", json={
            "game_id": "nonexistent_game",
            "player_id": "test_player_456"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "GAME_NOT_FOUND"
    
    @patch('backend.src.services.game_service.game_service.get_game_session')
    def test_generate_route_player_mismatch(self, mock_get_game_session, client, mock_game_session):
        """プレイヤーID不一致エラーのテスト"""
        mock_get_game_session.return_value = mock_game_session
        
        response = client.post("/api/v1/route/generate", json={
            "game_id": "test_game_123",
            "player_id": "wrong_player_id"
        })
        
        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert "プレイヤーIDが一致しません" in data["error"]["message"]
    
    @patch('backend.src.services.game_service.game_service.get_game_session')
    @patch('backend.src.services.route_generation_service.route_generation_service.generate_optimal_route')
    def test_generate_route_generation_failed(self, mock_generate_route, mock_get_game_session, client, mock_game_session):
        """ルート生成失敗のテスト"""
        mock_get_game_session.return_value = mock_game_session
        
        from shared.models.route import RouteGenerationResult
        mock_generate_route.return_value = RouteGenerationResult(
            success=False,
            optimal_route=None,
            generation_time_ms=50,
            error_message="距離が長すぎます",
            warnings=["推定時間: 120分"]
        )
        
        response = client.post("/api/v1/route/generate", json={
            "game_id": "test_game_123",
            "player_id": "test_player_456"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["route"] is None
        assert data["error_message"] == "距離が長すぎます"
        assert "推定時間: 120分" in data["warnings"]


class TestRouteValidationAPI:
    """ルート検証APIのテスト"""
    
    def test_validate_route_success(self, client):
        """ルート検証成功のテスト"""
        locations = [
            {"lat": 35.6812, "lng": 139.7671},  # 東京駅
            {"lat": 35.6785, "lng": 139.7667},  # 丸の内
            {"lat": 35.6762, "lng": 139.7625},  # 日比谷
            {"lat": 35.6794, "lng": 139.7707}   # 八重洲
        ]
        
        response = client.post("/api/v1/route/validate", json=locations)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "estimated_distance" in data
        assert "estimated_time" in data
        assert "tsp_computation_time_ms" in data
        assert "visit_order" in data
        
        # 基本的な妥当性確認
        assert isinstance(data["is_valid"], bool)
        assert data["estimated_distance"] > 0
        assert data["estimated_time"] > 0
        assert data["tsp_computation_time_ms"] >= 0
        assert len(data["visit_order"]) == 5  # 開始→3地点→開始
    
    def test_validate_route_insufficient_locations(self, client):
        """地点数不足エラーのテスト"""
        locations = [
            {"lat": 35.6812, "lng": 139.7671},
            {"lat": 35.6785, "lng": 139.7667}  # 2地点のみ
        ]
        
        response = client.post("/api/v1/route/validate", json=locations)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "最低4つの地点" in data["error"]["message"]
    
    def test_validate_route_with_parameters(self, client):
        """パラメータ付きルート検証のテスト"""
        locations = [
            {"lat": 35.6812, "lng": 139.7671},
            {"lat": 35.6785, "lng": 139.7667},
            {"lat": 35.6762, "lng": 139.7625},
            {"lat": 35.6794, "lng": 139.7707}
        ]
        
        response = client.post(
            "/api/v1/route/validate?max_distance=1500&max_time=25",
            json=locations
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # パラメータが適用されているかの推論的確認
        assert "recommendations" in data
        if data["estimated_distance"] > 1500:
            assert any("距離が長すぎます" in rec for rec in data["recommendations"])


class TestTSPTestAPI:
    """TSPテストAPIのテスト"""
    
    def test_tsp_algorithm_comparison(self, client):
        """TSPアルゴリズム比較テスト"""
        response = client.get("/api/v1/route/test/tsp", params={
            "lat1": 35.6812, "lng1": 139.7671,  # 東京駅
            "lat2": 35.6785, "lng2": 139.7667,  # 丸の内
            "lat3": 35.6762, "lng3": 139.7625,  # 日比谷
            "lat4": 35.6794, "lng4": 139.7707   # 八重洲
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # 基本構造確認
        assert "locations" in data
        assert "distance_matrix" in data
        assert "brute_force" in data
        assert "nearest_neighbor" in data
        assert "improvement" in data
        
        # 位置情報確認
        assert len(data["locations"]) == 4
        assert len(data["distance_matrix"]) == 4
        
        # 総当たり法結果確認
        bf = data["brute_force"]
        assert bf["algorithm"] == "brute_force"
        assert len(bf["visit_order"]) == 5
        assert bf["total_distance"] > 0
        assert bf["computation_time_ms"] >= 0
        
        # 最近傍法結果確認
        nn = data["nearest_neighbor"]
        assert nn["algorithm"] == "nearest_neighbor"
        assert len(nn["visit_order"]) == 5
        assert nn["total_distance"] > 0
        assert nn["computation_time_ms"] >= 0
        
        # 改善度確認
        improvement = data["improvement"]
        assert "distance_improvement" in improvement
        assert "time_ratio" in improvement
        
        # 総当たり法が最適解であることを確認
        assert bf["total_distance"] <= nn["total_distance"]
    
    def test_tsp_test_missing_parameters(self, client):
        """必須パラメータ不足エラーのテスト"""
        response = client.get("/api/v1/route/test/tsp", params={
            "lat1": 35.6812, "lng1": 139.7671,  # 1地点のみ
        })
        
        assert response.status_code == 422  # Validation Error


@pytest.mark.integration  
class TestRouteAPIIntegration:
    """ルートAPI統合テスト"""
    
    @pytest.mark.asyncio
    async def test_full_route_generation_flow(self, client):
        """完全なルート生成フローのテスト"""
        # 1. まずTSPテストで基本機能確認
        tsp_response = client.get("/api/v1/route/test/tsp", params={
            "lat1": 35.6812, "lng1": 139.7671,
            "lat2": 35.6785, "lng2": 139.7667,
            "lat3": 35.6762, "lng3": 139.7625,
            "lat4": 35.6794, "lng4": 139.7707
        })
        assert tsp_response.status_code == 200
        
        # 2. 次にルート検証で適合性確認
        locations = [
            {"lat": 35.6812, "lng": 139.7671},
            {"lat": 35.6785, "lng": 139.7667},
            {"lat": 35.6762, "lng": 139.7625},
            {"lat": 35.6794, "lng": 139.7707}
        ]
        validate_response = client.post("/api/v1/route/validate", json=locations)
        assert validate_response.status_code == 200
        
        validation_data = validate_response.json()
        if validation_data["is_valid"]:
            # 3. 適合する場合のみルート生成を実行（ゲームセッションがあれば）
            # ここではモックなしでは実行できないのでスキップ
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])