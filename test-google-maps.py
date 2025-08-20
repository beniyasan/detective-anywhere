#!/usr/bin/env python3
"""
Google Maps API テストスクリプト
.envのAPIキーを使用して実際のGoogle Maps APIをテスト
"""

import os
import sys
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import googlemaps

# 環境変数読み込み
load_dotenv()

def test_google_maps_api():
    """Google Maps APIのテスト"""
    
    # APIキー取得
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY が設定されていません")
        return False
    
    print(f"🔑 APIキー確認: {api_key[:20]}...")
    
    # Google Maps クライアント初期化
    try:
        gmaps = googlemaps.Client(key=api_key)
        print("✅ Google Maps クライアント初期化成功")
    except Exception as e:
        print(f"❌ Google Maps クライアント初期化失敗: {e}")
        return False
    
    # テスト用座標（東京タワー周辺）
    test_location = {
        "lat": 35.6586, 
        "lng": 139.7454
    }
    print(f"📍 テスト地点: 東京タワー周辺 ({test_location['lat']}, {test_location['lng']})")
    
    # 1. Places API テスト - 周辺施設検索
    print("\n🔍 Places API テスト - 周辺施設検索")
    try:
        places_result = gmaps.places_nearby(
            location=(test_location["lat"], test_location["lng"]),
            radius=1000,  # 1km圏内
            type='point_of_interest'
        )
        
        if places_result.get('results'):
            print(f"✅ 周辺POI検索成功: {len(places_result['results'])}件発見")
            
            # 上位5件を表示
            for i, place in enumerate(places_result['results'][:5]):
                name = place.get('name', '名前不明')
                types = place.get('types', [])
                rating = place.get('rating', 'N/A')
                print(f"  {i+1}. {name} (タイプ: {', '.join(types[:3])}, 評価: {rating})")
        else:
            print("⚠️  検索結果が空です")
            
    except Exception as e:
        print(f"❌ Places API エラー: {e}")
        return False
    
    # 2. Geocoding API テスト
    print("\n🌍 Geocoding API テスト")
    try:
        # 住所から座標
        geocode_result = gmaps.geocode('東京タワー')
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            formatted_address = geocode_result[0]['formatted_address']
            print(f"✅ ジオコーディング成功:")
            print(f"   住所: {formatted_address}")
            print(f"   座標: {location['lat']}, {location['lng']}")
        else:
            print("⚠️  ジオコーディング結果が空です")
            
    except Exception as e:
        print(f"❌ Geocoding API エラー: {e}")
        return False
    
    # 3. ゲーム用POI検索テスト（カフェ、公園など）
    print("\n☕ ゲーム用POI検索テスト")
    game_poi_types = ['cafe', 'park', 'tourist_attraction', 'store']
    
    for poi_type in game_poi_types:
        try:
            places_result = gmaps.places_nearby(
                location=(test_location["lat"], test_location["lng"]),
                radius=800,
                type=poi_type
            )
            
            count = len(places_result.get('results', []))
            print(f"  📍 {poi_type}: {count}件")
            
            # 詳細表示（最大2件）
            for place in places_result.get('results', [])[:2]:
                name = place.get('name', '名前不明')
                vicinity = place.get('vicinity', '住所不明')
                print(f"     - {name} ({vicinity})")
                
        except Exception as e:
            print(f"❌ {poi_type} 検索エラー: {e}")
    
    # 4. APIクォータ使用量確認
    print(f"\n💰 API使用量: この テストで約10-15リクエスト使用")
    print(f"   Places API: 通常 $17/1000リクエスト")
    print(f"   Geocoding API: 通常 $5/1000リクエスト")
    
    return True

def test_poi_game_suitability():
    """ゲーム用POI適性テスト"""
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return False
        
    gmaps = googlemaps.Client(key=api_key)
    
    print("\n🎮 ゲーム適性評価テスト")
    
    # 東京タワー周辺での証拠配置に適したPOI検索
    try:
        places_result = gmaps.places_nearby(
            location=(35.6586, 139.7454),
            radius=500,  # より狭い範囲でゲーム適性を評価
            type='point_of_interest'
        )
        
        suitable_pois = []
        for place in places_result.get('results', []):
            types = place.get('types', [])
            name = place.get('name', '')
            rating = place.get('rating', 0)
            
            # ゲーム証拠配置に適したPOIを判定
            suitable_types = {
                'cafe', 'restaurant', 'park', 'tourist_attraction',
                'store', 'museum', 'library', 'bank', 'post_office'
            }
            
            if any(t in suitable_types for t in types) and rating >= 4.0:
                suitable_pois.append({
                    'name': name,
                    'types': types,
                    'rating': rating,
                    'location': place['geometry']['location']
                })
        
        print(f"✅ 証拠配置適性POI: {len(suitable_pois)}件発見")
        
        for i, poi in enumerate(suitable_pois[:3]):
            print(f"  {i+1}. {poi['name']}")
            print(f"     評価: {poi['rating']}/5.0")
            print(f"     タイプ: {', '.join(poi['types'][:3])}")
            print(f"     座標: {poi['location']['lat']:.6f}, {poi['location']['lng']:.6f}")
            print()
            
        return len(suitable_pois) >= 3  # 最低3件以上でゲーム作成可能
        
    except Exception as e:
        print(f"❌ ゲーム適性テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Google Maps API テスト開始")
    print("=" * 50)
    
    # 基本APIテスト
    if test_google_maps_api():
        print("\n" + "=" * 50)
        print("✅ Google Maps API 基本テスト完了")
        
        # ゲーム適性テスト
        if test_poi_game_suitability():
            print("✅ この地域はゲーム作成に適しています")
        else:
            print("⚠️  この地域はPOIが少ないためゲーム作成に不向きかもしれません")
    else:
        print("❌ Google Maps API テスト失敗")
        sys.exit(1)
    
    print("\n🎯 テスト完了")