#!/usr/bin/env python3
"""
APIワークフローテスト - 実際の動作確認
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api_workflow():
    """API全体のワークフローをテスト"""
    
    print("🌐 API動作確認テスト")
    print("=" * 50)
    
    # 1. サーバー起動確認
    print("1. 🚀 サーバー起動確認")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ サーバー起動中: {data['message']}")
            print(f"   バージョン: {data['version']}")
        else:
            print(f"   ❌ サーバー応答エラー: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ サーバー接続失敗: {e}")
        return False
    
    # 2. 利用可能エンドポイント確認
    print("\n2. 📋 利用可能エンドポイント確認")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            endpoints = openapi_spec.get("paths", {})
            print(f"   ✅ 利用可能エンドポイント数: {len(endpoints)}")
            
            # 主要エンドポイントをチェック
            key_endpoints = ["/", "/api/v1/game/start", "/api/v1/evidence/discover"]
            for endpoint in key_endpoints:
                if endpoint in endpoints:
                    print(f"      ✅ {endpoint}")
                else:
                    print(f"      ❌ {endpoint} (未実装)")
        else:
            print(f"   ❌ OpenAPI仕様取得失敗")
    except Exception as e:
        print(f"   ⚠️ OpenAPI確認エラー: {e}")
    
    # 3. ゲーム作成テスト（可能な場合）
    print("\n3. 🎮 ゲーム作成テスト")
    game_start_data = {
        "player_id": "api_test_player",
        "player_location": {
            "lat": 35.6812,
            "lng": 139.7671
        },
        "difficulty": "normal"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/game/start",
            json=game_start_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            game_data = response.json()
            print(f"   ✅ ゲーム作成成功")
            print(f"      ゲームID: {game_data.get('game_id', '不明')}")
            return game_data.get('game_id')
        elif response.status_code == 404:
            print(f"   ⚠️ ゲーム作成エンドポイントが未実装")
        else:
            print(f"   ❌ ゲーム作成失敗: {response.status_code}")
            print(f"      レスポンス: {response.text}")
    except Exception as e:
        print(f"   ⚠️ ゲーム作成テストエラー: {e}")
    
    # 4. 証拠発見テスト（可能な場合）
    print("\n4. 🔍 証拠発見テスト")
    evidence_data = {
        "game_id": "test_game_123",
        "player_id": "api_test_player",
        "player_location": {
            "lat": 35.6812,
            "lng": 139.7671
        },
        "evidence_id": "test_evidence_001",
        "gps_reading": {
            "latitude": 35.6812,
            "longitude": 139.7671,
            "accuracy": {
                "horizontal_accuracy": 3.0,
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
        response = requests.post(
            f"{BASE_URL}/api/v1/evidence/discover",
            json=evidence_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 証拠発見API応答成功")
            print(f"      結果: {result.get('success', '不明')}")
        elif response.status_code == 404:
            print(f"   ⚠️ 証拠発見エンドポイントが未実装")
        else:
            print(f"   ❌ 証拠発見失敗: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ 証拠発見テストエラー: {e}")
    
    print(f"\n🎉 API動作確認完了")
    return True

def show_manual_test_instructions():
    """手動テストの手順を表示"""
    
    print("\n" + "=" * 50)
    print("📖 手動動作確認の方法")
    print("=" * 50)
    
    print("\n1. 🌐 ブラウザでSwagger UIを開く:")
    print(f"   http://localhost:8000/docs")
    print("   → APIの全エンドポイントを確認・テスト可能")
    
    print("\n2. 🧪 コマンドラインでcurlテスト:")
    print("   # サーバー状態確認")
    print("   curl http://localhost:8000/")
    print("")
    print("   # ゲーム作成テスト（実装済みの場合）")
    print("   curl -X POST http://localhost:8000/api/v1/game/start \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"player_id\":\"test\",\"player_location\":{\"lat\":35.6812,\"lng\":139.7671},\"difficulty\":\"normal\"}'")
    
    print("\n3. 🔧 データベース直接確認:")
    print("   # ローカルDBファイル確認")
    print("   ls -la local_db/")
    print("   cat local_db/game_sessions/test_game_123.json")
    
    print("\n4. 📱 モバイルアプリ連携（今後）:")
    print("   - GPS機能付きフロントエンド")
    print("   - リアルタイム位置情報送信")
    print("   - 証拠発見UI")

if __name__ == "__main__":
    test_api_workflow()
    show_manual_test_instructions()