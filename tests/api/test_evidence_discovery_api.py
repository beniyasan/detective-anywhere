#!/usr/bin/env python3
"""
生成されたゲームで証拠発見APIをテスト
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
GAME_ID = "6a6706cd-872f-4e92-9928-b705ea9d0708"  # 生成されたゲームID

def test_evidence_discovery():
    """実際のゲームで証拠発見をテスト"""
    
    print("🔍 証拠発見API動作テスト")
    print("=" * 50)
    
    # テスト用の証拠情報（生成されたゲームから）
    evidence_tests = [
        {
            "evidence_id": "evidence_1",
            "name": "血のついたコーヒーカップ",
            "location": {"lat": 35.6590, "lng": 139.7480},
            "poi_name": "コンビニエンスストア"
        },
        {
            "evidence_id": "evidence_4", 
            "name": "防犯カメラの映像",
            "location": {"lat": 35.6564, "lng": 139.7456},
            "poi_name": "地下鉄 神谷町駅"
        }
    ]
    
    print(f"🎮 ゲームID: {GAME_ID}")
    print(f"🧪 テストする証拠数: {len(evidence_tests)}")
    
    for i, evidence in enumerate(evidence_tests, 1):
        print(f"\n📍 テスト {i}: {evidence['name']}")
        print(f"   場所: {evidence['poi_name']}")
        print(f"   GPS座標: {evidence['location']['lat']}, {evidence['location']['lng']}")
        
        # 高精度GPSデータを作成
        discovery_request = {
            "game_id": GAME_ID,
            "player_id": "demo-player", 
            "player_location": evidence['location'],
            "evidence_id": evidence['evidence_id'],
            "gps_reading": {
                "latitude": evidence['location']['lat'],
                "longitude": evidence['location']['lng'],
                "accuracy": {
                    "horizontal_accuracy": 3.0,  # 3m精度
                    "vertical_accuracy": 5.0,
                    "speed_accuracy": 1.0
                },
                "altitude": 10.0,
                "speed": 0.0,
                "heading": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            # 証拠発見API呼び出し（存在する場合）
            response = requests.post(
                f"{BASE_URL}/api/v1/evidence/discover",
                json=discovery_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 証拠発見成功!")
                print(f"      成功: {result.get('success', 'Unknown')}")
                print(f"      距離: {result.get('distance', 'Unknown')}m")
                if 'message' in result:
                    print(f"      メッセージ: {result['message']}")
                    
            elif response.status_code == 404:
                print(f"   ⚠️ 証拠発見APIは未実装")
                print("   → 代わりにゲームサービスを直接テスト可能")
                
            else:
                print(f"   ❌ API エラー: {response.status_code}")
                print(f"      レスポンス: {response.text}")
                
        except Exception as e:
            print(f"   ❌ リクエストエラー: {e}")
    
    # ゲーム状態確認
    print(f"\n📊 ゲーム状態確認")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/game/{GAME_ID}")
        if response.status_code == 200:
            game_data = response.json()
            print(f"   ✅ ゲームデータ取得成功")
            print(f"      ステータス: {game_data.get('status', 'Unknown')}")
            discovered = game_data.get('discovered_evidence', [])
            print(f"      発見済み証拠: {len(discovered)}個")
        elif response.status_code == 404:
            print(f"   ⚠️ ゲーム取得APIは未実装")
        else:
            print(f"   ❌ ゲーム取得エラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ゲーム状態確認エラー: {e}")
    
    print(f"\n🎉 証拠発見テスト完了")

def show_game_play_instructions():
    """実際のゲームプレイ方法を表示"""
    
    print(f"\n" + "=" * 50)
    print("🎮 実際のゲームプレイ方法")
    print("=" * 50)
    
    print(f"\n📱 モバイルアプリでの確認:")
    print("1. GPS機能を有効にしたスマートフォン")
    print("2. 以下の場所に実際に移動:")
    print("   📍 コンビニエンスストア (35.6590, 139.7480)")
    print("   📍 愛宕神社 (35.6603, 139.7461)")  
    print("   📍 東京タワー (35.6586, 139.7454)")
    print("   📍 神谷町駅 (35.6564, 139.7456)")
    print("   📍 芝公園 (35.6566, 139.7502)")
    
    print(f"\n🔧 技術的な確認方法:")
    print("1. バックエンドログを確認:")
    print("   → GPS検証ロジックの動作")
    print("   → データベース更新の確認")
    
    print("2. データベース直接確認:")
    print(f"   cat local_db/game_sessions/{GAME_ID}.json")
    
    print("3. 証拠発見シミュレーション:")
    print("   → 実装済みのGPS検証システムが動作")
    print("   → 精度ベースの距離計算")
    print("   → GPS偽造検出")

if __name__ == "__main__":
    test_evidence_discovery()
    show_game_play_instructions()