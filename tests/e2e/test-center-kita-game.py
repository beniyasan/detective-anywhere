#!/usr/bin/env python3
"""
センター北駅周辺での難易度「難しい」ゲーム作成テスト
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv
import googlemaps
from typing import Dict, List, Any

load_dotenv()

class CenterKitaGameTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.gmaps_client = None
        self.setup_maps_client()
        
        # センター北駅の座標
        self.center_kita_location = {
            "lat": 35.5949,
            "lng": 139.5651
        }
    
    def setup_maps_client(self):
        """Google Maps クライアント初期化"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if api_key:
            self.gmaps_client = googlemaps.Client(key=api_key)
            print("✅ Google Maps クライアント初期化成功")
        else:
            print("❌ Google Maps APIキーが設定されていません")
    
    def start_backend_if_needed(self):
        """バックエンドが稼働していなければ起動"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=3)
            if response.status_code == 200:
                print("✅ バックエンドは既に稼働中")
                return True
        except:
            pass
        
        print("🚀 バックエンドを起動中...")
        import subprocess
        import time
        
        # バックエンドをバックグラウンドで起動
        process = subprocess.Popen([
            "python", "backend/src/main_minimal.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 少し待ってからヘルスチェック
        time.sleep(3)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ バックエンド起動完了")
                return True
        except:
            print("❌ バックエンド起動に失敗")
            return False
    
    def explore_center_kita_area(self):
        """センター北駅周辺のPOI調査"""
        print(f"\n🔍 センター北駅周辺のPOI調査")
        print("=" * 50)
        print(f"📍 中心座標: {self.center_kita_location['lat']}, {self.center_kita_location['lng']}")
        
        if not self.gmaps_client:
            print("❌ Google Maps API未設定")
            return False
        
        # 周辺POI検索
        try:
            places_result = self.gmaps_client.places_nearby(
                location=(self.center_kita_location["lat"], self.center_kita_location["lng"]),
                radius=1000,  # 1km圏内
                type='point_of_interest'
            )
            
            total_pois = len(places_result.get('results', []))
            print(f"✅ 周辺POI総数: {total_pois}件")
            
            # タイプ別分析
            poi_types = {}
            suitable_pois = []
            
            for place in places_result.get('results', []):
                name = place.get('name', '名前不明')
                types = place.get('types', [])
                rating = place.get('rating', 0)
                location = place['geometry']['location']
                
                # POIタイプ分類
                for poi_type in types:
                    if poi_type not in poi_types:
                        poi_types[poi_type] = 0
                    poi_types[poi_type] += 1
                
                # ゲーム用POI判定
                game_suitable_types = {
                    'cafe', 'restaurant', 'store', 'park', 'shopping_mall',
                    'library', 'bank', 'post_office', 'convenience_store',
                    'train_station', 'subway_station', 'tourist_attraction'
                }
                
                if any(t in game_suitable_types for t in types):
                    suitable_pois.append({
                        'name': name,
                        'types': types,
                        'rating': rating,
                        'location': location
                    })
            
            print(f"✅ ゲーム適性POI: {len(suitable_pois)}件")
            
            # 上位POIタイプ表示
            sorted_types = sorted(poi_types.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"\n📊 主要POIタイプ:")
            for poi_type, count in sorted_types:
                print(f"   {poi_type}: {count}件")
            
            # ゲーム適性POI詳細表示
            print(f"\n🎮 ゲーム適性POI（上位10件）:")
            for i, poi in enumerate(suitable_pois[:10]):
                types_str = ', '.join(poi['types'][:3])
                print(f"   {i+1}. {poi['name']}")
                print(f"      タイプ: {types_str}")
                print(f"      評価: {poi['rating']}/5.0")
                print(f"      座標: {poi['location']['lat']:.6f}, {poi['location']['lng']:.6f}")
            
            return len(suitable_pois) >= 5
            
        except Exception as e:
            print(f"❌ POI調査エラー: {e}")
            return False
    
    def create_hard_difficulty_game(self):
        """難易度「難しい」でゲーム作成"""
        print(f"\n🎲 難易度「難しい」ゲーム作成")
        print("=" * 50)
        
        # ゲーム作成リクエスト
        game_request = {
            "player_id": "test_player_center_kita",
            "location": self.center_kita_location,
            "difficulty": "hard"
        }
        
        try:
            # エリア検証
            print("🔍 エリア検証中...")
            validation_response = requests.post(
                f"{self.base_url}/api/v1/poi/validate-area",
                params={
                    "lat": self.center_kita_location["lat"],
                    "lng": self.center_kita_location["lng"],
                    "radius": 1000
                },
                timeout=10
            )
            
            if validation_response.status_code == 200:
                validation_data = validation_response.json()
                print(f"✅ エリア検証結果: {'有効' if validation_data['valid'] else '無効'}")
                if validation_data['valid']:
                    print(f"   利用可能POI: {validation_data.get('suitable_pois', 0)}件")
                else:
                    print(f"   理由: {validation_data.get('reason', '不明')}")
                    print(f"   推奨事項: {validation_data.get('recommendations', [])}")
            
            # ゲーム作成実行
            print("🚀 ゲーム作成実行中...")
            response = requests.post(
                f"{self.base_url}/api/v1/game/start",
                json=game_request,
                timeout=15
            )
            
            if response.status_code == 200:
                game_data = response.json()
                
                print(f"\n🎉 ゲーム作成成功！")
                print(f"=" * 50)
                print(f"🆔 ゲームID: {game_data['game_id']}")
                print(f"📍 場所: センター北駅周辺")
                print(f"🎚️  難易度: 難しい (hard)")
                
                # シナリオ情報
                scenario = game_data['scenario']
                print(f"\n📖 シナリオ: {scenario['title']}")
                print(f"📝 あらすじ:")
                print(f"   {scenario['description']}")
                
                # 被害者情報
                victim = scenario['victim']
                print(f"\n💀 被害者: {victim['name']} ({victim['age']}歳)")
                print(f"   職業: {victim['occupation']}")
                print(f"   性格: {victim['personality']}")
                
                # 容疑者情報
                suspects = scenario['suspects']
                print(f"\n🕵️ 容疑者一覧 ({len(suspects)}名):")
                for i, suspect in enumerate(suspects):
                    print(f"   {i+1}. {suspect['name']} ({suspect['age']}歳)")
                    print(f"      職業: {suspect['occupation']}")
                    print(f"      性格: {suspect['personality']}")
                    print(f"      関係: {suspect['relationship']}")
                    if suspect.get('alibi'):
                        print(f"      アリバイ: {suspect['alibi']}")
                    if suspect.get('motive'):
                        print(f"      動機: {suspect['motive']}")
                    print()
                
                # 真犯人（デバッグ用）
                print(f"🔍 真犯人: {scenario['culprit']} (デバッグ用)")
                
                # 証拠情報
                evidence_list = game_data['evidence']
                print(f"\n🔎 証拠一覧 ({len(evidence_list)}件):")
                for i, evidence in enumerate(evidence_list):
                    print(f"   {i+1}. {evidence['name']}")
                    print(f"      重要度: {evidence['importance']}")
                    print(f"      配置場所: {evidence['poi_name']} ({evidence['poi_type']})")
                    print(f"      座標: {evidence['location']['lat']:.6f}, {evidence['location']['lng']:.6f}")
                    print(f"      ヒント: {evidence['description']}")
                    print()
                
                # ゲームルール
                game_rules = game_data['game_rules']
                print(f"🎮 ゲームルール:")
                print(f"   発見半径: {game_rules['discovery_radius']}m")
                print(f"   制限時間: {game_rules.get('time_limit', '制限なし')}")
                print(f"   最大証拠数: {game_rules['max_evidence']}件")
                
                # 統計情報
                print(f"\n📊 ゲーム統計:")
                print(f"   シナリオの複雑度: {'高' if len(suspects) >= 4 else '中' if len(suspects) >= 3 else '低'}")
                print(f"   証拠の散布範囲: 約1km圏内")
                print(f"   推定プレイ時間: {len(evidence_list) * 10}-{len(evidence_list) * 15}分")
                
                return game_data
            else:
                error_data = response.json() if response.content else {}
                print(f"❌ ゲーム作成失敗: {response.status_code}")
                print(f"エラー: {error_data.get('detail', {}).get('message', '不明なエラー')}")
                return None
                
        except Exception as e:
            print(f"❌ ゲーム作成例外: {e}")
            return None

def main():
    print("🎮 センター北駅・難易度「難しい」ゲーム作成テスト")
    print("=" * 60)
    
    tester = CenterKitaGameTest()
    
    # 1. バックエンド起動確認
    if not tester.start_backend_if_needed():
        print("❌ バックエンドの起動に失敗しました")
        return False
    
    # 2. 地域調査
    if not tester.explore_center_kita_area():
        print("⚠️  センター北駅周辺のPOI調査で問題が発生しましたが、ゲーム作成を試行します")
    
    # 3. ゲーム作成
    game_data = tester.create_hard_difficulty_game()
    
    if game_data:
        print(f"\n🎯 テスト完了: ゲーム作成成功")
        return True
    else:
        print(f"\n❌ テスト失敗: ゲーム作成エラー")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)