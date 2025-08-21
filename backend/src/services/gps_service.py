"""
GPS検証サービス - 実際のGPSデータの検証と位置情報処理
"""

import math
import time
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)

from ....shared.models.location import Location


class GPSAccuracy(BaseModel):
    """GPS精度情報"""
    
    horizontal_accuracy: float  # 水平精度（メートル）
    vertical_accuracy: Optional[float] = None  # 垂直精度（メートル）
    timestamp: datetime  # 測定時刻
    provider: str = "unknown"  # GPS, NETWORK, PASSIVE等
    
    @property
    def is_high_accuracy(self) -> bool:
        """高精度かどうか（10m以内）"""
        return self.horizontal_accuracy <= 10.0
    
    @property
    def is_acceptable_accuracy(self) -> bool:
        """許容精度かどうか（50m以内）"""
        return self.horizontal_accuracy <= 50.0


class GPSReading(BaseModel):
    """GPS読み取り値"""
    
    location: Location
    accuracy: GPSAccuracy
    speed: Optional[float] = None  # 移動速度（m/s）
    bearing: Optional[float] = None  # 方位角（度）
    altitude: Optional[float] = None  # 標高（メートル）
    
    @property
    def is_reliable(self) -> bool:
        """信頼できるGPS読み取りかどうか"""
        return (
            self.accuracy.is_acceptable_accuracy and
            (datetime.now() - self.accuracy.timestamp).total_seconds() < 30  # 30秒以内
        )


class LocationValidationResult(BaseModel):
    """位置検証結果"""
    
    is_valid: bool
    confidence_score: float  # 0.0-1.0の信頼度
    distance_to_target: float  # ターゲットまでの距離
    accuracy_adjusted_distance: float  # 精度を考慮した距離
    validation_details: Dict[str, Any]
    
    @property
    def is_within_discovery_range(self) -> bool:
        """発見範囲内かどうか"""
        return self.accuracy_adjusted_distance <= 50.0  # デフォルト発見範囲


