"""
位置情報・POI関連のデータモデル
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import math


class POIType(str, Enum):
    """POI（興味のある場所）のタイプ"""
    RESTAURANT = "restaurant"      # レストラン・カフェ
    PARK = "park"                  # 公園
    LANDMARK = "landmark"          # ランドマーク・観光地
    CAFE = "cafe"                  # カフェ
    STATION = "station"            # 駅
    SHOP = "shop"                  # 店舗
    OFFICE = "office"              # オフィスビル
    SCHOOL = "school"              # 学校・大学
    HOSPITAL = "hospital"          # 病院
    LIBRARY = "library"            # 図書館・文化施設


class Location(BaseModel):
    """位置情報"""
    
    lat: float = Field(..., ge=-90.0, le=90.0, description="緯度")
    lng: float = Field(..., ge=-180.0, le=180.0, description="経度")
    
    def distance_to(self, other: "Location") -> float:
        """他の位置との距離を計算（メートル）"""
        if not isinstance(other, Location):
            raise TypeError("距離計算には Location オブジェクトが必要です")
        
        # Haversine formula for calculating distance between two points on Earth
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(self.lat)
        lat2_rad = math.radians(other.lat)
        delta_lat = math.radians(other.lat - self.lat)
        delta_lng = math.radians(other.lng - self.lng)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def is_within_radius(self, other: "Location", radius: float) -> bool:
        """指定半径内にあるかチェック"""
        return self.distance_to(other) <= radius


class POI(BaseModel):
    """興味のある場所（Point of Interest）"""
    
    poi_id: str = Field(..., description="POI ID")
    name: str = Field(..., description="場所名")
    poi_type: POIType = Field(..., description="POIタイプ")
    location: Location = Field(..., description="位置情報")
    address: Optional[str] = Field(None, description="住所")
    description: Optional[str] = Field(None, description="場所の説明")
    
    class Config:
        json_encoders = {
            POIType: lambda v: v.value
        }
    
    @property
    def display_name(self) -> str:
        """表示用の名前"""
        return f"{self.name} ({self.poi_type.value})"
    
    def distance_from(self, location: Location) -> float:
        """指定位置からの距離を取得"""
        return self.location.distance_to(location)
    
    def is_suitable_for_evidence(self) -> bool:
        """証拠配置に適しているかチェック"""
        # 特定のPOIタイプは証拠配置により適している
        suitable_types = {
            POIType.RESTAURANT,
            POIType.CAFE, 
            POIType.PARK,
            POIType.LANDMARK,
            POIType.SHOP,
            POIType.LIBRARY
        }
        return self.poi_type in suitable_types


class LocationArea(BaseModel):
    """エリア情報"""
    
    center: Location = Field(..., description="中心座標")
    radius: float = Field(..., gt=0, description="半径（メートル）")
    name: Optional[str] = Field(None, description="エリア名")
    
    def contains(self, location: Location) -> bool:
        """指定位置がエリア内にあるかチェック"""
        return self.center.distance_to(location) <= self.radius
    
    def get_bounds(self) -> dict:
        """エリアの境界座標を取得"""
        # 簡略化された境界計算（正確には楕円形になる）
        lat_offset = self.radius / 111111  # 約111km per degree
        lng_offset = self.radius / (111111 * math.cos(math.radians(self.center.lat)))
        
        return {
            "north": self.center.lat + lat_offset,
            "south": self.center.lat - lat_offset,
            "east": self.center.lng + lng_offset,
            "west": self.center.lng - lng_offset
        }