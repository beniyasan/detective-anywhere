"""
ゲーム関連のデータモデル
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .scenario import Scenario
from .evidence import Evidence, EvidenceDiscoveryResult
from .character import CharacterReaction
from .location import Location


class GameStatus(str, Enum):
    """ゲーム状態"""
    ACTIVE = "active"           # 進行中
    COMPLETED = "completed"     # 完了
    ABANDONED = "abandoned"     # 放棄
    EXPIRED = "expired"         # 期限切れ


class Difficulty(str, Enum):
    """難易度"""
    EASY = "easy"       # 容疑者3-4名、証拠3-4個、シンプル
    NORMAL = "normal"   # 容疑者4-6名、証拠4-6個、適度な複雑さ
    HARD = "hard"       # 容疑者6-8名、証拠5-8個、高い複雑さ


class GameRules(BaseModel):
    """ゲームルール設定"""
    
    discovery_radius: float = Field(default=50.0, description="証拠発見半径（メートル）")
    time_limit: Optional[int] = Field(None, description="制限時間（秒）")
    max_evidence: int = Field(default=8, description="最大証拠数")
    hint_enabled: bool = Field(default=True, description="ヒント機能有効")
    allow_multiple_attempts: bool = Field(default=False, description="複数回答許可")


class GameProgress(BaseModel):
    """ゲーム進行状況"""
    
    total_evidence: int = Field(..., description="総証拠数")
    discovered_count: int = Field(..., description="発見済み証拠数")
    completion_rate: float = Field(..., ge=0.0, le=1.0, description="完了率")
    hints_used: int = Field(default=0, description="使用したヒント数")
    time_elapsed: int = Field(default=0, description="経過時間（秒）")
    
    @property
    def remaining_evidence(self) -> int:
        """未発見証拠数"""
        return self.total_evidence - self.discovered_count
    
    @property
    def is_all_evidence_found(self) -> bool:
        """全証拠発見済みか"""
        return self.discovered_count >= self.total_evidence


class GameScore(BaseModel):
    """ゲーム得点"""
    
    evidence_found: int = Field(..., description="発見した証拠数")
    total_evidence: int = Field(..., description="総証拠数")
    correct_deduction: bool = Field(..., description="推理正解フラグ")
    discovery_bonus: int = Field(default=0, description="発見ボーナス")
    time_bonus: int = Field(default=0, description="時間ボーナス")
    difficulty_multiplier: float = Field(default=1.0, description="難易度倍率")
    hints_penalty: int = Field(default=0, description="ヒント使用ペナルティ")
    total_score: int = Field(..., description="総得点")
    
    @classmethod
    def calculate_score(
        cls,
        evidence_found: int,
        total_evidence: int,
        correct_deduction: bool,
        time_elapsed: int,
        difficulty: Difficulty,
        hints_used: int = 0,
        discovery_bonus: int = 0
    ) -> "GameScore":
        """得点を計算"""
        
        # 基礎点
        evidence_score = (evidence_found / total_evidence) * 50
        deduction_score = 50 if correct_deduction else 0
        
        # 時間ボーナス（10分以内で満点、それ以降は減点）
        time_bonus = max(0, (600 - time_elapsed) // 60) * 2
        
        # 難易度倍率
        difficulty_multipliers = {
            Difficulty.EASY: 1.0,
            Difficulty.NORMAL: 1.2,
            Difficulty.HARD: 1.5
        }
        multiplier = difficulty_multipliers.get(difficulty, 1.0)
        
        # ヒント使用ペナルティ
        hints_penalty = hints_used * 5
        
        # 総得点計算
        base_score = evidence_score + deduction_score + discovery_bonus
        total_score = int((base_score + time_bonus - hints_penalty) * multiplier)
        total_score = max(0, total_score)  # 負の値を防ぐ
        
        return cls(
            evidence_found=evidence_found,
            total_evidence=total_evidence,
            correct_deduction=correct_deduction,
            discovery_bonus=discovery_bonus,
            time_bonus=int(time_bonus),
            difficulty_multiplier=multiplier,
            hints_penalty=hints_penalty,
            total_score=total_score
        )


class GameSession(BaseModel):
    """ゲームセッション"""
    
    game_id: str = Field(..., description="ゲームID")
    player_id: str = Field(..., description="プレイヤーID")
    status: GameStatus = Field(default=GameStatus.ACTIVE, description="ゲーム状態")
    difficulty: Difficulty = Field(..., description="難易度")
    scenario: Scenario = Field(..., description="事件シナリオ")
    evidence_list: List[Evidence] = Field(..., description="証拠リスト")
    discovered_evidence: List[str] = Field(default=[], description="発見済み証拠IDリスト")
    player_location: Location = Field(..., description="プレイヤー現在位置")
    game_rules: GameRules = Field(default_factory=GameRules, description="ゲームルール")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    final_score: Optional[GameScore] = Field(None, description="最終得点")
    
    class Config:
        json_encoders = {
            GameStatus: lambda v: v.value,
            Difficulty: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def progress(self) -> GameProgress:
        """ゲーム進行状況を取得"""
        time_elapsed = int((datetime.now() - self.created_at).total_seconds())
        
        return GameProgress(
            total_evidence=len(self.evidence_list),
            discovered_count=len(self.discovered_evidence),
            completion_rate=len(self.discovered_evidence) / len(self.evidence_list),
            time_elapsed=time_elapsed
        )
    
    @property
    def remaining_evidence(self) -> List[Evidence]:
        """未発見証拠リストを取得"""
        return [
            evidence for evidence in self.evidence_list
            if evidence.evidence_id not in self.discovered_evidence
        ]
    
    def discover_evidence(self, evidence_id: str) -> bool:
        """証拠を発見済みにマーク"""
        if evidence_id not in self.discovered_evidence:
            self.discovered_evidence.append(evidence_id)
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete_game(self, score: GameScore) -> None:
        """ゲームを完了状態にする"""
        self.status = GameStatus.COMPLETED
        self.completed_at = datetime.now()
        self.final_score = score
        self.updated_at = datetime.now()
    
    def is_evidence_nearby(self, player_location: Location) -> List[Evidence]:
        """プレイヤー付近の証拠を検索"""
        nearby_evidence = []
        for evidence in self.remaining_evidence:
            distance = player_location.distance_to(evidence.location)
            if distance <= self.game_rules.discovery_radius:
                nearby_evidence.append(evidence)
        return nearby_evidence


class DeductionRequest(BaseModel):
    """推理回答リクエスト"""
    
    game_id: str = Field(..., description="ゲームID")
    player_id: str = Field(..., description="プレイヤーID")
    suspect_name: str = Field(..., description="推理した犯人名")
    reasoning: Optional[str] = Field(None, description="推理の根拠")


class DeductionResult(BaseModel):
    """推理判定結果"""
    
    correct: bool = Field(..., description="正解フラグ")
    culprit: str = Field(..., description="真犯人名")
    reactions: List[CharacterReaction] = Field(..., description="キャラクター反応リスト")
    game_completed: bool = Field(..., description="ゲーム完了フラグ")
    score: GameScore = Field(..., description="得点情報")
    explanation: Optional[str] = Field(None, description="解説文")


class GameHistory(BaseModel):
    """ゲーム履歴"""
    
    game_id: str = Field(..., description="ゲームID")
    title: str = Field(..., description="事件タイトル")
    completed_at: datetime = Field(..., description="完了日時")
    score: int = Field(..., description="得点")
    difficulty: Difficulty = Field(..., description="難易度")
    location_name: str = Field(..., description="プレイ場所")
    duration: int = Field(..., description="プレイ時間（秒）")
    evidence_found_rate: float = Field(..., description="証拠発見率")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Difficulty: lambda v: v.value
        }