class GPSService:
    """GPS検証サービス"""
    
    def __init__(self):
        self.min_accuracy_threshold = 100.0  # 最低限の精度閾値（メートル）
        self.discovery_base_radius = 50.0  # 基本発見半径
        self.max_speed_threshold = 50.0  # 最大速度閾値（m/s、約180km/h）
        
        # GPS履歴保存（簡易版）
        self._recent_readings: Dict[str, List[GPSReading]] = {}
    
    def validate_gps_reading(self, gps_reading: GPSReading) -> bool:
        """GPS読み取り値の基本検証"""
        
        # 緯度経度の範囲チェック
        if not (-90 <= gps_reading.location.lat <= 90):
            logger.warning(f"無効な緯度: {gps_reading.location.lat}")
            return False
        
        if not (-180 <= gps_reading.location.lng <= 180):
            logger.warning(f"無効な経度: {gps_reading.location.lng}")
            return False
        
        # 精度チェック
        if gps_reading.accuracy.horizontal_accuracy > self.min_accuracy_threshold:
            logger.warning(f"精度が低すぎます: {gps_reading.accuracy.horizontal_accuracy}m")
            return False
        
        # タイムスタンプチェック（未来や過度に古い時刻でないか）
        now = datetime.now()
        time_diff = abs((now - gps_reading.accuracy.timestamp).total_seconds())
        if time_diff > 300:  # 5分以上古い
            logger.warning(f"GPS読み取り時刻が古すぎます: {time_diff}秒前")
            return False
        
        # 速度チェック（異常に高速でないか）
        if gps_reading.speed and gps_reading.speed > self.max_speed_threshold:
            logger.warning(f"移動速度が異常に高速: {gps_reading.speed}m/s")
            return False
        
        return True
    
    def validate_evidence_discovery(
        self,
        player_gps: GPSReading,
        evidence_location: Location,
        player_id: Optional[str] = None
    ) -> LocationValidationResult:
        """証拠発見のための位置検証"""
        
        # 基本距離計算
        distance = player_gps.location.distance_to(evidence_location)
        
        # GPS精度を考慮した検証
        accuracy_buffer = player_gps.accuracy.horizontal_accuracy
        confidence_score = self._calculate_confidence_score(player_gps, distance)
        
        # 精度調整済み距離（最悪ケースを考慮）
        accuracy_adjusted_distance = max(0, distance - accuracy_buffer)
        
        # 移動履歴チェック（可能であれば）
        movement_validation = self._validate_movement_pattern(
            player_gps, player_id
        ) if player_id else {}
        
        # 検証詳細
        validation_details = {
            "raw_distance": distance,
            "gps_accuracy": accuracy_buffer,
            "confidence_factors": {
                "accuracy_quality": player_gps.accuracy.is_high_accuracy,
                "timestamp_freshness": (datetime.now() - player_gps.accuracy.timestamp).total_seconds(),
                "provider": player_gps.accuracy.provider
            },
            "movement_validation": movement_validation
        }
        
        # 最終判定
        is_valid = (
            self.validate_gps_reading(player_gps) and
            accuracy_adjusted_distance <= self.discovery_base_radius and
            confidence_score >= 0.7
        )
        
        return LocationValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            distance_to_target=distance,
            accuracy_adjusted_distance=accuracy_adjusted_distance,
            validation_details=validation_details
        )
    
    def calculate_adaptive_discovery_radius(
        self,
        player_gps: GPSReading,
        evidence_location: Location,
        poi_type: Optional[str] = None
    ) -> float:
        """適応的な発見半径を計算"""
        
        base_radius = self.discovery_base_radius
        
        # GPS精度に基づく調整
        accuracy_factor = min(2.0, player_gps.accuracy.horizontal_accuracy / 10.0)
        adjusted_radius = base_radius + (accuracy_factor * 10.0)
        
        # POIタイプに基づく調整
        poi_modifiers = {
            "park": 1.5,        # 公園は広いので範囲を拡大
            "landmark": 1.3,    # ランドマークも範囲拡大
            "cafe": 0.8,        # カフェは範囲を狭く
            "restaurant": 0.8,  # レストランも範囲を狭く
            "station": 1.2      # 駅は少し範囲拡大
        }
        
        if poi_type and poi_type in poi_modifiers:
            adjusted_radius *= poi_modifiers[poi_type]
        
        # 最大・最小制限
        return max(20.0, min(100.0, adjusted_radius))
    
    def detect_gps_spoofing(
        self,
        player_gps: GPSReading,
        player_id: str
    ) -> Dict[str, Any]:
        """GPS偽造検出（基本版）"""
        
        spoofing_indicators = {
            "suspicious_accuracy": False,
            "impossible_movement": False,
            "location_jump": False,
            "provider_inconsistency": False
        }
        
        # 異常に高い精度（偽造の可能性）
        if player_gps.accuracy.horizontal_accuracy < 1.0:
            spoofing_indicators["suspicious_accuracy"] = True
        
        # 移動履歴との整合性チェック
        recent_readings = self._get_recent_readings(player_id, 5)
        if recent_readings:
            movement_check = self._analyze_movement_pattern(recent_readings, player_gps)
            spoofing_indicators.update(movement_check)
        
        # 履歴保存
        self._store_gps_reading(player_id, player_gps)
        
        return {
            "is_likely_spoofed": any(spoofing_indicators.values()),
            "indicators": spoofing_indicators,
            "risk_score": sum(spoofing_indicators.values()) / len(spoofing_indicators)
        }
    
    def _calculate_confidence_score(
        self,
        player_gps: GPSReading,
        distance: float
    ) -> float:
        """信頼度スコアの計算"""
        
        score = 1.0
        
        # 精度による減点
        if player_gps.accuracy.horizontal_accuracy > 10:
            score -= (player_gps.accuracy.horizontal_accuracy - 10) * 0.01
        
        # 距離による減点（遠いほど不確実）
        if distance > 20:
            score -= (distance - 20) * 0.01
        
        # タイムスタンプの新しさ
        time_diff = (datetime.now() - player_gps.accuracy.timestamp).total_seconds()
        if time_diff > 10:
            score -= time_diff * 0.001
        
        # プロバイダーによる調整
        provider_scores = {
            "gps": 1.0,
            "network": 0.8,
            "passive": 0.6,
            "unknown": 0.5
        }
        provider_score = provider_scores.get(
            player_gps.accuracy.provider.lower(), 0.5
        )
        score *= provider_score
        
        return max(0.0, min(1.0, score))
    
    def _validate_movement_pattern(
        self,
        current_gps: GPSReading,
        player_id: str
    ) -> Dict[str, Any]:
        """移動パターンの検証"""
        
        recent_readings = self._get_recent_readings(player_id, 3)
        if not recent_readings:
            return {"validation": "no_history", "is_valid": True}
        
        last_reading = recent_readings[-1]
        time_diff = (current_gps.accuracy.timestamp - 
                    last_reading.accuracy.timestamp).total_seconds()
        
        if time_diff <= 0:
            return {"validation": "invalid_time", "is_valid": False}
        
        distance = current_gps.location.distance_to(last_reading.location)
        implied_speed = distance / time_diff
        
        # 徒歩想定での速度チェック（最大15km/h = 4.17m/s程度）
        max_walking_speed = 5.0  # m/s
        
        return {
            "validation": "movement_check",
            "is_valid": implied_speed <= max_walking_speed,
            "implied_speed": implied_speed,
            "time_diff": time_diff,
            "distance_moved": distance
        }
    
    def _analyze_movement_pattern(
        self,
        recent_readings: List[GPSReading],
        current_reading: GPSReading
    ) -> Dict[str, bool]:
        """移動パターン分析"""
        
        indicators = {
            "impossible_movement": False,
            "location_jump": False,
            "provider_inconsistency": False
        }
        
        if not recent_readings:
            return indicators
        
        last_reading = recent_readings[-1]
        
        # 時間差計算
        time_diff = (current_reading.accuracy.timestamp - 
                    last_reading.accuracy.timestamp).total_seconds()
        
        if time_diff > 0:
            distance = current_reading.location.distance_to(last_reading.location)
            speed = distance / time_diff
            
            # 不可能な移動速度（100km/h以上）
            if speed > 28.0:  # 約100km/h
                indicators["impossible_movement"] = True
            
            # 急激な位置ジャンプ（短時間での大きな移動）
            if time_diff < 5 and distance > 100:
                indicators["location_jump"] = True
        
        # プロバイダーの一貫性
        providers = [r.accuracy.provider for r in recent_readings[-3:]]
        if len(set(providers)) > 1 and "gps" in providers:
            # GPS以外のプロバイダーとの混在は要注意
            indicators["provider_inconsistency"] = True
        
        return indicators
    
    def _get_recent_readings(self, player_id: str, count: int) -> List[GPSReading]:
        """最近のGPS読み取り値を取得"""
        if player_id not in self._recent_readings:
            return []
        return self._recent_readings[player_id][-count:]
    
    def _store_gps_reading(self, player_id: str, reading: GPSReading):
        """GPS読み取り値を保存（簡易版）"""
        if player_id not in self._recent_readings:
            self._recent_readings[player_id] = []
        
        self._recent_readings[player_id].append(reading)
        
        # 古いデータの削除（最新10件のみ保持）
        if len(self._recent_readings[player_id]) > 10:
            self._recent_readings[player_id] = self._recent_readings[player_id][-10:]
    
    def get_location_quality_info(self, gps_reading: GPSReading) -> Dict[str, Any]:
        """位置情報の品質情報を取得"""
        
        quality_level = "poor"
        if gps_reading.accuracy.horizontal_accuracy <= 5:
            quality_level = "excellent"
        elif gps_reading.accuracy.horizontal_accuracy <= 10:
            quality_level = "good"
        elif gps_reading.accuracy.horizontal_accuracy <= 25:
            quality_level = "fair"
        
        return {
            "quality_level": quality_level,
            "accuracy_meters": gps_reading.accuracy.horizontal_accuracy,
            "provider": gps_reading.accuracy.provider,
            "timestamp": gps_reading.accuracy.timestamp,
            "is_reliable": gps_reading.is_reliable,
            "recommended_radius": self.calculate_adaptive_discovery_radius(
                gps_reading, gps_reading.location
            )
        }


# グローバルGPSサービスインスタンス
gps_service = GPSService()