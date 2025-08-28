"""
拡張POIサービス - 証拠発見機能に最適化されたGoogle Maps統合
"""

import asyncio
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import googlemaps
from geopy.distance import geodesic

from ..config.secrets import get_api_key
from ..core.logging import get_logger, LogCategory
from shared.models.location import Location, POI, POIType

logger = get_logger(__name__, LogCategory.POI_SERVICE)


class EvidencePlacementStrategy:
    """証拠配置戦略"""
    
    @staticmethod
    def calculate_poi_suitability(poi: POI, player_location: Location) -> float:
        """POIの証拠配置適性スコアを計算"""
        
        score = 0.0
        
        # POIタイプによる基本スコア
        type_scores = {
            POIType.PARK: 0.9,        # 公園は証拠配置に最適
            POIType.LANDMARK: 0.8,    # ランドマークも良い
            POIType.CAFE: 0.7,        # カフェは適度
            POIType.RESTAURANT: 0.6,  # レストランも可
            POIType.LIBRARY: 0.8,     # 図書館は良い
            POIType.SHOP: 0.5,        # 店舗は普通
            POIType.STATION: 0.4,     # 駅は混雑しがち
            POIType.HOSPITAL: 0.3,    # 病院は避けたい
            POIType.SCHOOL: 0.2,      # 学校は避けたい
        }
        
        score += type_scores.get(poi.poi_type, 0.3)
        
        # 距離による調整（近すぎず遠すぎない場所を好む）
        distance = poi.distance_from(player_location)
        if 100 <= distance <= 500:
            score += 0.2  # 理想的な距離
        elif 50 <= distance <= 1000:
            score += 0.1  # 許容範囲
        elif distance < 50:
            score -= 0.3  # 近すぎる
        elif distance > 1500:
            score -= 0.2  # 遠すぎる
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def ensure_evidence_distribution(
        pois: List[POI], 
        evidence_count: int,
        min_distance_between: float = 150.0
    ) -> List[POI]:
        """証拠間の適切な分散を確保（ランダム性追加）"""
        
        if len(pois) <= evidence_count:
            return pois
        
        # ランダムシャッフルを追加して毎回異なる選択を可能にする
        import random
        shuffled_pois = pois.copy()
        random.shuffle(shuffled_pois)
        
        selected = [shuffled_pois[0]]  # 最初のPOIを選択
        
        for poi in shuffled_pois[1:]:
            if len(selected) >= evidence_count:
                break
            
            # 既選択のPOIから十分離れているかチェック
            too_close = False
            for selected_poi in selected:
                if poi.distance_from(selected_poi.location) < min_distance_between:
                    too_close = True
                    break
            
            if not too_close:
                selected.append(poi)
        
        # まだ足りない場合は距離制限を緩めて追加
        if len(selected) < evidence_count:
            remaining = [p for p in shuffled_pois if p not in selected]
            need_more = evidence_count - len(selected)
            selected.extend(remaining[:need_more])
        
        return selected


