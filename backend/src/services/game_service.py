"""
ゲームサービス - ビジネスロジック
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.database import game_session_repo, player_repo, game_history_repo
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
        active_games = await game_session_repo.get_active_games_by_player(player_id)
        if len(active_games) >= 3:  # 最大3つまで
            raise ValueError("同時進行可能なゲーム数を超えています")
        
        # 周辺POI検索
        nearby_pois = await poi_service.find_nearby_pois(
            player_location,
            radius=1000,
            min_count=5
        )
        
        if len(nearby_pois) < 3:
            raise ValueError("この地域にはゲーム作成に十分なPOIがありません")
        
        # 地域コンテキスト取得
        location_context = await poi_service.get_location_context(player_location)
        
        # シナリオ生成リクエスト作成
        scenario_request = ScenarioGenerationRequest(
            difficulty=difficulty.value,
            location_context=location_context,
            poi_types=[poi.poi_type.value for poi in nearby_pois],
            suspect_count_range=self._get_suspect_count_range(difficulty)
        )
        
        # AIでシナリオ生成
        scenario = await ai_service.generate_mystery_scenario(scenario_request)
        
        # 証拠配置用POI選択
        evidence_count = self._get_evidence_count(difficulty)
        evidence_pois = poi_service.select_evidence_pois(nearby_pois, evidence_count)
        
        # 証拠生成
        evidence_list = await ai_service.generate_evidence(
            scenario,
            [{"name": poi.name, "type": poi.poi_type.value, 
              "lat": poi.location.lat, "lng": poi.location.lng} for poi in evidence_pois],
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
        await self._save_game_session(game_session)
        
        return game_session
    
    async def get_game_session(self, game_id: str) -> Optional[GameSession]:
        """ゲームセッションを取得"""
        
        game_data = await game_session_repo.get(game_id)
        if not game_data:
            return None
        
        return self._deserialize_game_session(game_data)
    
    async def discover_evidence(
        self,
        game_id: str,
        player_id: str,
        player_location: Location,
        evidence_id: str
    ) -> EvidenceDiscoveryResult:
        """
        証拠発見処理
        
        Args:
            game_id: ゲームID
            player_id: プレイヤーID 
            player_location: プレイヤー現在位置
            evidence_id: 証拠ID
        
        Returns:
            EvidenceDiscoveryResult: 発見結果
        """
        
        # ゲームセッション取得
        game_session = await self.get_game_session(game_id)
        if not game_session:
            return EvidenceDiscoveryResult.failure_result(
                0.0, "ゲームセッションが見つかりません"
            )
        
        if game_session.player_id != player_id:
            return EvidenceDiscoveryResult.failure_result(
                0.0, "プレイヤーIDが一致しません"
            )
        
        if game_session.status != GameStatus.ACTIVE:
            return EvidenceDiscoveryResult.failure_result(
                0.0, "ゲームは終了しています"
            )
        
        # 証拠が既に発見済みかチェック
        if evidence_id in game_session.discovered_evidence:
            return EvidenceDiscoveryResult.failure_result(
                0.0, "この証拠は既に発見済みです"
            )
        
        # 該当証拠を検索
        evidence = None
        for ev in game_session.evidence_list:
            if ev.evidence_id == evidence_id:
                evidence = ev
                break
        
        if not evidence:
            return EvidenceDiscoveryResult.failure_result(
                0.0, "指定された証拠が見つかりません"
            )
        
        # 距離チェック
        distance = player_location.distance_to(evidence.location)
        if distance > game_session.game_rules.discovery_radius:
            return EvidenceDiscoveryResult.failure_result(
                distance, 
                f"証拠から{distance:.1f}m離れています。{game_session.game_rules.discovery_radius}m以内に近づいてください。"
            )
        
        # 証拠発見処理
        game_session.discover_evidence(evidence_id)
        evidence.discover()
        
        # 次のヒント生成（オプション）
        next_clue = await self._generate_next_clue(game_session, evidence)
        
        # データベース更新
        await self._save_game_session(game_session)
        
        return EvidenceDiscoveryResult.success_result(
            evidence, distance, next_clue
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
        await self._save_game_session(game_session)
        
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
    
    def _get_suspect_count_range(self, difficulty: Difficulty) -> tuple[int, int]:
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
    
    async def _save_game_session(self, game_session: GameSession):
        """ゲームセッションをデータベースに保存"""
        
        game_data = self._serialize_game_session(game_session)
        await game_session_repo.create(game_session.game_id, game_data)
    
    async def _save_game_history(self, game_session: GameSession):
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
        
        await game_history_repo.create(
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