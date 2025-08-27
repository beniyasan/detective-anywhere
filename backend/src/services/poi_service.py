"""
Google Maps Places APIを使用してPOI情報を取得するサービス
"""

import os
import json
import random
import aiohttp
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class POI:
    """POI (Point of Interest) データクラス"""
    name: str
    location: Tuple[float, float]  # (lat, lng)
    place_type: str
    address: Optional[str] = None
    place_id: Optional[str] = None


class POIService:
    """Google Maps Places APIを使用してPOI情報を取得"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self.api_key = api_key
        else:
            from ..config.settings import get_settings
            settings = get_settings()
            self.api_key = settings.api.google_maps_api_key
        self.places_api_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
    async def get_nearby_pois(
        self, 
        lat: float, 
        lng: float, 
        radius: int = 500,  # デフォルトを500mに変更
        poi_types: Optional[List[str]] = None
    ) -> List[POI]:
        """
        指定座標周辺のPOIを取得
        
        Args:
            lat: 緯度
            lng: 経度
            radius: 検索半径（メートル）
            poi_types: 検索するPOIタイプのリスト
        
        Returns:
            POIのリスト
        """
        
        # APIキーがない場合はフォールバック
        if not self.api_key:
            return self._get_fallback_pois(lat, lng, radius)
        
        # POIタイプのデフォルト設定
        if not poi_types:
            poi_types = [
                'cafe', 'restaurant', 'park', 'convenience_store',
                'shopping_mall', 'museum', 'train_station', 'bus_station'
            ]
        
        all_pois = []
        
        async with aiohttp.ClientSession() as session:
            for poi_type in poi_types:
                params = {
                    'location': f'{lat},{lng}',
                    'radius': radius,
                    'type': poi_type,
                    'key': self.api_key,
                    'language': 'ja'
                }
                
                try:
                    async with session.get(self.places_api_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for place in data.get('results', [])[:3]:  # 各タイプから最大3件
                                poi = POI(
                                    name=place.get('name'),
                                    location=(
                                        place['geometry']['location']['lat'],
                                        place['geometry']['location']['lng']
                                    ),
                                    place_type=poi_type,
                                    address=place.get('vicinity'),
                                    place_id=place.get('place_id')
                                )
                                all_pois.append(poi)
                                
                except Exception as e:
                    print(f"Error fetching POIs for type {poi_type}: {e}")
                    continue
        
        # POIが少ない場合はフォールバックを追加
        if len(all_pois) < 3:
            fallback_pois = self._get_fallback_pois(lat, lng, radius)
            all_pois.extend(fallback_pois[:3 - len(all_pois)])
        
        return all_pois[:9]  # 最大9件まで返す
    
    def _get_fallback_pois(self, lat: float, lng: float, radius: int) -> List[POI]:
        """
        APIが使用できない場合のフォールバックPOI生成
        
        Args:
            lat: 中心緯度
            lng: 中心経度
            radius: 半径（メートル）
        
        Returns:
            仮想的なPOIのリスト
        """
        import math
        
        fallback_names = [
            ("カフェ", "cafe"),
            ("コンビニ", "convenience_store"),
            ("公園", "park"),
            ("駐車場", "parking"),
            ("バス停", "bus_station"),
            ("交差点", "intersection"),
            ("商店", "store"),
            ("レストラン", "restaurant"),
            ("自動販売機", "vending_machine")
        ]
        
        pois = []
        for i, (name_base, poi_type) in enumerate(random.sample(fallback_names, min(9, len(fallback_names)))):
            # ランダムな距離と方向で配置（より近い範囲に）
            distance = random.uniform(radius * 0.2, radius * 0.8)  # 範囲の20%〜80%
            angle = (i * 40 + random.uniform(-20, 20)) * math.pi / 180  # 40度ずつ分散
            
            # 新しい座標を計算
            lat_offset = (distance / 111000) * math.cos(angle)
            lng_offset = (distance / (111000 * math.cos(math.radians(lat)))) * math.sin(angle)
            
            poi = POI(
                name=f"{name_base} ({int(distance)}m先)",
                location=(lat + lat_offset, lng + lng_offset),
                place_type=poi_type,
                address=f"約{int(distance)}m先"
            )
            pois.append(poi)
        
        return pois
    
    async def get_evidence_locations(
        self,
        center_lat: float,
        center_lng: float,
        evidence_count: int = 3,
        min_distance: int = 100,  # 100m以上
        max_distance: int = 500   # 500m以内
    ) -> List[Dict]:
        """
        証拠配置用のPOI情報を取得
        
        Args:
            center_lat: 中心緯度
            center_lng: 中心経度
            evidence_count: 証拠の数
            min_distance: 最小距離（メートル）
            max_distance: 最大距離（メートル）
        
        Returns:
            証拠配置情報のリスト
        """
        # POIを取得
        pois = await self.get_nearby_pois(
            center_lat, 
            center_lng, 
            max_distance,
            ['cafe', 'restaurant', 'park', 'convenience_store', 'shopping_mall']
        )
        
        # POIが足りない場合は追加生成
        if len(pois) < evidence_count:
            fallback_pois = self._get_fallback_pois(center_lat, center_lng, max_distance)
            pois.extend(fallback_pois[:evidence_count - len(pois)])
        
        # ランダムに選択
        selected_pois = random.sample(pois, min(evidence_count, len(pois)))
        
        evidence_locations = []
        for poi in selected_pois:
            evidence_locations.append({
                'poi_name': poi.name,
                'lat': poi.location[0],
                'lng': poi.location[1],
                'place_type': poi.place_type,
                'address': poi.address
            })
        
        return evidence_locations