class EnhancedPOIService:
    """拡張POIサービス"""
    
    def __init__(self):
        self.gmaps = None
        self.poi_cache: Dict[str, Tuple[List[POI], datetime]] = {}
        self.cache_duration = timedelta(minutes=30)
        
        # Google Places APIタイプマッピングを拡張
        self.place_type_mapping = {
            # 基本的な場所タイプ
            "restaurant": POIType.RESTAURANT,
            "cafe": POIType.CAFE,
            "park": POIType.PARK,
            "tourist_attraction": POIType.LANDMARK,
            "museum": POIType.LANDMARK,
            "art_gallery": POIType.LANDMARK,
            
            # 交通関連
            "subway_station": POIType.STATION,
            "train_station": POIType.STATION,
            "bus_station": POIType.STATION,
            
            # 商業施設
            "store": POIType.SHOP,
            "shopping_mall": POIType.SHOP,
            "convenience_store": POIType.SHOP,
            "book_store": POIType.LIBRARY,
            
            # 公共施設
            "library": POIType.LIBRARY,
            "school": POIType.SCHOOL,
            "university": POIType.SCHOOL,
            "hospital": POIType.HOSPITAL,
            "post_office": POIType.OFFICE,
            "bank": POIType.OFFICE,
        }
        
        # 証拠配置に推奨されるPOIタイプ
        self.evidence_preferred_types = [
            "park", "tourist_attraction", "museum", "library",
            "cafe", "restaurant", "art_gallery"
        ]
    
    async def initialize(self):
        """サービス初期化"""
        try:
            google_maps_api_key = get_api_key('google_maps')
            if google_maps_api_key:
                logger.info(f"Google Maps API key取得成功 (長さ: {len(google_maps_api_key)})")
                self.gmaps = googlemaps.Client(key=google_maps_api_key)
                logger.info("Google Maps API初期化完了")
            else:
                logger.error("Google Maps API key取得失敗 - Secret ManagerまたはCloud Run環境変数を確認してください")
                logger.warning("モックデータモードで動作します")
                
        except Exception as e:
            logger.error(f"Enhanced POI Service初期化エラー: {e}")
            logger.warning("Google Maps API初期化失敗 - モックデータモードで動作します")
    
    async def find_evidence_suitable_pois(
        self,
        center_location: Location,
        radius: int = 1000,
        evidence_count: int = 5
    ) -> List[POI]:
        """証拠配置に適したPOIを検索"""
        
        cache_key = f"{center_location.lat:.4f},{center_location.lng:.4f},{radius}"
        
        # キャッシュチェック
        if cache_key in self.poi_cache:
            cached_pois, cached_time = self.poi_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                logger.info("キャッシュされたPOIデータを使用")
                return self._select_best_evidence_pois(
                    cached_pois, center_location, evidence_count
                )
        
        try:
            if self.gmaps:
                pois = await self._search_real_pois(center_location, radius)
            else:
                pois = await self._generate_mock_pois(center_location, evidence_count * 2)
            
            # キャッシュに保存
            self.poi_cache[cache_key] = (pois, datetime.now())
            
            return self._select_best_evidence_pois(pois, center_location, evidence_count)
            
        except Exception as e:
            logger.error(f"POI検索エラー: {e}")
            return await self._generate_mock_pois(center_location, evidence_count)
    
    async def _search_real_pois(
        self,
        center_location: Location,
        radius: int
    ) -> List[POI]:
        """実際のGoogle Places APIを使用してPOIを検索"""
        
        all_pois = []
        
        # 証拠配置に適したタイプを優先的に検索
        search_types = self.evidence_preferred_types + [
            "store", "shopping_mall", "subway_station", "train_station"
        ]
        
        for place_type in search_types:
            try:
                # 非同期でGoogle Places API呼び出し
                places_result = await asyncio.to_thread(
                    self.gmaps.places_nearby,
                    location=(center_location.lat, center_location.lng),
                    radius=radius,
                    type=place_type,
                    language='ja'
                )
                
                for place in places_result.get('results', []):
                    poi = self._create_enhanced_poi(place)
                    if poi and self._is_poi_suitable_for_evidence(poi):
                        all_pois.append(poi)
                
                # レート制限対策
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"POI検索エラー (タイプ: {place_type}): {e}")
                continue
        
        # 重複除去と距離順ソート
        unique_pois = self._deduplicate_pois(all_pois)
        sorted_pois = sorted(
            unique_pois, 
            key=lambda p: p.distance_from(center_location)
        )
        
        logger.info(f"実際のPOI検索完了: {len(sorted_pois)}件")
        return sorted_pois[:30]  # 最大30件
    
    def _create_enhanced_poi(self, place: Dict[str, Any]) -> Optional[POI]:
        """Google Places APIレスポンスから拡張POIを作成"""
        
        try:
            # POIタイプの決定（より正確に）
            poi_type = self._determine_poi_type(place.get('types', []))
            
            geometry = place.get('geometry', {})
            location_data = geometry.get('location', {})
            
            # 評価やステータス情報も含める
            rating = place.get('rating', 0.0)
            business_status = place.get('business_status', 'OPERATIONAL')
            
            poi = POI(
                poi_id=place.get('place_id', ''),
                name=place.get('name', ''),
                poi_type=poi_type,
                location=Location(
                    lat=location_data.get('lat', 0.0),
                    lng=location_data.get('lng', 0.0)
                ),
                address=place.get('vicinity', ''),
                description=f"評価: {rating:.1f}/5.0, ステータス: {business_status}"
            )
            
            return poi
            
        except Exception as e:
            logger.error(f"POI作成エラー: {e}")
            return None
    
    def _determine_poi_type(self, google_types: List[str]) -> POIType:
        """Google Places APIのタイプからPOITypeを決定"""
        
        # 優先順位順にチェック
        priority_mapping = [
            (["park", "amusement_park"], POIType.PARK),
            (["tourist_attraction", "museum", "art_gallery"], POIType.LANDMARK),
            (["library"], POIType.LIBRARY),
            (["cafe", "bakery"], POIType.CAFE),
            (["restaurant", "meal_takeaway", "meal_delivery"], POIType.RESTAURANT),
            (["subway_station", "train_station", "bus_station"], POIType.STATION),
            (["store", "shopping_mall", "convenience_store"], POIType.SHOP),
            (["school", "university"], POIType.SCHOOL),
            (["hospital", "doctor"], POIType.HOSPITAL),
            (["post_office", "bank"], POIType.OFFICE),
        ]
        
        for type_list, poi_type in priority_mapping:
            if any(t in google_types for t in type_list):
                return poi_type
        
        return POIType.LANDMARK  # デフォルト
    
    def _is_poi_suitable_for_evidence(self, poi: POI) -> bool:
        """POIが証拠配置に適しているかチェック"""
        
        # 基本的な適性チェック
        if not poi.is_suitable_for_evidence():
            return False
        
        # 名前による追加フィルタリング
        unsuitable_keywords = [
            "ATM", "自動販売機", "駐車場", "トイレ", 
            "工事", "閉鎖", "建設中"
        ]
        
        for keyword in unsuitable_keywords:
            if keyword in poi.name:
                return False
        
        return True
    
    def _select_best_evidence_pois(
        self,
        available_pois: List[POI],
        center_location: Location,
        evidence_count: int
    ) -> List[POI]:
        """証拠配置に最適なPOIを選択"""
        
        if not available_pois:
            return []
        
        # 各POIの適性スコアを計算
        scored_pois = []
        for poi in available_pois:
            score = EvidencePlacementStrategy.calculate_poi_suitability(
                poi, center_location
            )
            scored_pois.append((poi, score))
        
        # スコア順にソート
        scored_pois.sort(key=lambda x: x[1], reverse=True)
        
        # 上位POIを選択
        candidate_pois = [poi for poi, score in scored_pois[:evidence_count * 2]]
        
        # 分散を考慮して最終選択
        selected_pois = EvidencePlacementStrategy.ensure_evidence_distribution(
            candidate_pois, evidence_count
        )
        
        logger.info(f"証拠配置用POI選択完了: {len(selected_pois)}件")
        return selected_pois
    
    def _deduplicate_pois(self, pois: List[POI]) -> List[POI]:
        """POIの重複除去（改良版）"""
        
        if not pois:
            return []
        
        unique_pois = []
        seen_locations = []
        
        for poi in pois:
            # 既存の位置から50m以内の場合は重複とみなす
            is_duplicate = False
            for seen_loc in seen_locations:
                if poi.location.distance_to(seen_loc) < 50:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_pois.append(poi)
                seen_locations.append(poi.location)
        
        return unique_pois
    
    async def _generate_mock_pois(
        self,
        center: Location,
        count: int
    ) -> List[POI]:
        """開発用モックPOIデータ（証拠配置最適化版）"""
        
        mock_templates = [
            {"name": "中央公園", "type": POIType.PARK},
            {"name": "市立美術館", "type": POIType.LANDMARK},
            {"name": "図書館本館", "type": POIType.LIBRARY},
            {"name": "歴史資料館", "type": POIType.LANDMARK},
            {"name": "カフェ・ド・パーク", "type": POIType.CAFE},
            {"name": "コミュニティセンター", "type": POIType.LIBRARY},
            {"name": "駅前広場", "type": POIType.LANDMARK},
            {"name": "和風庭園", "type": POIType.PARK},
            {"name": "文化会館", "type": POIType.LANDMARK},
            {"name": "ブックカフェ", "type": POIType.CAFE},
        ]
        
        mock_pois = []
        for i in range(min(count, len(mock_templates))):
            template = mock_templates[i]
            
            # 証拠配置に適した距離で配置（100-800m）
            angle = random.uniform(0, 360)
            distance = random.uniform(100, 800)
            
            # 距離と角度から位置を計算
            lat_offset = (distance / 111111) * random.choice([-1, 1])
            lng_offset = (distance / (111111 * abs(center.lat))) * random.choice([-1, 1])
            
            poi = POI(
                poi_id=f"mock_evidence_{i+1}",
                name=f"{template['name']}",
                poi_type=template["type"],
                location=Location(
                    lat=center.lat + lat_offset,
                    lng=center.lng + lng_offset
                ),
                address=f"模擬住所 {i+1}-{i*3+1}-{i*2+5}",
                description="証拠配置最適化モックデータ"
            )
            mock_pois.append(poi)
        
        return mock_pois
    
    async def get_poi_details(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """POIの詳細情報を取得"""
        
        if not self.gmaps:
            return None
        
        try:
            place_details = await asyncio.to_thread(
                self.gmaps.place,
                place_id=poi_id,
                fields=['name', 'formatted_address', 'rating', 'opening_hours',
                       'photos', 'reviews', 'website', 'international_phone_number'],
                language='ja'
            )
            
            return place_details.get('result', {})
            
        except Exception as e:
            logger.error(f"POI詳細取得エラー: {e}")
            return None
    
    async def validate_poi_accessibility(
        self,
        poi: POI,
        player_location: Location
    ) -> Dict[str, Any]:
        """POIのアクセス性を検証"""
        
        distance = poi.distance_from(player_location)
        
        # 徒歩でのアクセス時間を推定
        walking_speed = 4.0  # km/h
        walking_time_minutes = (distance / 1000) / walking_speed * 60
        
        accessibility = {
            "distance_meters": distance,
            "walking_time_minutes": walking_time_minutes,
            "accessibility_level": "easy" if distance <= 300 else 
                                  "moderate" if distance <= 800 else "challenging",
            "is_reasonable_walking_distance": distance <= 1500
        }
        
        return accessibility


# グローバルインスタンス
enhanced_poi_service = EnhancedPOIService()