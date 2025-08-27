#!/usr/bin/env python3
"""
データベース統合テスト - Firestoreとローカルファイルの両方をテスト
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# 環境変数設定
os.environ['GOOGLE_CLOUD_PROJECT'] = 'detective-anywhere-local'
os.environ['USE_FIRESTORE_EMULATOR'] = 'false'  # まずはローカルファイルでテスト

print("🧪 データベース統合テスト")
print("=" * 60)

async def test_database_service():
    """データベースサービスの総合テスト"""
    
    try:
        from services.database_service import database_service
        print("✅ データベースサービスのインポート成功")
        
        # ヘルスチェック
        print("\n📊 ヘルスチェック実行...")
        health = await database_service.health_check()
        print(f"   データベースタイプ: {health['database_type']}")
        print(f"   ステータス: {health['status']}")
        if 'details' in health:
            for key, value in health['details'].items():
                print(f"   {key}: {value}")
        
        # テストデータ準備
        test_game_id = "test_game_123"
        test_player_id = "test_player_456"
        
        # ゲームセッションデータ作成
        test_game_data = {
            "game_id": test_game_id,
            "player_id": test_player_id,
            "status": "active",
            "difficulty": "normal",
            "scenario": {
                "title": "テストミステリー",
                "culprit": "テスト犯人",
                "motive": "テスト動機"
            },
            "evidence_list": [
                {
                    "evidence_id": "ev1",
                    "name": "テスト証拠1", 
                    "poi_name": "テストPOI",
                    "location": {"lat": 35.6762, "lng": 139.6503}
                }
            ],
            "discovered_evidence": [],
            "player_location": {"lat": 35.6762, "lng": 139.6503},
            "created_at": datetime.now()
        }
        
        print(f"\n🎮 ゲームセッションテスト (ID: {test_game_id})")
        
        # 1. 保存テスト
        print("   保存中...")
        save_result = await database_service.save_game_session(test_game_id, test_game_data)
        if save_result:
            print("   ✅ 保存成功")
        else:
            print("   ❌ 保存失敗")
            return False
        
        # 2. 取得テスト
        print("   取得中...")
        retrieved_data = await database_service.get_game_session(test_game_id)
        if retrieved_data:
            print("   ✅ 取得成功")
            print(f"      タイトル: {retrieved_data['scenario']['title']}")
            print(f"      作成日時: {retrieved_data['created_at']}")
        else:
            print("   ❌ 取得失敗")
            return False
        
        # 3. 更新テスト
        print("   更新中...")
        update_data = {
            "discovered_evidence": ["ev1"],
            "last_activity": datetime.now()
        }
        update_result = await database_service.update_game_session(test_game_id, update_data)
        if update_result:
            print("   ✅ 更新成功")
            
            # 更新確認
            updated_data = await database_service.get_game_session(test_game_id)
            if updated_data and "ev1" in updated_data.get("discovered_evidence", []):
                print("   ✅ 更新内容確認済み")
            else:
                print("   ❌ 更新内容が反映されていません")
        else:
            print("   ❌ 更新失敗")
        
        # 4. アクティブゲーム検索テスト
        print(f"\n👤 プレイヤーゲーム検索テスト (ID: {test_player_id})")
        active_games = await database_service.get_active_games_by_player(test_player_id)
        if active_games:
            print(f"   ✅ アクティブゲーム {len(active_games)} 件発見")
            for game in active_games:
                print(f"      ゲームID: {game.get('game_id', game.get('id'))}")
        else:
            print("   ⚠️  アクティブゲームが見つかりません")
        
        # 5. プレイヤーデータテスト
        print(f"\n👤 プレイヤーデータテスト")
        player_data = {
            "player_id": test_player_id,
            "name": "テストプレイヤー",
            "level": 1,
            "total_games": 1,
            "last_login": datetime.now()
        }
        
        player_save_result = await database_service.save_player_data(test_player_id, player_data)
        if player_save_result:
            print("   ✅ プレイヤーデータ保存成功")
            
            # 取得確認
            retrieved_player = await database_service.get_player_data(test_player_id)
            if retrieved_player:
                print(f"   ✅ プレイヤーデータ取得成功: {retrieved_player['name']}")
            else:
                print("   ❌ プレイヤーデータ取得失敗")
        else:
            print("   ❌ プレイヤーデータ保存失敗")
        
        # 6. ゲーム履歴テスト
        print(f"\n📚 ゲーム履歴テスト")
        history_data = {
            "game_id": test_game_id,
            "player_id": test_player_id,
            "title": "テストミステリー",
            "completed_at": datetime.now(),
            "score": 850,
            "difficulty": "normal",
            "duration": 1200
        }
        
        history_save_result = await database_service.save_game_history(
            f"{test_game_id}_history", history_data
        )
        if history_save_result:
            print("   ✅ ゲーム履歴保存成功")
        else:
            print("   ❌ ゲーム履歴保存失敗")
        
        print(f"\n🎉 データベース統合テスト完了！")
        print(f"   データベースタイプ: {health['database_type']}")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_firestore():
    """Firestoreを使用したテスト"""
    print(f"\n🔥 Firestoreモードでのテスト")
    print("-" * 40)
    
    # Firestoreモードに切り替え
    os.environ['USE_FIRESTORE_EMULATOR'] = 'true'
    
    # 新しいインスタンスを作成して再テスト
    try:
        from importlib import reload
        import services.database_service
        reload(services.database_service)
        
        from services.database_service import database_service
        
        # ヘルスチェック
        health = await database_service.health_check()
        print(f"   データベースタイプ: {health['database_type']}")
        print(f"   ステータス: {health['status']}")
        
        if health['status'] == 'healthy':
            print("   ✅ Firestore接続成功 - 基本テスト実行可能")
            return True
        else:
            print("   ⚠️  Firestore接続に問題があります")
            return False
            
    except Exception as e:
        print(f"   ❌ Firestoreテストエラー: {e}")
        return False

async def main():
    """メイン実行関数"""
    
    # まずローカルファイルでテスト
    print("Phase 1: ローカルファイルデータベーステスト")
    local_success = await test_database_service()
    
    # Firestoreテスト
    print(f"\nPhase 2: Firestoreテスト")
    firestore_success = await test_with_firestore()
    
    # 結果サマリー
    print(f"\n" + "=" * 60)
    print(f"📊 テスト結果サマリー")
    print(f"   ローカルファイルDB: {'✅ 成功' if local_success else '❌ 失敗'}")
    print(f"   Firestore: {'✅ 成功' if firestore_success else '❌ 失敗'}")
    
    if local_success:
        print(f"\n🎉 統合テスト成功！")
        print(f"   ローカル開発環境でのゲーム機能は正常に動作します")
        
        if firestore_success:
            print(f"   Firestore統合も準備完了しています")
        else:
            print(f"   Firestore接続は環境設定後に利用可能になります")
            
    else:
        print(f"\n❌ 統合テスト失敗")
        print(f"   データベース設定を確認してください")

if __name__ == "__main__":
    asyncio.run(main())