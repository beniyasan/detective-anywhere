"""
POI（興味のある場所）サービス - Google Maps API連携
"""

from typing import List, Dict, Any, Optional, Tuple
import googlemaps
from geopy import distance
import asyncio
import random

from ..core.config import settings
from ..config.secrets import get_api_key
from ...shared.models.location import Location, POI, POIType


class POIService:
    """POI サービス"""
    
    def __init__(self):
        self.gmaps = None
        self.poi_type_mapping = {
            # Google Places APIのタイプをPOITypeにマッピング
            "restaurant": POIType.RESTAURANT,
            "cafe": POIType.CAFE,
            "park": POIType.PARK,
            "tourist_attraction": POIType.LANDMARK,
            "subway_station": POIType.STATION,
            "train_station": POIType.STATION,
            "store": POIType.SHOP,
            "shopping_mall": POIType.SHOP,
            "school": POIType.SCHOOL,
            "hospital": POIType.HOSPITAL,
            "library": POIType.LIBRARY,
            "museum": POIType.LIBRARY,
        }
    
    def initialize(self):
        """POI サービスの初期化"""
        google_maps_api_key = get_api_key('google_maps')
        if google_maps_api_key:
            self.gmaps = googlemaps.Client(key=google_maps_api_key)
        else:
            raise ValueError("Google Maps API キーが設定されていません")
    
    async def find_nearby_pois(
        self,
        location: Location,
        radius: int = 1000,
        poi_types: Optional[List[str]] = None,
        min_count: int = 5
    ) -> List[POI]:
        """
        指定位置周辺のPOIを検索
        
        Args:
            location: 中心位置
            radius: 検索半径（メートル）
            poi_types: 検索するPOIタイプ（Noneの場合は全タイプ）
            min_count: 最小POI数（足りない場合は範囲を広げる）
        
        Returns:
            POIリスト
        """
        if not self.gmaps:
            # 開発環境用のモックデータ
            return await self._get_mock_pois(location, min_count)
        
        try:
            all_pois = []
            search_types = poi_types or list(self.poi_type_mapping.keys())
            
            # 各POIタイプで検索
            for place_type in search_types:
                pois = await asyncio.to_thread(
                    self._search_places_by_type,
                    location,
                    place_type,
                    radius
                )
                all_pois.extend(pois)
            
            # 重複除去とソート
            unique_pois = self._deduplicate_pois(all_pois)
            sorted_pois = sorted(unique_pois, key=lambda p: p.distance_from(location))
            
            # 最小数に満たない場合は範囲を拡大して再検索
            if len(sorted_pois) < min_count and radius < 5000:
                extended_pois = await self.find_nearby_pois(
                    location, radius * 2, poi_types, min_count
                )
                return extended_pois[:min_count * 2]  # 多すぎないように制限
            
            return sorted_pois[:20]  # 最大20個まで
            
        except Exception as e:
            print(f"POI検索エラー: {e}")
            return await self._get_mock_pois(location, min_count)
    
    def _search_places_by_type(
        self,
        location: Location,
        place_type: str,
        radius: int
    ) -> List[POI]:
        """指定タイプの場所を検索"""
        
        places_result = self.gmaps.places_nearby(
            location=(location.lat, location.lng),
            radius=radius,
            type=place_type,
            language='ja'
        )
        
        pois = []
        for place in places_result.get('results', []):
            poi = self._create_poi_from_place(place)
            if poi:
                pois.append(poi)
        
        return pois
    
    def _create_poi_from_place(self, place: Dict[str, Any]) -> Optional[POI]:
        """Google Places APIの結果からPOIオブジェクトを作成"""
        
        try:
            # POIタイプの決定
            poi_type = POIType.LANDMARK  # デフォルト
            for gmap_type in place.get('types', []):
                if gmap_type in self.poi_type_mapping:
                    poi_type = self.poi_type_mapping[gmap_type]
                    break
            
            # 位置情報の取得
            geometry = place.get('geometry', {})
            location_data = geometry.get('location', {})
            
            poi = POI(
                poi_id=place.get('place_id', ''),
                name=place.get('name', ''),
                poi_type=poi_type,
                location=Location(
                    lat=location_data.get('lat', 0.0),
                    lng=location_data.get('lng', 0.0)
                ),
                address=place.get('vicinity', ''),
                description=f"Rating: {place.get('rating', 'N/A')}"
            )
            
            return poi
            
        except Exception as e:
            print(f"POI作成エラー: {e}")
            return None
    
    def _deduplicate_pois(self, pois: List[POI]) -> List[POI]:
        """POIの重複除去"""
        
        seen_names = set()
        unique_pois = []
        
        for poi in pois:
            # 名前と位置が近い場合は重複とみなす
            key = f"{poi.name}_{int(poi.location.lat*1000)}_{int(poi.location.lng*1000)}"
            
            if key not in seen_names:
                seen_names.add(key)
                unique_pois.append(poi)
        
        return unique_pois
    
    async def _get_mock_pois(self, center: Location, count: int) -> List[POI]:
        """開発用モックPOIデータ"""
        
        mock_pois = []
        poi_templates = [
            {"name": "スターバックス", "type": POIType.CAFE},
            {"name": "中央公園", "type": POIType.PARK},
            {"name": "市立図書館", "type": POIType.LIBRARY},
            {"name": "ファミリーマート", "type": POIType.SHOP},
            {"name": "地下鉄駅", "type": POIType.STATION},
            {"name": "タワーレコード", "type": POIType.SHOP},
            {"name": "イタリアンレストラン", "type": POIType.RESTAURANT},
            {"name": "総合病院", "type": POIType.HOSPITAL},
            {"name": "商業ビル", "type": POIType.OFFICE},
            {"name": "歴史博物館", "type": POIType.LANDMARK}
        ]
        
        # ランダムな位置にPOIを配置
        for i in range(min(count, len(poi_templates))):
            template = poi_templates[i]
            
            # 中心から半径500m以内にランダム配置
            lat_offset = random.uniform(-0.005, 0.005)
            lng_offset = random.uniform(-0.005, 0.005)
            
            mock_poi = POI(
                poi_id=f"mock_{i+1}",
                name=f"{template['name']}_{i+1}",
                poi_type=template["type"],
                location=Location(
                    lat=center.lat + lat_offset,
                    lng=center.lng + lng_offset
                ),
                address=f"模擬住所{i+1}",
                description="開発用モックデータ"
            )
            mock_pois.append(mock_poi)
        
        return mock_pois
    
    async def get_location_context(self, location: Location) -> str:
        """位置から地域コンテキストを取得"""
        
        if not self.gmaps:
            return "東京都内の商業エリア"
        
        try:
            # リバースジオコーディング
            reverse_geocode_result = await asyncio.to_thread(
                self.gmaps.reverse_geocode,
                (location.lat, location.lng),
                language='ja'
            )
            
            if reverse_geocode_result:
                address_components = reverse_geocode_result[0].get('address_components', [])
                
                locality = ""
                sublocality = ""
                
                for component in address_components:
                    types = component.get('types', [])
                    if 'locality' in types:
                        locality = component.get('long_name', '')
                    elif 'sublocality' in types:
                        sublocality = component.get('long_name', '')
                
                context = f"{locality}{sublocality}周辺"
                return context if context.strip() else "市街地エリア"
            
        except Exception as e:
            print(f"位置コンテキスト取得エラー: {e}")
        
        return "市街地エリア"
    
    def select_evidence_pois(
        self,
        available_pois: List[POI],
        evidence_count: int
    ) -> List[POI]:
        """証拠配置に適したPOIを選択"""
        
        # 証拠配置に適したPOIを優先
        suitable_pois = [poi for poi in available_pois if poi.is_suitable_for_evidence()]
        
        if len(suitable_pois) >= evidence_count:
            # ランダムに選択（分散させるため）
            selected = random.sample(suitable_pois, evidence_count)
        else:
            # 不足分は全POIから補完
            selected = suitable_pois.copy()
            remaining = [poi for poi in available_pois if poi not in suitable_pois]
            need_more = evidence_count - len(selected)
            selected.extend(random.sample(remaining, min(need_more, len(remaining))))
        
        return selected
    
    async def validate_location(self, location: Location) -> bool:
        """位置の有効性を検証"""
        
        # 基本的な範囲チェック
        if not (-90 <= location.lat <= 90 and -180 <= location.lng <= 180):
            return False
        
        # 日本国内かチェック（大まかな範囲）
        japan_bounds = {
            "north": 45.5,
            "south": 24.0,
            "east": 146.0,
            "west": 129.0
        }
        
        if not (japan_bounds["south"] <= location.lat <= japan_bounds["north"] and
                japan_bounds["west"] <= location.lng <= japan_bounds["east"]):
            return False
        
        return True


# グローバルPOIサービスインスタンス
poi_service = POIService()