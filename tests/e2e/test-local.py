#!/usr/bin/env python3
"""
ローカル環境テストスクリプト
APIエンドポイントの動作確認
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class LocalTester:
    """ローカル環境テスター"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def test_health_check(self) -> bool:
        """ヘルスチェックテスト"""
        print("🏥 ヘルスチェックテスト...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ ヘルスチェック成功: {data.get('status')}")
                return True
            else:
                print(f"❌ ヘルスチェック失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 接続エラー: {e}")
            return False
    
    async def test_poi_search(self) -> bool:
        """POI検索テスト"""
        print("\n📍 POI検索テスト...")
        
        try:
            # 東京タワー周辺
            params = {
                "lat": 35.6762,
                "lng": 139.6503,
                "radius": 1000,
                "limit": 10
            }
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/poi/nearby",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                poi_count = len(data.get("pois", []))
                print(f"✅ POI検索成功: {poi_count}件のPOIを発見")
                
                # 最初のPOIを表示
                if poi_count > 0:
                    first_poi = data["pois"][0]
                    print(f"   例: {first_poi['name']} ({first_poi['type']})")
                
                return True
            else:
                print(f"❌ POI検索失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ POI検索エラー: {e}")
            return False
    
    async def test_game_start(self) -> str:
        """ゲーム開始テスト"""
        print("\n🎮 ゲーム開始テスト...")
        
        try:
            game_data = {
                "player_id": "test_player_001",
                "location": {
                    "lat": 35.6762,
                    "lng": 139.6503
                },
                "difficulty": "easy"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/game/start",
                json=game_data
            )
            
            if response.status_code == 200:
                data = response.json()
                game_id = data.get("game_id")
                scenario_title = data.get("scenario", {}).get("title", "不明")
                evidence_count = len(data.get("evidence", []))
                
                print(f"✅ ゲーム開始成功!")
                print(f"   ゲームID: {game_id}")
                print(f"   シナリオ: {scenario_title}")
                print(f"   証拠数: {evidence_count}個")
                
                return game_id
            else:
                error_detail = response.json() if response.headers.get("content-type") == "application/json" else response.text
                print(f"❌ ゲーム開始失敗: {response.status_code}")
                print(f"   エラー詳細: {error_detail}")
                return None
                
        except Exception as e:
            print(f"❌ ゲーム開始エラー: {e}")
            return None
    
    async def test_game_status(self, game_id: str) -> bool:
        """ゲーム状態テスト"""
        print(f"\n📊 ゲーム状態テスト (ID: {game_id[:8]}...)...")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/game/{game_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                progress = data.get("progress", {})
                
                print(f"✅ ゲーム状態取得成功")
                print(f"   状態: {status}")
                print(f"   進行率: {progress.get('completion_rate', 0)*100:.1f}%")
                
                return True
            else:
                print(f"❌ ゲーム状態取得失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ ゲーム状態エラー: {e}")
            return False
    
    async def test_location_validation(self) -> bool:
        """位置検証テスト"""
        print("\n🌍 位置検証テスト...")
        
        try:
            params = {
                "lat": 35.6762,
                "lng": 139.6503,
                "radius": 1000
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/poi/validate-area",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get("valid", False)
                total_pois = data.get("total_pois", 0)
                
                if is_valid:
                    print(f"✅ エリア検証成功: {total_pois}個のPOIが利用可能")
                else:
                    print(f"⚠️ エリア使用不可: {data.get('reason')}")
                
                return True
            else:
                print(f"❌ エリア検証失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ エリア検証エラー: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """全テスト実行"""
        print("🚀 ローカル環境テスト開始\n" + "="*50)
        
        results = {}
        
        # 1. ヘルスチェック
        results["health"] = await self.test_health_check()
        if not results["health"]:
            print("❌ サーバーが起動していません。先にサーバーを起動してください。")
            return results
        
        # 2. POI検索
        results["poi_search"] = await self.test_poi_search()
        
        # 3. 位置検証
        results["location_validation"] = await self.test_location_validation()
        
        # 4. ゲーム開始
        game_id = await self.test_game_start()
        results["game_start"] = game_id is not None
        
        # 5. ゲーム状態（ゲームが開始できた場合のみ）
        if game_id:
            results["game_status"] = await self.test_game_status(game_id)
        
        # 結果サマリー
        print("\n" + "="*50)
        print("📊 テスト結果サマリー:")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 総合結果: {passed}/{total} テスト通過")
        
        if passed == total:
            print("🎉 すべてのテストに合格しました！")
        else:
            print("⚠️ 一部のテストが失敗しました。ログを確認してください。")
        
        return results


async def main():
    """メイン関数"""
    async with LocalTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())