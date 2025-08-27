"""
ルート生成・ナビゲーション関連のデータモデル
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .location import Location


class RouteSegmentType(str, Enum):
    """ルート区間タイプ"""
    STRAIGHT = "straight"          # 直進
    TURN_LEFT = "turn_left"        # 左折
    TURN_RIGHT = "turn_right"      # 右折
    ROUNDABOUT = "roundabout"      # ラウンドアバウト
    STAIRS = "stairs"              # 階段
    CROSSWALK = "crosswalk"        # 横断歩道


class RouteSegment(BaseModel):
    """ルート区間情報"""
    
    start_location: Location = Field(..., description="区間開始地点")
    end_location: Location = Field(..., description="区間終了地点")
    distance: float = Field(..., description="区間距離（メートル）")
    duration: int = Field(..., description="推定所要時間（秒）")
    instruction: str = Field(..., description="道案内指示")
    segment_type: RouteSegmentType = Field(RouteSegmentType.STRAIGHT, description="区間タイプ")
    polyline: Optional[str] = Field(None, description="Google Maps ポリライン")


class RouteSafetyInfo(BaseModel):
    """ルート安全性情報"""
    
    pedestrian_friendly_score: float = Field(..., description="歩行者適合性スコア（0-1）")
    lighting_score: float = Field(..., description="照明スコア（0-1）")  
    traffic_safety_score: float = Field(..., description="交通安全スコア（0-1）")
    sidewalk_coverage: float = Field(..., description="歩道整備率（0-1）")
    warnings: List[str] = Field(default_factory=list, description="安全性警告リスト")


class OptimalRoute(BaseModel):
    """最適ルート"""
    
    route_id: str = Field(..., description="ルートID")
    waypoints: List[Location] = Field(..., description="順序付きのルート地点")
    total_distance: float = Field(..., description="総歩行距離（メートル）")
    estimated_time: int = Field(..., description="推定時間（分）")
    safety_score: float = Field(..., description="安全性スコア（0-1）")
    segments: List[RouteSegment] = Field(default_factory=list, description="ルート区間詳細")
    safety_info: Optional[RouteSafetyInfo] = Field(None, description="安全性詳細情報")
    created_at: datetime = Field(default_factory=datetime.now, description="生成時刻")
    
    @property
    def is_suitable_for_walking(self) -> bool:
        """ウォーキングに適しているかを判定"""
        return (
            1500 <= self.total_distance <= 3000 and  # 1.5km-3km
            20 <= self.estimated_time <= 45 and      # 20-45分
            self.safety_score >= 0.6                 # 安全性60%以上
        )
    
    @property
    def average_speed(self) -> float:
        """平均歩行速度（m/s）を計算"""
        if self.estimated_time == 0:
            return 0.0
        return self.total_distance / (self.estimated_time * 60)


class RouteCandidate(BaseModel):
    """ルート候補"""
    
    candidate_id: str = Field(..., description="候補ID")
    route: OptimalRoute = Field(..., description="ルート詳細")
    selection_score: float = Field(..., description="選択評価スコア（0-1）")
    generation_method: str = Field(..., description="生成方法")
    
    
class RouteGenerationRequest(BaseModel):
    """ルート生成リクエスト"""
    
    start_location: Location = Field(..., description="開始地点")
    evidence_locations: List[Location] = Field(..., description="証拠地点リスト（3個）")
    user_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="ユーザー設定（距離制限・安全性重視等）"
    )
    difficulty_level: str = Field("normal", description="難易度レベル")
    
    @property
    def total_locations(self) -> List[Location]:
        """全地点を順序付きで取得（開始地点含む）"""
        return [self.start_location] + self.evidence_locations


class RouteGenerationResult(BaseModel):
    """ルート生成結果"""
    
    success: bool = Field(..., description="生成成功フラグ")
    optimal_route: Optional[OptimalRoute] = Field(None, description="最適ルート")
    alternative_routes: List[RouteCandidate] = Field(
        default_factory=list, 
        description="代替ルート候補"
    )
    generation_time_ms: int = Field(..., description="生成時間（ミリ秒）")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")


# TSPアルゴリズム関連モデル

class TSPSolution(BaseModel):
    """TSP解結果"""
    
    visit_order: List[int] = Field(..., description="訪問順序（インデックス）")
    total_distance: float = Field(..., description="総距離")
    computation_time_ms: int = Field(..., description="計算時間（ミリ秒）")
    algorithm_used: str = Field(..., description="使用アルゴリズム")
    
    def get_ordered_locations(self, locations: List[Location]) -> List[Location]:
        """訪問順序に基づいて地点を並べ替え"""
        return [locations[i] for i in self.visit_order]