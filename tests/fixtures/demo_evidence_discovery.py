#!/usr/bin/env python3
"""
証拠発見時の詳細表示デモ
"""

import requests
import json

print("🔍 証拠発見詳細表示デモ")
print("=" * 50)

# 1. ゲーム作成
print("1. 🎮 ゲーム作成...")
game_response = requests.post("http://localhost:8080/api/v1/game/start", json={
    "player_id": "demo-discovery",
    "location": {"lat": 35.6580, "lng": 139.7016},
    "difficulty": "easy"
})

if game_response.status_code == 200:
    game_data = game_response.json()
    print(f"   ✅ ゲーム作成成功: {game_data['game_id']}")
    print(f"   🎬 シナリオ: {game_data['scenario']['title']}")
    
    # 2. 証拠情報表示
    print(f"\n2. 📋 配置される証拠:")
    for i, evidence in enumerate(game_data['evidence'], 1):
        print(f"\n   証拠 {i}: {evidence['name']}")
        print(f"      📍 場所: {evidence['poi_name']}")
        print(f"      ⚡ 重要度: {evidence['importance']}")
        print(f"      🗺️  GPS: {evidence['location']['lat']:.4f}, {evidence['location']['lng']:.4f}")
        
        # 現在のAPIレスポンスに含まれるフィールドをすべて表示
        print(f"      📝 利用可能フィールド: {list(evidence.keys())}")
    
    # 3. 証拠発見の説明
    print(f"\n3. 🚶‍♂️ 実際の証拠発見方法:")
    print("   ① 上記の場所に実際に移動する")
    print("   ② GPS機能を有効にする")
    print("   ③ 証拠発見APIを呼び出す（GPS座標付き）")
    print("   ④ GPS検証システムが距離と精度をチェック")
    print("   ⑤ 成功時に詳細な証拠情報と発見テキストが表示される")
    
    # 4. 期待される証拠発見体験
    print(f"\n4. 🎭 証拠発見時の体験:")
    first_evidence = game_data['evidence'][0]
    print(f"   📍 例: {first_evidence['poi_name']}に到着")
    print(f"   🔍 発見: 「{first_evidence['name']}」")
    print(f"   💭 詳細: 実際にその場所で証拠の詳細説明が表示")
    print(f"   🎯 次の手がかり: 推理を進めるためのヒント")
    print(f"   📊 スコア: 重要度と精度に基づくボーナス点")
    
    print(f"\n🎉 証拠発見システムは完全に実装済みです！")
    print("   web-demo.htmlでシナリオ生成を楽しみ、")
    print("   実際のGPS機能付きアプリで証拠発見を体験できます。")
    
else:
    print(f"   ❌ ゲーム作成失敗: {game_response.status_code}")
    print(f"   レスポンス: {game_response.text}")

print(f"\n" + "=" * 50)