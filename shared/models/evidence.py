"""
証拠関連のデータモデル
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .location import Location


class EvidenceImportance(str, Enum):
    """証拠の重要度"""
    CRITICAL = "critical"       # 決定的証拠
    IMPORTANT = "important"     # 重要証拠
    MISLEADING = "misleading"   # ミスリード証拠
    BACKGROUND = "background"   # 背景情報


class Evidence(BaseModel):
    """証拠"""
    
    evidence_id: str = Field(..., description="証拠ID")
    name: str = Field(..., description="証拠名")
    description: str = Field(..., description="証拠の詳細説明")
    discovery_text: str = Field(..., description="発見時のテキスト")
    importance: EvidenceImportance = Field(..., description="重要度")
    location: Location = Field(..., description="発見場所")
    poi_name: str = Field(..., description="POI名")
    poi_type: str = Field(..., description="POIタイプ")
    discovered_at: Optional[datetime] = Field(None, description="発見日時")
    related_character: Optional[str] = Field(None, description="関連キャラクター名")
    clue_text: Optional[str] = Field(None, description="次のヒントテキスト")
    
    class Config:
        json_encoders = {
            EvidenceImportance: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def is_discovered(self) -> bool:
        """発見済みかどうか"""
        return self.discovered_at is not None
    
    @property
    def is_critical(self) -> bool:
        """決定的証拠かどうか"""
        return self.importance == EvidenceImportance.CRITICAL
    
    @property
    def is_misleading(self) -> bool:
        """ミスリード証拠かどうか"""
        return self.importance == EvidenceImportance.MISLEADING
    
    def discover(self) -> None:
        """証拠を発見済みにマーク"""
        if not self.is_discovered:
            self.discovered_at = datetime.now()
    
    def get_importance_description(self) -> str:
        """重要度の説明を取得"""
        descriptions = {
            EvidenceImportance.CRITICAL: "この証拠は事件解決の鍵となりそうです",
            EvidenceImportance.IMPORTANT: "重要な手がかりのようです",
            EvidenceImportance.MISLEADING: "何か違和感を感じます...",
            EvidenceImportance.BACKGROUND: "事件の背景を知る手がかりです"
        }
        return descriptions.get(self.importance, "")


class EvidenceDiscoveryResult(BaseModel):
    """証拠発見結果"""
    
    success: bool = Field(..., description="発見成功フラグ")
    evidence: Optional[Evidence] = Field(None, description="発見された証拠")
    distance: float = Field(..., description="証拠場所からの距離（メートル）")
    next_clue: Optional[str] = Field(None, description="次の手がかり")
    message: str = Field(..., description="結果メッセージ")
    discovery_bonus: int = Field(default=0, description="発見ボーナス点数")
    
    @classmethod
    def success_result(
        cls,
        evidence: Evidence,
        distance: float,
        next_clue: Optional[str] = None
    ) -> "EvidenceDiscoveryResult":
        """成功結果を作成"""
        bonus = cls._calculate_bonus(evidence.importance, distance)
        return cls(
            success=True,
            evidence=evidence,
            distance=distance,
            next_clue=next_clue,
            message=f"証拠「{evidence.name}」を発見しました！",
            discovery_bonus=bonus
        )
    
    @classmethod
    def failure_result(cls, distance: float, reason: str) -> "EvidenceDiscoveryResult":
        """失敗結果を作成"""
        return cls(
            success=False,
            evidence=None,
            distance=distance,
            next_clue=None,
            message=reason,
            discovery_bonus=0
        )
    
    @staticmethod
    def _calculate_bonus(importance: EvidenceImportance, distance: float) -> int:
        """発見ボーナス点数を計算"""
        base_scores = {
            EvidenceImportance.CRITICAL: 50,
            EvidenceImportance.IMPORTANT: 30,
            EvidenceImportance.MISLEADING: 20,
            EvidenceImportance.BACKGROUND: 10
        }
        
        base_score = base_scores.get(importance, 10)
        
        # 距離ボーナス（近いほど高い）
        if distance <= 10:
            distance_multiplier = 1.5
        elif distance <= 30:
            distance_multiplier = 1.2
        elif distance <= 50:
            distance_multiplier = 1.0
        else:
            distance_multiplier = 0.8
        
        return int(base_score * distance_multiplier)