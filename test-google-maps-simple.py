#!/usr/bin/env python3
"""
Google Maps API 簡易テストスクリプト（Places APIのみ）
"""

import os
import sys
import json
from dotenv import load_dotenv
import googlemaps

# 環境変数読み込み
load_dotenv()

def test_places_api_only():
    """Places APIのみテスト"""
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY が設定されていません")
        return False
    
    print(f"🔑 APIキー確認: {api_key[:20]}...")
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        print("✅ Google Maps クライアント初期化成功")
    except Exception as e:
        print(f"❌ Google Maps クライアント初期化失敗: {e}")
        return False
    
    # テスト用座標（東京タワー周辺）
    test_location = {"lat": 35.6586, "lng": 139.7454}
    print(f"📍 テスト地点: 東京タワー周辺 ({test_location['lat']}, {test_location['lng']})")
    
    # ゲーム用POI検索テスト
    print("\n🎮 ゲーム用POI検索テスト")
    game_poi_types = ['cafe', 'park', 'tourist_attraction', 'store', 'restaurant']
    
    total_suitable = 0
    all_pois = []
    
    for poi_type in game_poi_types:
        try:
            print(f"\n🔍 {poi_type.upper()} タイプ検索中...")
            places_result = gmaps.places_nearby(
                location=(test_location["lat"], test_location["lng"]),
                radius=800,
                type=poi_type
            )
            
            results = places_result.get('results', [])
            count = len(results)
            print(f"  📍 発見: {count}件")
            
            # 上位3件の詳細表示
            for i, place in enumerate(results[:3]):
                name = place.get('name', '名前不明')
                rating = place.get('rating', 'N/A')
                types = ', '.join(place.get('types', [])[:2])
                vicinity = place.get('vicinity', '住所不明')
                location_data = place['geometry']['location']
                
                print(f"     {i+1}. {name}")
                print(f"        評価: {rating}/5.0")
                print(f"        タイプ: {types}")
                print(f"        住所: {vicinity}")
                print(f"        座標: {location_data['lat']:.6f}, {location_data['lng']:.6f}")
                
                all_pois.append({
                    'name': name,
                    'type': poi_type,
                    'rating': rating,
                    'location': location_data,
                    'types': place.get('types', [])
                })
            
            total_suitable += min(count, 3)  # 最大3件まで数える
                
        except Exception as e:
            print(f"❌ {poi_type} 検索エラー: {e}")
            if "API key" in str(e):
                print("   → APIキーまたは権限の問題の可能性があります")
            continue
    
    # 結果サマリー
    print(f"\n📊 テスト結果サマリー")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 発見したゲーム適性POI: {total_suitable}件")
    print(f"🎯 ゲーム作成可能判定: {'⭕ 可能' if total_suitable >= 5 else '❌ POI不足'}")
    
    # APIテスト用の簡単なゲームスタート模擬
    if total_suitable >= 5:
        print(f"\n🎲 模擬ゲーム証拠配置テスト")
        selected_pois = all_pois[:5]  # 5つのPOIを選択
        
        for i, poi in enumerate(selected_pois):
            evidence_name = [
                "血のついたコーヒーカップ",
                "謎のメモ",
                "目撃者の証言",
                "防犯カメラの映像", 
                "不審な領収書"
            ][i]
            
            print(f"  証拠{i+1}: {evidence_name}")
            print(f"     配置場所: {poi['name']} ({poi['type']})")
            print(f"     座標: {poi['location']['lat']:.6f}, {poi['location']['lng']:.6f}")
    
    # コスト概算
    api_calls = len(game_poi_types) * 1  # 各タイプ1回検索
    estimated_cost = api_calls * 0.017  # $17/1000 requests
    print(f"\n💰 このテストでのAPI使用量:")
    print(f"   Places API呼び出し: {api_calls}回")
    print(f"   推定コスト: ${estimated_cost:.4f} USD")
    
    return total_suitable >= 5

if __name__ == "__main__":
    print("🚀 Google Maps Places API テスト開始")
    print("=" * 50)
    
    if test_places_api_only():
        print("\n✅ テスト成功 - この地域でゲーム作成可能です！")
    else:
        print("\n⚠️  テスト完了 - POIの追加検討が必要かもしれません")
    
    print("\n🔧 次のステップ:")
    print("   1. Geocoding APIも有効にする (住所検索用)")
    print("   2. APIキーに制限を設定する (セキュリティ向上)")
    print("   3. 本格的なバックエンド統合を開始する")