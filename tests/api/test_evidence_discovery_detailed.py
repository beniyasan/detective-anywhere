#!/usr/bin/env python3
"""
証拠発見時の詳細情報表示テスト
"""

import requests
import json
import sys
import os
from datetime import datetime

# パス設定  
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

BASE_URL = "http://localhost:8080"

async def test_evidence_discovery_details():
    """証拠発見時の詳細情報をテスト"""
    
    print("🔍 証拠発見詳細情報テスト")
    print("=" * 50)
    
    # 1. 新しいゲーム作成
    print("1. 🎮 ゲーム作成...")
    game_request = {
        "player_id": "detail-test-player",
        "location": {"lat": 35.6580, "lng": 139.7016},
        "difficulty": "easy"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/game/start", json=game_request)
    if response.status_code != 200:
        print(f"   ❌ ゲーム作成失敗: {response.status_code}")
        return False
    
    game_data = response.json()
    game_id = game_data["game_id"]
    evidence_list = game_data["evidence"]
    
    print(f"   ✅ ゲーム作成成功: {game_id}")
    print(f"   📍 証拠数: {len(evidence_list)}")
    
    # 2. 証拠の詳細確認
    print(f"\n2. 📋 生成された証拠の詳細:")
    for i, evidence in enumerate(evidence_list, 1):
        print(f"\n   証拠 {i}: {evidence['name']}")
        print(f"      場所: {evidence['poi_name']}")
        print(f"      重要度: {evidence['importance']}")
        print(f"      GPS: {evidence['location']['lat']:.4f}, {evidence['location']['lng']:.4f}")
        
        # 詳細フィールドの確認
        if 'description' in evidence:
            print(f"      説明: {evidence['description']}")
        else:
            print(f"      説明: ❌ 未設定")
            
        if 'discovery_text' in evidence:
            print(f"      発見テキスト: {evidence['discovery_text']}")
        else:
            print(f"      発見テキスト: ❌ 未設定")
    
    # 3. ゲームサービスを直接テストしてみる
    print(f"\n3. 🧪 ゲームサービス直接テスト:")
    
    try:
        from services.game_service import game_service
        from services.gps_service import GPSReading, GPSAccuracy
        from shared.models.location import Location
        
        # ゲームセッション取得
        game_session = await game_service.get_game_session(game_id)
        if game_session:
            print(f"   ✅ ゲームセッション取得成功")
            
            # 最初の証拠で発見テスト
            if game_session.evidence_list:
                target_evidence = game_session.evidence_list[0]
                print(f"   🎯 テスト対象証拠: {target_evidence.name}")
                
                # 証拠の詳細フィールド確認
                print(f"      名前: {target_evidence.name}")
                print(f"      説明: {getattr(target_evidence, 'description', '❌ 未設定')}")
                print(f"      発見テキスト: {getattr(target_evidence, 'discovery_text', '❌ 未設定')}")
                print(f"      重要度: {target_evidence.importance}")
                
                # GPS読み取り作成
                gps_reading = GPSReading(
                    latitude=target_evidence.location.lat,
                    longitude=target_evidence.location.lng,
                    accuracy=GPSAccuracy(
                        horizontal_accuracy=2.0,
                        vertical_accuracy=4.0,
                        speed_accuracy=1.0
                    ),
                    altitude=10.0,
                    speed=0.0,
                    heading=0.0,
                    timestamp=datetime.now()
                )
                
                # 証拠発見テスト
                discovery_result = await game_service.discover_evidence(
                    game_id=game_id,
                    player_id="detail-test-player",
                    player_location=target_evidence.location,
                    evidence_id=target_evidence.evidence_id,
                    gps_reading=gps_reading
                )
                
                print(f"   🔍 証拠発見結果:")
                print(f"      成功: {discovery_result.success}")
                print(f"      メッセージ: {discovery_result.message}")
                if discovery_result.evidence:
                    print(f"      発見された証拠: {discovery_result.evidence.name}")
                    print(f"      詳細説明: {getattr(discovery_result.evidence, 'description', '未設定')}")
                    print(f"      発見テキスト: {getattr(discovery_result.evidence, 'discovery_text', '未設定')}")
                
        else:
            print(f"   ❌ ゲームセッション取得失敗")
            
    except Exception as e:
        print(f"   ❌ ゲームサービステストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    return True

async def main():
    """メイン実行関数"""
    success = await test_evidence_discovery_details()
    
    print(f"\n" + "=" * 50)
    if success:
        print("✅ 証拠詳細情報テスト完了")
        print("\n🔍 確認項目:")
        print("- API応答に含まれる証拠フィールド")
        print("- ゲームサービスでの証拠詳細")
        print("- 証拠発見時の詳細表示")
    else:
        print("❌ テスト失敗")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())