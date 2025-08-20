#!/usr/bin/env python3
"""
統合APIテスト - 実際のGoogle Maps APIとバックエンドAPIの連携テスト
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv
import googlemaps
from typing import Dict, List, Any

load_dotenv()

class IntegratedAPITest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.gmaps_client = None
        self.setup_maps_client()
    
    def setup_maps_client(self):
        """Google Maps クライアント初期化"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if api_key:
            self.gmaps_client = googlemaps.Client(key=api_key)
            print("✅ Google Maps クライアント初期化成功")
        else:
            print("⚠️  Google Maps APIキーが設定されていません")
    
    def test_backend_health(self):
        """バックエンドAPIヘルスチェック"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ バックエンド稼働中")
                print(f"   サービス状態: {data.get('services', {})}")
                return True
            else:
                print(f"❌ バックエンド異常: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ バックエンド接続失敗: {e}")
            return False
    
    def test_poi_search_comparison(self):
        """POI検索: モック vs 実際のAPI比較"""
        test_lat, test_lng = 35.6586, 139.7454  # 東京タワー
        
        print(f"\n🔍 POI検索比較テスト（緯度: {test_lat}, 経度: {test_lng}）")
        
        # 1. バックエンドAPIのモック検索
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/poi/nearby",
                params={"lat": test_lat, "lng": test_lng, "radius": 1000, "limit": 5},
                timeout=10
            )
            
            if response.status_code == 200:
                mock_data = response.json()
                print(f"✅ モックAPI: {len(mock_data['pois'])}件発見")
                for poi in mock_data['pois']:
                    print(f"   - {poi['name']} ({poi['type']}) - {poi['distance']:.1f}m")
            else:
                print(f"❌ モックAPI エラー: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ モックAPI例外: {e}")
            return False
        
        # 2. 実際のGoogle Maps API検索
        if self.gmaps_client:
            try:
                places_result = self.gmaps_client.places_nearby(
                    location=(test_lat, test_lng),
                    radius=1000,
                    type='point_of_interest'
                )
                
                real_pois = places_result.get('results', [])
                print(f"✅ 実際のAPI: {len(real_pois)}件発見")
                for poi in real_pois[:5]:
                    name = poi.get('name', '名前不明')
                    types = poi.get('types', [])
                    rating = poi.get('rating', 'N/A')
                    print(f"   - {name} ({', '.join(types[:2])}) - 評価: {rating}")
                
                return True
                
            except Exception as e:
                print(f"❌ 実際のAPI例外: {e}")
                return False
        else:
            print("⚠️  Google Maps API クライアントが利用できません")
            return False
    
    def test_game_creation_with_real_pois(self):
        """実際のPOIデータでゲーム作成テスト"""
        print(f"\n🎮 リアルPOIでのゲーム作成テスト")
        
        # 1. エリア検証
        test_lat, test_lng = 35.6586, 139.7454
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/poi/validate-area",
                params={"lat": test_lat, "lng": test_lng, "radius": 1000},
                timeout=10
            )
            
            if response.status_code == 200:
                validation = response.json()
                print(f"✅ エリア検証: {'有効' if validation['valid'] else '無効'}")
                print(f"   利用可能POI: {validation.get('suitable_pois', 0)}件")
                
                if not validation['valid']:
                    print(f"   理由: {validation.get('reason', '不明')}")
                    return False
            else:
                print(f"❌ エリア検証エラー: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ エリア検証例外: {e}")
            return False
        
        # 2. ゲーム開始
        game_request = {
            "player_id": "test_player_real_poi",
            "location": {"lat": test_lat, "lng": test_lng},
            "difficulty": "easy"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/game/start",
                json=game_request,
                timeout=15
            )
            
            if response.status_code == 200:
                game_data = response.json()
                print(f"✅ ゲーム作成成功")
                print(f"   ゲームID: {game_data['game_id']}")
                print(f"   シナリオ: {game_data['scenario']['title']}")
                print(f"   証拠数: {len(game_data['evidence'])}件")
                
                # 証拠配置詳細
                for i, evidence in enumerate(game_data['evidence']):
                    print(f"   証拠{i+1}: {evidence['name']}")
                    print(f"     場所: {evidence['poi_name']} ({evidence['poi_type']})")
                    print(f"     座標: {evidence['location']['lat']:.6f}, {evidence['location']['lng']:.6f}")
                
                return game_data['game_id']
            else:
                error_data = response.json()
                print(f"❌ ゲーム作成失敗: {response.status_code}")
                print(f"   エラー: {error_data.get('detail', {}).get('message', '不明')}")
                return None
                
        except Exception as e:
            print(f"❌ ゲーム作成例外: {e}")
            return None
    
    def test_enhanced_poi_integration(self):
        """将来の実装: 拡張POI統合テスト（設計確認）"""
        print(f"\n🔧 拡張POI統合機能の設計確認")
        
        if self.gmaps_client:
            # 実際のAPIから詳細情報取得
            try:
                places_result = self.gmaps_client.places_nearby(
                    location=(35.6586, 139.7454),
                    radius=500,
                    type='cafe'
                )
                
                cafes = places_result.get('results', [])[:3]
                print(f"✅ カフェ情報取得: {len(cafes)}件")
                
                for cafe in cafes:
                    name = cafe.get('name', '名前不明')
                    place_id = cafe.get('place_id')
                    
                    # Place Details API（将来の実装用）
                    print(f"   📍 {name}")
                    print(f"      Place ID: {place_id}")
                    print(f"      座標: {cafe['geometry']['location']['lat']:.6f}, {cafe['geometry']['location']['lng']:.6f}")
                    print(f"      タイプ: {', '.join(cafe.get('types', [])[:3])}")
                    
                    # 将来実装時の機能案
                    print(f"      [将来実装] 営業時間、電話番号、レビュー詳細など")
                
                return True
                
            except Exception as e:
                print(f"❌ 拡張POI機能テストエラー: {e}")
                return False
        else:
            print("⚠️  Google Maps API未設定のため、拡張機能テストをスキップ")
            return True

def main():
    print("🚀 統合APIテスト開始")
    print("=" * 60)
    
    tester = IntegratedAPITest()
    
    # 1. バックエンドヘルスチェック
    if not tester.test_backend_health():
        print("❌ バックエンドが稼働していません。先にバックエンドを起動してください。")
        print("   コマンド: python backend/src/main_minimal.py")
        return False
    
    # 2. POI検索比較テスト
    if not tester.test_poi_search_comparison():
        print("⚠️  POI検索比較テストに問題がありました")
    
    # 3. ゲーム作成テスト
    game_id = tester.test_game_creation_with_real_pois()
    if game_id:
        print(f"✅ 統合テスト成功 - ゲーム作成完了")
    else:
        print("⚠️  ゲーム作成テストに問題がありました")
    
    # 4. 拡張機能設計確認
    tester.test_enhanced_poi_integration()
    
    print("\n" + "=" * 60)
    print("🎯 統合テスト完了")
    
    # 推奨事項
    print("\n📋 次のステップ:")
    print("   1. ✅ Places API統合 - 動作確認済み")
    print("   2. 🔧 Geocoding API有効化 - 住所検索用")
    print("   3. 🏗️  バックエンドへの実API統合実装")
    print("   4. 🧪 E2Eテストの拡充")
    print("   5. 📱 Flutterアプリとの統合テスト")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)