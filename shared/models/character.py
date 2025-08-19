"""
キャラクター関連のデータモデル
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Temperament(str, Enum):
    """キャラクターの気質"""
    CALM = "calm"           # 冷静
    VOLATILE = "volatile"   # 激情的
    SARCASTIC = "sarcastic" # 皮肉屋
    DEFENSIVE = "defensive" # 虚勢
    NERVOUS = "nervous"     # 動揺


class Character(BaseModel):
    """キャラクター（容疑者・被害者・関係者）"""
    
    name: str = Field(..., description="キャラクター名")
    age: int = Field(..., ge=10, le=100, description="年齢")
    occupation: str = Field(..., description="職業")
    personality: str = Field(..., description="性格・特徴")
    temperament: Temperament = Field(..., description="気質")
    relationship: str = Field(..., description="被害者との関係")
    alibi: Optional[str] = Field(None, description="アリバイ")
    motive: Optional[str] = Field(None, description="動機")
    background: Optional[str] = Field(None, description="背景・追加情報")
    
    class Config:
        json_encoders = {
            Temperament: lambda v: v.value
        }
    
    @property
    def display_info(self) -> str:
        """表示用の基本情報"""
        return f"{self.name}（{self.age}歳・{self.occupation}）"
    
    def get_reaction_style(self) -> dict:
        """気質に基づく反応スタイルを取得"""
        styles = {
            Temperament.CALM: {
                "tone": "冷静で論理的",
                "speech_pattern": "丁寧語",
                "emotional_range": "低"
            },
            Temperament.VOLATILE: {
                "tone": "感情的で激しい",
                "speech_pattern": "感嘆符多用",
                "emotional_range": "高"
            },
            Temperament.SARCASTIC: {
                "tone": "皮肉で辛辣",
                "speech_pattern": "嫌味を含む",
                "emotional_range": "中"
            },
            Temperament.DEFENSIVE: {
                "tone": "防御的で虚勢",
                "speech_pattern": "強がり",
                "emotional_range": "中"
            },
            Temperament.NERVOUS: {
                "tone": "不安で動揺",
                "speech_pattern": "どもり・繰り返し",
                "emotional_range": "高"
            }
        }
        return styles.get(self.temperament, styles[Temperament.CALM])


class CharacterReaction(BaseModel):
    """キャラクターの反応"""
    
    character_name: str = Field(..., description="キャラクター名")
    reaction: str = Field(..., description="反応テキスト")
    reaction_type: str = Field(..., description="反応タイプ（confession/denial/surprise/praise）")
    temperament: Temperament = Field(..., description="気質")
    emotion_intensity: float = Field(..., ge=0.0, le=1.0, description="感情の強度")
    
    class Config:
        json_encoders = {
            Temperament: lambda v: v.value
        }