"""
ゲームサービス - ビジネスロジック
"""

import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .database_service import database_service
from ...shared.models.game import (
    GameSession, GameStatus, Difficulty, GameScore, 
    DeductionRequest, DeductionResult
)
from ...shared.models.scenario import Scenario, ScenarioGenerationRequest
from ...shared.models.evidence import Evidence, EvidenceDiscoveryResult
from ...shared.models.location import Location
from ...shared.models.character import CharacterReaction

from .ai_service import ai_service
from .poi_service import poi_service
from .enhanced_poi_service import enhanced_poi_service
from .gps_service import gps_service, GPSReading, GPSAccuracy


class GameService:
    """ゲームサービス"""
    
    async def start_new_game(
        self,
        player_id: str,
        player_location: Location,
        difficulty: Difficulty
    ) -> GameSession:
        """
        新しいゲームセッションを開始
        
        Args:
            player_id: プレイヤーID
            player_location: プレイヤーの現在位置
            difficulty: 難易度
        
        Returns:
            GameSession: 作成されたゲームセッション
        """
        
        # 位置の有効性チェック
        if not await poi_service.validate_location(player_location):
            raise ValueError("無効な位置情報です")
        
        # 同じプレイヤーのアクティブなゲーム数チェック
        active_games = await database_service.get_active_games_by_player(player_id)
        if len(active_games) >= 3:  # 最大3つまで
            raise ValueError("同時進行可能なゲーム数を超えています")
        
        # 拡張POIサービスを初期化
        await enhanced_poi_service.initialize()
        
        # 証拠配置に最適化されたPOI検索
        evidence_count = self._get_evidence_count(difficulty)
        evidence_pois = await enhanced_poi_service.find_evidence_suitable_pois(
            player_location,
            radius=1000,
            evidence_count=evidence_count
        )
        
        if len(evidence_pois) < 3:
            raise ValueError("この地域にはゲーム作成に十分なPOIがありません")
        
        # 地域コンテキスト取得
        location_context = await poi_service.get_location_context(player_location)
        
        # シナリオ生成リクエスト作成
        scenario_request = ScenarioGenerationRequest(
            difficulty=difficulty.value,
            location_context=location_context,
            poi_types=[poi.poi_type.value for poi in evidence_pois],
            suspect_count_range=self._get_suspect_count_range(difficulty)
        )
        
        # AIでシナリオ生成
        scenario = await ai_service.generate_mystery_scenario(scenario_request)
        
        # 証拠生成（選択されたPOIを使用）
        evidence_list = await ai_service.generate_evidence(
            scenario,
            [{"name": poi.name, "type": poi.poi_type.value, 
              "lat": poi.location.lat, "lng": poi.location.lng,
              "poi_id": poi.poi_id, "address": poi.address} for poi in evidence_pois],
            evidence_count
        )
        
        # ゲームセッション作成
        game_id = str(uuid.uuid4())
        game_session = GameSession(
            game_id=game_id,
            player_id=player_id,
            difficulty=difficulty,
            scenario=scenario,
            evidence_list=evidence_list,
            player_location=player_location
        )
        
        # データベースに保存
        await database_service.save_game_session(game_session.game_id, self._serialize_game_session(game_session))
        
        return game_session
    
    async def get_game_session(self, game_id: str) -> Optional[GameSession]:
        """ゲームセッションを取得"""
        
        game_data = await database_service.get_game_session(game_id)
        if not game_data:
            return None
        
        return self._deserialize_game_session(game_data)

    async def _validate_game_session(
        self,
        game_id: str,
        player_id: str
    ) -> Tuple[Optional[GameSession], Optional[EvidenceDiscoveryResult]]:
        """
        ゲームセッションの検証
        
        Returns:
            tuple: (game_session, error_result) 
                   エラーの場合は(None, error_result)を返す
        """
        game_session = await self.get_game_session(game_id)
        if not game_session:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "ゲームセッションが見つかりません"
            )
        
        if game_session.player_id != player_id:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "プレイヤーIDが一致しません"
            )
        
        if game_session.status != GameStatus.ACTIVE:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "ゲームは終了しています"
            )
        
        return game_session, None
    
    async def _validate_evidence(
        self,
        game_session: GameSession,
        evidence_id: str
    ) -> Tuple[Optional[Evidence], Optional[EvidenceDiscoveryResult]]:
        """
        証拠の検証
        
        Returns:
            tuple: (evidence, error_result)
                   エラーの場合は(None, error_result)を返す
        """
        # 証拠が既に発見済みかチェック
        if evidence_id in game_session.discovered_evidence:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "この証拠は既に発見済みです"
            )
        
        # 該当証拠を検索
        evidence = None
        for ev in game_session.evidence_list:
            if ev.evidence_id == evidence_id:
                evidence = ev
                break
        
        if not evidence:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "指定された証拠が見つかりません"
            )
        
        return evidence, None
    
    async def _validate_distance_with_gps(
        self,
        gps_reading: GPSReading,
        evidence: Evidence,
        player_id: str,
        game_session: GameSession
    ) -> Tuple[float, Optional[EvidenceDiscoveryResult]]:
        """
        GPS検証付き距離チェック
        
        Returns:
            tuple: (distance, error_result)
                   成功の場合は(distance, None)を返す
        """
        # 高度なGPS検証
        validation_result = gps_service.validate_evidence_discovery(
            gps_reading, evidence.location, player_id
        )
        
        # GPS偽造検出
        spoofing_check = gps_service.detect_gps_spoofing(gps_reading, player_id)
        if spoofing_check["is_likely_spoofed"]:
            return validation_result.distance_to_target, EvidenceDiscoveryResult.failure_result(
                validation_result.distance_to_target,
                "位置情報に問題があります。GPS設定を確認してください。"
            )
        
        # 検証失敗の場合
        if not validation_result.is_valid:
            # 適応的な発見半径を計算
            adaptive_radius = gps_service.calculate_adaptive_discovery_radius(
                gps_reading, evidence.location, evidence.poi_type
            )
            
            return validation_result.distance_to_target, EvidenceDiscoveryResult.failure_result(
                validation_result.distance_to_target,
                f"証拠から{validation_result.distance_to_target:.1f}m離れています。"
                f"GPS精度: {gps_reading.accuracy.horizontal_accuracy:.1f}m "
                f"（{adaptive_radius:.1f}m以内に近づいてください）"
            )
        
        return validation_result.distance_to_target, None
    
    async def _validate_distance_simple(
        self,
        player_location: Location,
        evidence: Evidence,
        game_session: GameSession
    ) -> Tuple[float, Optional[EvidenceDiscoveryResult]]:
        """
        単純な距離チェック（GPS情報なしのフォールバック）
        
        Returns:
            tuple: (distance, error_result)
                   成功の場合は(distance, None)を返す
        """
        distance = player_location.distance_to(evidence.location)
        if distance > game_session.game_rules.discovery_radius:
            return distance, EvidenceDiscoveryResult.failure_result(
                distance, 
                f"証拠から{distance:.1f}m離れています。{game_session.game_rules.discovery_radius}m以内に近づいてください。"
            )
        return distance, None
    
    async def _process_evidence_discovery(
        self,
        game_session: GameSession,
        evidence: Evidence,
        evidence_id: str,
        distance: float
    ) -> EvidenceDiscoveryResult:
        """
        証拠発見処理の実行
        
        Returns:
            EvidenceDiscoveryResult: 発見結果
        """
        # 証拠発見処理
        game_session.discover_evidence(evidence_id)
        evidence.discover()
        
        # 次のヒント生成（オプション）
        next_clue = await self._generate_next_clue(game_session, evidence)
        
        # データベース更新
        await database_service.update_game_session(game_session.game_id, {
            "discovered_evidence": game_session.discovered_evidence,
            "last_activity": datetime.now()
        })
        
        return EvidenceDiscoveryResult.success_result(
            evidence, distance, next_clue
        )
    
    async def discover_evidence(
        self,
        game_id: str,
        player_id: str,
        player_location: Location,
        evidence_id: str,
        gps_reading: Optional[GPSReading] = None
    ) -> EvidenceDiscoveryResult:
        """
        証拠発見処理（GPS検証付き）
        
        Args:
            game_id: ゲームID
            player_id: プレイヤーID 
            player_location: プレイヤー現在位置
            evidence_id: 証拠ID
            gps_reading: GPS読み取り情報（精度情報含む）
        
        Returns:
            EvidenceDiscoveryResult: 発見結果
        """
        
        # ゲームセッションの検証
        game_session, error = await self._validate_game_session(game_id, player_id)
        if error:
            return error
        
        # 証拠の検証
        evidence, error = await self._validate_evidence(game_session, evidence_id)
        if error:
            return error
        
        # 距離検証
        if gps_reading:
            distance, error = await self._validate_distance_with_gps(
                gps_reading, evidence, player_id, game_session
            )
            if error:
                return error
        else:
            distance, error = await self._validate_distance_simple(
                player_location, evidence, game_session
            )
            if error:
                return error
        
        # 証拠発見処理の実行
        return await self._process_evidence_discovery(
            game_session, evidence, evidence_id, distance
        )
    
    async def submit_deduction(
        self,
        request: DeductionRequest
    ) -> DeductionResult:
        """
        推理回答を提出し判定
        
        Args:
            request: 推理リクエスト
        
        Returns:
            DeductionResult: 判定結果
        """
        
        # ゲームセッション取得
        game_session = await self.get_game_session(request.game_id)
        if not game_session:
            raise ValueError("ゲームセッションが見つかりません")
        
        if game_session.player_id != request.player_id:
            raise ValueError("プレイヤーIDが一致しません")
        
        if game_session.status != GameStatus.ACTIVE:
            raise ValueError("ゲームは終了しています")
        
        # 推理判定
        is_correct = game_session.scenario.is_culprit(request.suspect_name)
        
        # キャラクター反応生成
        reactions = await ai_service.judge_deduction(
            game_session.scenario,
            request.suspect_name,
            request.reasoning
        )
        
        # スコア計算
        progress = game_session.progress
        score = GameScore.calculate_score(
            evidence_found=progress.discovered_count,
            total_evidence=progress.total_evidence,
            correct_deduction=is_correct,
            time_elapsed=progress.time_elapsed,
            difficulty=game_session.difficulty,
            hints_used=progress.hints_used,
            discovery_bonus=0  # 証拠発見時に加算済み
        )
        
        # ゲーム完了処理
        game_session.complete_game(score)
        
        # データベース更新
        await database_service.update_game_session(game_session.game_id, {
            "status": "completed",
            "completed_at": game_session.completed_at,
            "final_score": score.total_score
        })
        
        # 履歴保存
        await self._save_game_history(game_session)
        
        return DeductionResult(
            correct=is_correct,
            culprit=game_session.scenario.culprit,
            reactions=reactions,
            game_completed=True,
            score=score,
            explanation=f"真犯人は{game_session.scenario.culprit}でした。動機: {game_session.scenario.motive}"
        )
    
    async def get_player_nearby_evidence(
        self,
        game_id: str,
        player_location: Location
    ) -> List[Evidence]:
        """プレイヤー付近の未発見証拠を取得"""
        
        game_session = await self.get_game_session(game_id)
        if not game_session:
            return []
        
        return game_session.is_evidence_nearby(player_location)
    
    def _get_suspect_count_range(self, difficulty: Difficulty) -> Tuple[int, int]:
        """難易度に応じた容疑者数範囲を取得"""
        ranges = {
            Difficulty.EASY: (3, 4),
            Difficulty.NORMAL: (4, 6),
            Difficulty.HARD: (6, 8)
        }
        return ranges.get(difficulty, (4, 6))
    
    def _get_evidence_count(self, difficulty: Difficulty) -> int:
        """難易度に応じた証拠数を取得"""
        counts = {
            Difficulty.EASY: 3,
            Difficulty.NORMAL: 5,
            Difficulty.HARD: 7
        }
        return counts.get(difficulty, 5)
    
    async def _generate_next_clue(
        self,
        game_session: GameSession,
        discovered_evidence: Evidence
    ) -> Optional[str]:
        """次のヒントを生成"""
        
        remaining = game_session.remaining_evidence
        if not remaining:
            return "全ての証拠を発見しました。推理を始めましょう。"
        
        # 簡単なヒント生成
        if len(remaining) == 1:
            next_evidence = remaining[0]
            return f"最後の証拠は{next_evidence.poi_name}の近くにありそうです。"
        elif len(remaining) <= 3:
            locations = [ev.poi_name for ev in remaining[:2]]
            return f"残りの証拠は{', '.join(locations)}周辺を探してみてください。"
        
        return None
    
    async def _save_game_history(self, game_session: GameSession) -> None:
        """ゲーム履歴を保存"""
        
        if not game_session.completed_at or not game_session.final_score:
            return
        
        duration = int((game_session.completed_at - game_session.created_at).total_seconds())
        
        history_data = {
            "game_id": game_session.game_id,
            "player_id": game_session.player_id,
            "title": game_session.scenario.title,
            "completed_at": game_session.completed_at,
            "score": game_session.final_score.total_score,
            "difficulty": game_session.difficulty.value,
            "location_name": "現在地周辺",  # 実装時により詳細に
            "duration": duration,
            "evidence_found_rate": (
                game_session.final_score.evidence_found / 
                game_session.final_score.total_evidence
            )
        }
        
        await database_service.save_game_history(
            f"{game_session.game_id}_history",
            history_data
        )
    
    def _serialize_game_session(self, game_session: GameSession) -> Dict[str, Any]:
        """GameSessionをFirestore保存用に変換"""
        return game_session.dict()
    
    def _deserialize_game_session(self, data: Dict[str, Any]) -> GameSession:
        """FirestoreデータからGameSessionを復元"""
        return GameSession(**data)


# グローバルゲームサービスインスタンス  
game_service = GameService()