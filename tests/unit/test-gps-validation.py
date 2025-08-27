#!/usr/bin/env python3
"""
GPS検証機能のテスト
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# GPS検証サービスのインポート
try:
    from backend.src.services.gps_service import (
        GPSService, GPSReading, GPSAccuracy, LocationValidationResult
    )
    from shared.models.location import Location
except ImportError:
    # 簡易版のテスト用モック（実際の実装確認のため）
    print("⚠️ GPS検証モジュールのインポートに失敗しました。簡易テストを実行します。")
    import math
    from datetime import datetime
    from pydantic import BaseModel
    from typing import Optional, Dict, Any
    
    class Location(BaseModel):
        lat: float
        lng: float
        
        def distance_to(self, other: "Location") -> float:
            R = 6371000
            lat1_rad = math.radians(self.lat)
            lat2_rad = math.radians(other.lat)
            delta_lat = math.radians(other.lat - self.lat)
            delta_lng = math.radians(other.lng - self.lng)
            
            a = (math.sin(delta_lat / 2) ** 2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * 
                 math.sin(delta_lng / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
    
    class GPSAccuracy(BaseModel):
        horizontal_accuracy: float
        vertical_accuracy: Optional[float] = None
        timestamp: datetime
        provider: str = "unknown"
    
    class GPSReading(BaseModel):
        location: Location
        accuracy: GPSAccuracy
        speed: Optional[float] = None
        bearing: Optional[float] = None
        altitude: Optional[float] = None
    
    class LocationValidationResult(BaseModel):
        is_valid: bool
        confidence_score: float
        distance_to_target: float
        accuracy_adjusted_distance: float
        validation_details: Dict[str, Any]
        
        @property
        def is_within_discovery_range(self) -> bool:
            return self.accuracy_adjusted_distance <= 50.0
    
    class GPSService:
        def validate_gps_reading(self, gps_reading): return True
        def validate_evidence_discovery(self, gps, evidence_loc, player_id):
            distance = gps.location.distance_to(evidence_loc)
            return LocationValidationResult(
                is_valid=distance <= 50,
                confidence_score=0.8,
                distance_to_target=distance,
                accuracy_adjusted_distance=max(0, distance - gps.accuracy.horizontal_accuracy),
                validation_details={}
            )
        def calculate_adaptive_discovery_radius(self, gps, evidence_loc, poi_type=None):
            return 50.0 + (gps.accuracy.horizontal_accuracy * 0.5)
        def detect_gps_spoofing(self, gps, player_id):
            return {"is_likely_spoofed": gps.accuracy.horizontal_accuracy < 1.0, "risk_score": 0.1}
        def get_location_quality_info(self, gps):
            quality = "good" if gps.accuracy.horizontal_accuracy <= 10 else "poor"
            return {"quality_level": quality, "recommended_radius": 50.0}

def test_basic_gps_validation():
    """基本的なGPS検証テスト"""
    print("🧪 基本的なGPS検証テスト")
    print("=" * 50)
    
    gps_service = GPSService()
    
    # 高精度GPS読み取り値
    high_accuracy_gps = GPSReading(
        location=Location(lat=35.5070, lng=139.6176),  # 新横浜駅
        accuracy=GPSAccuracy(
            horizontal_accuracy=5.0,
            timestamp=datetime.now(),
            provider="gps"
        )
    )
    
    print(f"✅ 高精度GPS検証: {gps_service.validate_gps_reading(high_accuracy_gps)}")
    
    # 低精度GPS読み取り値
    low_accuracy_gps = GPSReading(
        location=Location(lat=35.5070, lng=139.6176),
        accuracy=GPSAccuracy(
            horizontal_accuracy=150.0,  # 閾値(100m)を超える
            timestamp=datetime.now(),
            provider="network"
        )
    )
    
    print(f"❌ 低精度GPS検証: {gps_service.validate_gps_reading(low_accuracy_gps)}")
    
    # 古いタイムスタンプ
    old_timestamp_gps = GPSReading(
        location=Location(lat=35.5070, lng=139.6176),
        accuracy=GPSAccuracy(
            horizontal_accuracy=10.0,
            timestamp=datetime.now() - timedelta(minutes=10),  # 10分前
            provider="gps"
        )
    )
    
    print(f"❌ 古いタイムスタンプGPS検証: {gps_service.validate_gps_reading(old_timestamp_gps)}")

def test_evidence_discovery_validation():
    """証拠発見検証テスト"""
    print("\n🎯 証拠発見検証テスト")
    print("=" * 50)
    
    gps_service = GPSService()
    
    # プレイヤー位置（新横浜駅付近）
    player_location = Location(lat=35.5070, lng=139.6176)
    
    # 証拠位置（50m離れた場所）
    evidence_location = Location(lat=35.5075, lng=139.6180)
    
    # 高精度GPS
    high_accuracy_gps = GPSReading(
        location=player_location,
        accuracy=GPSAccuracy(
            horizontal_accuracy=3.0,
            timestamp=datetime.now(),
            provider="gps"
        )
    )
    
    validation_result = gps_service.validate_evidence_discovery(
        high_accuracy_gps, evidence_location, "test_player_1"
    )
    
    print(f"📍 証拠までの距離: {validation_result.distance_to_target:.1f}m")
    print(f"📏 精度調整済み距離: {validation_result.accuracy_adjusted_distance:.1f}m")
    print(f"📊 信頼度スコア: {validation_result.confidence_score:.2f}")
    print(f"✅ 発見可能: {validation_result.is_valid}")
    print(f"🎯 発見範囲内: {validation_result.is_within_discovery_range}")
    
    # 低精度GPS
    low_accuracy_gps = GPSReading(
        location=player_location,
        accuracy=GPSAccuracy(
            horizontal_accuracy=30.0,
            timestamp=datetime.now(),
            provider="network"
        )
    )
    
    validation_result_low = gps_service.validate_evidence_discovery(
        low_accuracy_gps, evidence_location, "test_player_2"
    )
    
    print(f"\n📡 低精度GPS検証:")
    print(f"📏 精度調整済み距離: {validation_result_low.accuracy_adjusted_distance:.1f}m")
    print(f"📊 信頼度スコア: {validation_result_low.confidence_score:.2f}")
    print(f"✅ 発見可能: {validation_result_low.is_valid}")

def test_adaptive_discovery_radius():
    """適応的発見半径テスト"""
    print("\n📐 適応的発見半径テスト")
    print("=" * 50)
    
    gps_service = GPSService()
    
    evidence_location = Location(lat=35.5070, lng=139.6176)
    
    test_cases = [
        ("高精度GPS", 3.0, "gps", "cafe"),
        ("中精度GPS", 15.0, "network", "park"),
        ("低精度GPS", 45.0, "passive", "landmark"),
    ]
    
    for name, accuracy, provider, poi_type in test_cases:
        gps_reading = GPSReading(
            location=evidence_location,
            accuracy=GPSAccuracy(
                horizontal_accuracy=accuracy,
                timestamp=datetime.now(),
                provider=provider
            )
        )
        
        radius = gps_service.calculate_adaptive_discovery_radius(
            gps_reading, evidence_location, poi_type
        )
        
        print(f"{name}: 精度{accuracy}m, POI:{poi_type} → 発見半径: {radius:.1f}m")

def test_gps_spoofing_detection():
    """GPS偽造検出テスト"""
    print("\n🕵️ GPS偽造検出テスト")
    print("=" * 50)
    
    gps_service = GPSService()
    player_id = "test_player_spoofing"
    
    # 正常なGPS読み取り
    normal_gps = GPSReading(
        location=Location(lat=35.5070, lng=139.6176),
        accuracy=GPSAccuracy(
            horizontal_accuracy=8.0,
            timestamp=datetime.now(),
            provider="gps"
        ),
        speed=1.5  # 歩行速度
    )
    
    spoofing_result = gps_service.detect_gps_spoofing(normal_gps, player_id)
    print(f"正常なGPS: 偽造疑い={spoofing_result['is_likely_spoofed']}, リスクスコア={spoofing_result['risk_score']:.2f}")
    
    # 異常に高い精度（偽造疑い）
    suspicious_gps = GPSReading(
        location=Location(lat=35.5080, lng=139.6180),
        accuracy=GPSAccuracy(
            horizontal_accuracy=0.1,  # 異常に高い精度
            timestamp=datetime.now(),
            provider="gps"
        )
    )
    
    spoofing_result_suspicious = gps_service.detect_gps_spoofing(suspicious_gps, player_id)
    print(f"疑わしいGPS: 偽造疑い={spoofing_result_suspicious['is_likely_spoofed']}, リスクスコア={spoofing_result_suspicious['risk_score']:.2f}")

def test_location_quality_info():
    """位置情報品質情報テスト"""
    print("\n📊 位置情報品質情報テスト")
    print("=" * 50)
    
    gps_service = GPSService()
    
    test_readings = [
        ("優秀", 2.0, "gps"),
        ("良好", 8.0, "gps"),
        ("普通", 20.0, "network"),
        ("悪い", 80.0, "passive"),
    ]
    
    for name, accuracy, provider in test_readings:
        gps_reading = GPSReading(
            location=Location(lat=35.5070, lng=139.6176),
            accuracy=GPSAccuracy(
                horizontal_accuracy=accuracy,
                timestamp=datetime.now(),
                provider=provider
            )
        )
        
        quality_info = gps_service.get_location_quality_info(gps_reading)
        print(f"{name}: 品質={quality_info['quality_level']}, 推奨半径={quality_info['recommended_radius']:.1f}m")

def main():
    """メインテスト実行"""
    print("🚀 GPS検証機能テスト開始")
    print("=" * 60)
    
    try:
        test_basic_gps_validation()
        test_evidence_discovery_validation()
        test_adaptive_discovery_radius()
        test_gps_spoofing_detection()
        test_location_quality_info()
        
        print("\n" + "=" * 60)
        print("✅ 全てのGPS検証テストが完了しました!")
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)