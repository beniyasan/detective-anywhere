"""
シナリオ関連のデータモデル
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .character import Character


class Scenario(BaseModel):
    """事件シナリオ"""
    
    title: str = Field(..., description="事件タイトル")
    description: str = Field(..., description="事件の導入文（200-500字）")
    victim: Character = Field(..., description="被害者")
    suspects: List[Character] = Field(..., min_items=3, max_items=8, description="容疑者リスト")
    culprit: str = Field(..., description="真犯人の名前")
    motive: str = Field(..., description="犯行動機")
    method: str = Field(..., description="犯行手口")
    timeline: List[str] = Field(..., description="事件の時系列")
    theme: Optional[str] = Field(None, description="テーマ（人間ドラマ、時系列複雑等）")
    difficulty_factors: List[str] = Field(default=[], description="難易度要素")
    red_herrings: List[str] = Field(default=[], description="ミスリード要素")
    
    @property
    def suspect_count(self) -> int:
        """容疑者数"""
        return len(self.suspects)
    
    @property
    def culprit_character(self) -> Optional[Character]:
        """真犯人のキャラクター情報を取得"""
        for suspect in self.suspects:
            if suspect.name == self.culprit:
                return suspect
        return None
    
    def get_suspect_by_name(self, name: str) -> Optional[Character]:
        """名前で容疑者を検索"""
        for suspect in self.suspects:
            if suspect.name == name:
                return suspect
        return None
    
    def get_all_characters(self) -> List[Character]:
        """全キャラクター（被害者+容疑者）を取得"""
        return [self.victim] + self.suspects
    
    def is_culprit(self, suspect_name: str) -> bool:
        """指定した名前が真犯人かチェック"""
        return self.culprit == suspect_name
    
    def validate_culprit(self) -> bool:
        """真犯人が容疑者リストに含まれているかチェック"""
        return any(suspect.name == self.culprit for suspect in self.suspects)


class ScenarioGenerationRequest(BaseModel):
    """シナリオ生成リクエスト"""
    
    difficulty: str = Field(..., description="難易度")
    location_context: str = Field(..., description="場所の文脈情報")
    poi_types: List[str] = Field(..., description="利用可能なPOIタイプ")
    theme_preference: Optional[str] = Field(None, description="テーマの希望")
    suspect_count_range: tuple[int, int] = Field((3, 6), description="容疑者数の範囲")
    
    class Config:
        # tupleをリストとして扱う
        json_encoders = {
            tuple: lambda v: list(v)
        }


class ScenarioTemplate(BaseModel):
    """シナリオテンプレート（AI生成用）"""
    
    template_id: str = Field(..., description="テンプレートID")
    name: str = Field(..., description="テンプレート名")
    genre: str = Field(..., description="ジャンル（殺人、窃盗、詐欺等）")
    setting_types: List[str] = Field(..., description="適用可能な場所タイプ")
    character_archetypes: List[dict] = Field(..., description="キャラクター原型")
    plot_structure: dict = Field(..., description="プロット構造")
    evidence_patterns: List[dict] = Field(..., description="証拠パターン")
    
    def is_suitable_for_location(self, poi_types: List[str]) -> bool:
        """指定されたPOIタイプに適用可能かチェック"""
        return any(setting in poi_types for setting in self.setting_types)


class StoryTheme(BaseModel):
    """ストーリーテーマ"""
    
    theme_id: str = Field(..., description="テーマID")
    name: str = Field(..., description="テーマ名")
    description: str = Field(..., description="テーマ説明")
    complexity_factors: List[str] = Field(..., description="複雑さ要因")
    narrative_focus: str = Field(..., description="物語の焦点")
    
    # テーマ例
    HUMAN_DRAMA = "human_drama"      # 人間ドラマ重視
    TIME_COMPLEX = "time_complex"    # 時系列の複雑さ
    MISDIRECTION = "misdirection"    # ミスリード重視
    PSYCHOLOGICAL = "psychological"  # 心理戦
    CLASSIC_WHODUNIT = "classic"     # 古典的推理