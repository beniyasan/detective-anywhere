#!/usr/bin/env python3
"""
Firestore統合テスト - ローカル環境でのデータベース機能確認
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# 環境変数設定（Firestoreエミュレーター用）
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'detective-anywhere-local'
os.environ['USE_FIRESTORE_EMULATOR'] = 'true'

try:
    from backend.src.core.database import (
        initialize_firestore, 
        game_session_repo, 
        player_repo, 
        game_history_repo,
        health_check
    )
    from backend.src.core.config import settings
    FIRESTORE_AVAILABLE = True
    print("✅ Firestoreモジュールのインポート成功")
except ImportError as e:
    print(f"⚠️ Firestoreモジュールのインポート失敗: {e}")
    FIRESTORE_AVAILABLE = False


class MockGameSession:
    """テスト用ゲームセッション"""
    
    def __init__(self, game_id: str, player_id: str):
        self.game_id = game_id
        self.player_id = player_id
        self.status = "active"
        self.difficulty = "normal"
        self.created_at = datetime.now()
        self.player_location = {"lat": 35.5070, "lng": 139.6176}
        self.scenario = {
            "title": "新横浜駅の謎",
            "description": "新横浜駅で起きた不可解な事件",
            "suspects": [
                {"name": "田中太郎", "age": 45, "occupation": "会社員"},
                {"name": "佐藤花子", "age": 35, "occupation": "看護師"}
            ],
            "culprit": "田中太郎"
        }
        self.evidence_list = [
            {
                "evidence_id": "evidence_1",
                "name": "血痕の付いたハンカチ",
                "location": {"lat": 35.5075, "lng": 139.6180},
                "poi_name": "新横浜公園"
            }
        ]
        self.discovered_evidence = []
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            "game_id": self.game_id,
            "player_id": self.player_id,
            "status": self.status,
            "difficulty": self.difficulty,
            "player_location": self.player_location,
            "scenario": self.scenario,
            "evidence_list": self.evidence_list,
            "discovered_evidence": self.discovered_evidence,
            "created_at": self.created_at
        }


async def test_firestore_connection():
    """Firestore接続テスト"""
    print("🔌 Firestore接続テスト")
    print("=" * 50)
    
    if not FIRESTORE_AVAILABLE:
        print("❌ Firestoreモジュールが利用できません")
        return False
    
    try:
        # Firestore初期化
        await initialize_firestore()
        print("✅ Firestore初期化成功")
        
        # ヘルスチェック
        health_result = await health_check()
        print(f"📊 ヘルスチェック: {health_result}")
        
        if health_result["status"] == "healthy":
            print("✅ Firestore接続成功")
            return True
        else:
            print(f"❌ Firestore接続失敗: {health_result.get('error', '不明なエラー')}")
            return False
            
    except Exception as e:
        print(f"❌ Firestore接続エラー: {e}")
        return False


async def test_game_session_repository():
    """ゲームセッションリポジトリのテスト"""
    print("\n🎮 ゲームセッションリポジトリテスト")
    print("=" * 50)
    
    try:
        # テストデータ作成
        test_game = MockGameSession("test_game_001", "test_player_001")
        game_data = test_game.to_dict()
        
        print(f"📝 ゲームセッション作成: {test_game.game_id}")
        
        # ゲームセッション保存
        created_id = await game_session_repo.create(test_game.game_id, game_data)
        print(f"✅ ゲームセッション保存成功: {created_id}")
        
        # ゲームセッション取得
        retrieved_game = await game_session_repo.get(test_game.game_id)
        if retrieved_game:
            print(f"✅ ゲームセッション取得成功")
            print(f"   タイトル: {retrieved_game['scenario']['title']}")
            print(f"   プレイヤー: {retrieved_game['player_id']}")
            print(f"   状態: {retrieved_game['status']}")
        else:
            print("❌ ゲームセッション取得失敗")
            return False
        
        # アクティブゲーム検索
        active_games = await game_session_repo.get_active_games_by_player("test_player_001")
        print(f"📊 アクティブゲーム数: {len(active_games)}")
        
        # ゲームセッション更新
        update_data = {"status": "completed", "completed_at": datetime.now()}
        update_success = await game_session_repo.update(test_game.game_id, update_data)
        print(f"🔄 ゲームセッション更新: {'成功' if update_success else '失敗'}")
        
        # 更新後の取得確認
        updated_game = await game_session_repo.get(test_game.game_id)
        if updated_game and updated_game["status"] == "completed":
            print("✅ ゲームセッション更新確認成功")
        
        return True
        
    except Exception as e:
        print(f"❌ ゲームセッションリポジトリテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_player_repository():
    """プレイヤーリポジトリのテスト"""
    print("\n👤 プレイヤーリポジトリテスト")
    print("=" * 50)
    
    try:
        player_id = "test_player_001"
        player_data = {
            "name": "テストプレイヤー",
            "email": "test@example.com",
            "level": 1,
            "total_games": 0,
            "total_score": 0,
            "joined_at": datetime.now()
        }
        
        # プレイヤー作成
        created_player_id = await player_repo.create_or_update_player(player_id, player_data)
        print(f"✅ プレイヤー作成成功: {created_player_id}")
        
        # プレイヤー取得
        retrieved_player = await player_repo.get(player_id)
        if retrieved_player:
            print(f"✅ プレイヤー取得成功: {retrieved_player['name']}")
        else:
            print("❌ プレイヤー取得失敗")
            return False
        
        # プレイヤー更新
        update_data = {"total_games": 1, "total_score": 150}
        updated_player_id = await player_repo.create_or_update_player(player_id, update_data)
        print(f"🔄 プレイヤー更新成功: {updated_player_id}")
        
        # 更新確認
        updated_player = await player_repo.get(player_id)
        if updated_player and updated_player["total_games"] == 1:
            print("✅ プレイヤー更新確認成功")
        
        return True
        
    except Exception as e:
        print(f"❌ プレイヤーリポジトリテストエラー: {e}")
        return False


async def test_game_history_repository():
    """ゲーム履歴リポジトリのテスト"""
    print("\n📊 ゲーム履歴リポジトリテスト")
    print("=" * 50)
    
    try:
        # テスト履歴データ作成
        history_data = {
            "game_id": "test_game_001",
            "player_id": "test_player_001", 
            "title": "新横浜駅の謎",
            "completed_at": datetime.now(),
            "score": 150,
            "difficulty": "normal",
            "location_name": "新横浜駅",
            "duration": 1800,  # 30分
            "evidence_found_rate": 0.8
        }
        
        # 履歴保存
        history_id = f"{history_data['game_id']}_history"
        created_id = await game_history_repo.create(history_id, history_data)
        print(f"✅ ゲーム履歴保存成功: {created_id}")
        
        # プレイヤー履歴取得
        player_history = await game_history_repo.get_player_history("test_player_001", limit=5)
        print(f"📊 プレイヤー履歴取得: {len(player_history)}件")
        
        if player_history:
            latest_game = player_history[0]
            print(f"   最新ゲーム: {latest_game['title']} (スコア: {latest_game['score']})")
        
        return True
        
    except Exception as e:
        print(f"❌ ゲーム履歴リポジトリテストエラー: {e}")
        return False


async def test_complete_game_flow():
    """完全なゲームフローのテスト"""
    print("\n🎯 完全ゲームフローテスト")
    print("=" * 50)
    
    try:
        # 1. プレイヤー作成
        player_id = "flow_test_player"
        player_data = {
            "name": "フローテストプレイヤー",
            "level": 1,
            "total_games": 0
        }
        
        await player_repo.create_or_update_player(player_id, player_data)
        print("✅ Step 1: プレイヤー作成完了")
        
        # 2. ゲームセッション開始
        game_id = "flow_test_game"
        test_game = MockGameSession(game_id, player_id)
        await game_session_repo.create(game_id, test_game.to_dict())
        print("✅ Step 2: ゲームセッション開始完了")
        
        # 3. 証拠発見の記録（模擬）
        evidence_update = {
            "discovered_evidence": ["evidence_1"],
            "last_activity": datetime.now()
        }
        await game_session_repo.update(game_id, evidence_update)
        print("✅ Step 3: 証拠発見記録完了")
        
        # 4. ゲーム完了
        completion_data = {
            "status": "completed",
            "completed_at": datetime.now(),
            "final_score": 180
        }
        await game_session_repo.update(game_id, completion_data)
        print("✅ Step 4: ゲーム完了記録完了")
        
        # 5. 履歴保存
        history_data = {
            "game_id": game_id,
            "player_id": player_id,
            "title": "新横浜駅の謎",
            "completed_at": datetime.now(),
            "score": 180,
            "difficulty": "normal"
        }
        await game_history_repo.create(f"{game_id}_history", history_data)
        print("✅ Step 5: 履歴保存完了")
        
        # 6. プレイヤー統計更新
        player_update = {"total_games": 1, "total_score": 180}
        await player_repo.create_or_update_player(player_id, player_update)
        print("✅ Step 6: プレイヤー統計更新完了")
        
        print("\n🎉 完全ゲームフローテスト成功！")
        return True
        
    except Exception as e:
        print(f"❌ 完全ゲームフローテストエラー: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("🚀 Firestore統合テスト開始")
    print("=" * 70)
    
    # 環境情報表示
    print(f"📍 プロジェクトID: {os.getenv('GOOGLE_CLOUD_PROJECT', 'なし')}")
    print(f"🔥 Firestoreエミュレーター: {os.getenv('FIRESTORE_EMULATOR_HOST', 'なし')}")
    print(f"🏗️ エミュレーター使用: {os.getenv('USE_FIRESTORE_EMULATOR', 'false')}")
    
    success_count = 0
    total_tests = 5
    
    try:
        # 1. 接続テスト
        if await test_firestore_connection():
            success_count += 1
        
        # 2. ゲームセッションリポジトリテスト
        if await test_game_session_repository():
            success_count += 1
        
        # 3. プレイヤーリポジトリテスト
        if await test_player_repository():
            success_count += 1
        
        # 4. ゲーム履歴リポジトリテスト
        if await test_game_history_repository():
            success_count += 1
        
        # 5. 完全フローテスト
        if await test_complete_game_flow():
            success_count += 1
        
        # 結果サマリー
        print("\n" + "=" * 70)
        print(f"📊 テスト結果: {success_count}/{total_tests} 成功")
        
        if success_count == total_tests:
            print("🎉 全てのFirestore統合テストが成功しました！")
            print("\n✅ 利用可能な機能:")
            print("  • ゲームセッション管理")
            print("  • プレイヤーデータ管理") 
            print("  • ゲーム履歴管理")
            print("  • 完全なゲームフロー")
            return 0
        else:
            print("⚠️ 一部のテストが失敗しました")
            return 1
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)