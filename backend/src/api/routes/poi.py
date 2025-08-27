"""
POI（興味のある場所）関連APIルーター
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...services.poi_service import poi_service
from shared.models.location import Location, POI, POIType
from ..errors import APIError, POIAPIError


router = APIRouter()


# レスポンスモデル
class NearbyPOIResponse(BaseModel):
    """周辺POIレスポンス"""
    pois: List[dict]
    center_location: Location
    search_radius: int
    total_found: int


class LocationContextResponse(BaseModel):
    """位置コンテキストレスポンス"""
    location: Location
    context: str
    region_name: str


@router.get("/nearby", response_model=NearbyPOIResponse)
async def get_nearby_pois(
    lat: float = Query(..., description="緯度"),
    lng: float = Query(..., description="経度"),
    radius: int = Query(1000, description="検索半径（メートル）", ge=100, le=5000),
    poi_type: Optional[str] = Query(None, description="POIタイプフィルター"),
    limit: int = Query(20, description="最大取得数", ge=1, le=50)
):
    """
    指定位置周辺のPOIを検索
    
    - Google Maps APIを使用してPOI情報を取得
    - タイプフィルターと距離ソート
    - ゲーム作成前の事前確認用
    """
    
    try:
        location = Location(lat=lat, lng=lng)
        
        # 位置の有効性チェック
        if not await poi_service.validate_location(location):
            raise POIAPIError.invalid_location()
        
        # POI検索
        poi_types = [poi_type] if poi_type else None
        pois = await poi_service.find_nearby_pois(
            location=location,
            radius=radius,
            poi_types=poi_types,
            min_count=5
        )
        
        # レスポンス用にフォーマット
        poi_list = []
        for poi in pois[:limit]:
            distance = poi.distance_from(location)
            poi_list.append({
                "poi_id": poi.poi_id,
                "name": poi.name,
                "type": poi.poi_type.value,
                "location": {
                    "lat": poi.location.lat,
                    "lng": poi.location.lng
                },
                "address": poi.address,
                "distance": round(distance, 1),
                "suitable_for_evidence": poi.is_suitable_for_evidence()
            })
        
        return NearbyPOIResponse(
            pois=poi_list,
            center_location=location,
            search_radius=radius,
            total_found=len(pois)
        )
        
    except ValueError as e:
        raise APIError.bad_request(
            code="INVALID_LOCATION",
            message=str(e)
        )
    except Exception as e:
        raise POIAPIError.poi_search_failed()


@router.get("/context", response_model=LocationContextResponse)
async def get_location_context(
    lat: float = Query(..., description="緯度"),
    lng: float = Query(..., description="経度")
):
    """
    位置の地域コンテキストを取得
    
    - 住所情報から地域名を取得
    - シナリオ生成時の舞台設定に使用
    """
    
    try:
        location = Location(lat=lat, lng=lng)
        
        if not await poi_service.validate_location(location):
            raise POIAPIError.invalid_location()
        
        context = await poi_service.get_location_context(location)
        
        return LocationContextResponse(
            location=location,
            context=context,
            region_name=context  # 簡略化
        )
        
    except Exception as e:
        raise APIError.bad_gateway(
            code="EXTERNAL_API_ERROR",
            message="位置情報取得に失敗しました",
            service="Google Maps API"
        )


@router.get("/types")
async def get_poi_types():
    """
    利用可能なPOIタイプ一覧を取得
    
    - フロントエンドでのフィルター選択に使用
    - 各タイプの日本語名も含む
    """
    
    poi_type_info = []
    
    type_names = {
        POIType.RESTAURANT: "レストラン",
        POIType.CAFE: "カフェ",
        POIType.PARK: "公園",
        POIType.LANDMARK: "ランドマーク",
        POIType.STATION: "駅",
        POIType.SHOP: "店舗",
        POIType.OFFICE: "オフィス",
        POIType.SCHOOL: "学校",
        POIType.HOSPITAL: "病院",
        POIType.LIBRARY: "図書館・文化施設"
    }
    
    for poi_type in POIType:
        poi_type_info.append({
            "value": poi_type.value,
            "name": type_names.get(poi_type, poi_type.value),
            "suitable_for_evidence": poi_type in [
                POIType.RESTAURANT, POIType.CAFE, POIType.PARK,
                POIType.LANDMARK, POIType.SHOP, POIType.LIBRARY
            ]
        })
    
    return {
        "poi_types": poi_type_info,
        "total_types": len(poi_type_info)
    }


@router.post("/validate-area")
async def validate_game_area(
    lat: float = Query(..., description="中心緯度"),
    lng: float = Query(..., description="中心経度"),
    radius: int = Query(1000, description="検索半径（メートル）")
):
    """
    ゲーム作成可能なエリアかを検証
    
    - 十分な数のPOIが存在するか
    - 証拠配置に適したPOIが含まれるか
    - ゲーム開始前の事前チェック用
    """
    
    try:
        location = Location(lat=lat, lng=lng)
        
        if not await poi_service.validate_location(location):
            return {
                "valid": False,
                "reason": "指定された位置情報が無効です",
                "recommendations": ["位置情報を確認してください"]
            }
        
        # 周辺POI検索
        pois = await poi_service.find_nearby_pois(
            location=location,
            radius=radius,
            min_count=5
        )
        
        suitable_pois = [poi for poi in pois if poi.is_suitable_for_evidence()]
        
        # 検証結果
        min_total_pois = 5
        min_suitable_pois = 3
        
        is_valid = (len(pois) >= min_total_pois and 
                   len(suitable_pois) >= min_suitable_pois)
        
        recommendations = []
        if len(pois) < min_total_pois:
            recommendations.append("もう少し市街地に近い場所を選んでください")
        if len(suitable_pois) < min_suitable_pois:
            recommendations.append("カフェや公園などがある場所を選んでください")
        
        if is_valid:
            recommendations.append("この地域でゲームを作成できます")
        
        return {
            "valid": is_valid,
            "total_pois": len(pois),
            "suitable_pois": len(suitable_pois),
            "min_required_total": min_total_pois,
            "min_required_suitable": min_suitable_pois,
            "reason": "検証完了",
            "recommendations": recommendations,
            "poi_types_available": list(set(poi.poi_type.value for poi in pois))
        }
        
    except Exception as e:
        return {
            "valid": False,
            "reason": f"検証中にエラーが発生しました: {str(e)}",
            "recommendations": ["しばらく時間をおいて再試行してください"]
        }