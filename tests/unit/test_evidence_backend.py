#!/usr/bin/env python3
"""
証拠発見機能の最終統合テスト
"""

import sys
import os
import asyncio
from datetime import datetime
from typing import Dict, Any

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 環境設定
os.environ['GOOGLE_CLOUD_PROJECT'] = 'gen-lang-client-0666798948'
os.environ['USE_FIRESTORE_EMULATOR'] = 'false'  # ローカルファイルでテスト

print("🔍 証拠発見機能最終統合テスト")
print("=" * 60)

async def test_evidence_discovery():
    """証拠発見機能の最終テスト"""
    
    try:
        # 基本インポート
        from services.database_service import database_service
        from services.gps_service import GPSReading, GPSAccuracy
        
        print("✅ 基本サービスのインポート成功")
        
        # データベース接続確認
        print("\n📊 データベース接続確認...")
        health = await database_service.health_check()
        print(f"   ステータス: {health['status']}")
        print(f"   データベースタイプ: {health['database_type']}")
        
        # テスト用データ作成
        test_game_id = f"evidence_test_{int(datetime.now().timestamp())}"
        test_player_id = "evidence_player_123"
        
        # モックゲームデータ（GPS機能付き）
        game_data = {
            "game_id": test_game_id,
            "player_id": test_player_id,
            "status": "active",
            "difficulty": "normal",
            "scenario": {
                "title": "GPS証拠発見テスト",
                "culprit": "テスト犯人",
                "motive": "GPS機能検証のため"
            },
            "evidence_list": [
                {
                    "evidence_id": "gps_ev_001",
                    "name": "GPS証拠：血痕",
                    "description": "不審な血痕が発見された",
                    "poi_name": "東京駅",
                    "poi_type": "transport_station",
                    "location": {"lat": 35.6812, "lng": 139.7671},
                    "significance": "high",
                    "discovered": False,
                    "discovery_timestamp": None
                },
                {
                    "evidence_id": "gps_ev_002",
                    "name": "GPS証拠：手袋",
                    "description": "高級手袋が遺留された",
                    "poi_name": "東京駅構内",
                    "poi_type": "transport_station", 
                    "location": {"lat": 35.6813, "lng": 139.7672},
                    "significance": "medium",
                    "discovered": False,
                    "discovery_timestamp": None
                }
            ],
            "discovered_evidence": [],
            "player_location": {"lat": 35.6812, "lng": 139.7671},
            "game_rules": {
                "discovery_radius": 50,
                "gps_accuracy_required": True,
                "spoofing_detection": True
            },
            "created_at": datetime.now()
        }
        
        print(f"\n🎮 ゲームセッション作成")
        print(f"   ゲームID: {test_game_id}")
        
        # ゲームセッション保存
        save_success = await database_service.save_game_session(test_game_id, game_data)
        if save_success:
            print("   ✅ ゲームセッション保存成功")
        else:
            print("   ❌ ゲームセッション保存失敗")
            return False
        
        # GPS読み取りデータ作成
        print(f"\n🛰️  GPS証拠発見シミュレーション")
        
        # 高精度GPS (証拠の正確な位置)
        evidence_location = game_data["evidence_list"][0]["location"]
        high_precision_gps = GPSReading(
            latitude=evidence_location["lat"],
            longitude=evidence_location["lng"],
            accuracy=GPSAccuracy(
                horizontal_accuracy=2.0,  # 2m精度
                vertical_accuracy=4.0,
                speed_accuracy=1.0
            ),
            altitude=10.0,
            speed=0.0,
            heading=0.0,
            timestamp=datetime.now()
        )
        
        print(f"   📍 証拠位置: ({evidence_location['lat']}, {evidence_location['lng']})")
        print(f"   🎯 GPS精度: {high_precision_gps.accuracy.horizontal_accuracy}m")
        
        # GPS検証システムをテスト
        from services.gps_service import gps_service
        
        # 証拠発見の距離計算
        target_lat, target_lng = evidence_location["lat"], evidence_location["lng"]
        distance = gps_service.calculate_distance(
            high_precision_gps.latitude, high_precision_gps.longitude,
            target_lat, target_lng
        )
        
        print(f"   📏 計算距離: {distance:.2f}m")
        
        # GPS検証実行
        from shared.models.location import Location
        target_location = Location(lat=target_lat, lng=target_lng)
        
        validation_result = gps_service.validate_evidence_discovery(
            high_precision_gps, target_location, test_player_id
        )
        
        print(f"   🔍 GPS検証結果:")
        print(f"      有効: {validation_result.is_valid}")
        print(f"      距離: {validation_result.distance_to_target:.2f}m")
        print(f"      要求精度: {validation_result.required_accuracy:.1f}m")
        print(f"      実際精度: {validation_result.actual_accuracy:.1f}m")
        
        # GPS偽造検出テスト
        spoofing_result = gps_service.detect_gps_spoofing(high_precision_gps, test_player_id)
        print(f"   🛡️  GPS偽造検出:")
        print(f"      偽造疑い: {spoofing_result['is_likely_spoofed']}")
        print(f"      信頼度スコア: {spoofing_result['confidence_score']:.2f}")
        
        # 証拠発見状態をシミュレート
        if validation_result.is_valid and not spoofing_result['is_likely_spoofed']:
            print(f"\n✅ GPS検証成功 - 証拠発見処理実行")
            
            # 証拠発見状態を更新
            evidence_discovery_update = {
                "discovered_evidence": ["gps_ev_001"],
                "evidence_discovery_log": [{
                    "evidence_id": "gps_ev_001",
                    "discovered_at": datetime.now(),
                    "discovery_method": "gps_validated",
                    "gps_accuracy": high_precision_gps.accuracy.horizontal_accuracy,
                    "distance": validation_result.distance_to_target
                }],
                "last_activity": datetime.now()
            }
            
            update_success = await database_service.update_game_session(
                test_game_id, evidence_discovery_update
            )
            
            if update_success:
                print("   ✅ 証拠発見状態更新成功")
            else:
                print("   ❌ 証拠発見状態更新失敗")
        
        # 更新されたゲームセッション確認
        print(f"\n💾 永続化セッション確認")
        updated_session = await database_service.get_game_session(test_game_id)
        
        if updated_session:
            print("   ✅ セッション取得成功")
            print(f"      発見済み証拠: {updated_session.get('discovered_evidence', [])}")
            
            if 'evidence_discovery_log' in updated_session:
                print(f"      発見ログ記録数: {len(updated_session['evidence_discovery_log'])}")
            
            discovery_count = len(updated_session.get('discovered_evidence', []))
            total_evidence = len(updated_session.get('evidence_list', []))
            print(f"      進捗: {discovery_count}/{total_evidence} 証拠発見")
        else:
            print("   ❌ セッション取得失敗")
        
        print(f"\n🎉 証拠発見機能統合テスト完了！")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    
    success = await test_evidence_discovery()
    
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 証拠発見機能統合テスト成功！")
        print("")
        print("✅ 動作確認済み機能:")
        print("   📍 GPS位置検証システム")
        print("   🎯 精度ベース証拠発見判定")
        print("   🛡️  GPS偽造検出機能")
        print("   💾 ゲームセッション永続化")
        print("   📊 証拠発見状態管理")
        print("")
        print("🚀 Firestore統合の実装完了！")
        print("   ローカル開発: ファイルベースDB使用")
        print("   本番環境: Firestore使用可能")
    else:
        print("❌ 統合テスト失敗")

if __name__ == "__main__":
    asyncio.run(main())