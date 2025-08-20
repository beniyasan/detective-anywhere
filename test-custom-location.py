#!/usr/bin/env python3
"""
カスタム場所機能のテスト
"""

import requests
import json

def test_custom_location():
    """カスタム場所（名古屋競馬場）でのテスト"""
    print("📍 カスタム場所テスト: 名古屋競馬場")
    print("=" * 50)
    
    # カスタム場所データ
    custom_location_data = {
        "player_id": "demo-player",
        "location": {
            "lat": 35.0000,
            "lng": 135.0000,
            "name": "名古屋競馬場",
            "context": "愛知県名古屋市にあった競馬場。2022年に八戸市に移転した歴史ある施設。地元住民にとって思い出深い場所で、多くの人々が通った"
        },
        "difficulty": "normal"
    }
    
    print(f"送信データ:")
    print(f"  場所名: {custom_location_data['location']['name']}")
    print(f"  説明: {custom_location_data['location']['context']}")
    print(f"  難易度: {custom_location_data['difficulty']}")
    print()
    
    try:
        # リクエスト送信
        response = requests.post(
            'http://localhost:8080/api/v1/game/start',
            json=custom_location_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            scenario = result.get('scenario', {})
            print("✅ カスタム場所テスト成功!")
            print(f"🎬 生成されたタイトル: {scenario.get('title', 'N/A')}")
            print(f"📖 あらすじの最初の100文字:")
            print(f"  {scenario.get('description', '')[:100]}...")
            
            # 名古屋競馬場が言及されているかチェック
            description = scenario.get('description', '')
            if '名古屋競馬場' in description or '名古屋' in description or '競馬場' in description:
                print("🎯 SUCCESS: シナリオに名古屋競馬場が反映されています!")
            else:
                print("❌ WARNING: シナリオに名古屋競馬場が反映されていません")
                print(f"生成された場所: {description}")
            
        else:
            print(f"❌ エラー: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")

if __name__ == "__main__":
    test_custom_location()