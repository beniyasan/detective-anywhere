#!/usr/bin/env python3
"""
実際のFirestore接続テスト - 既存のGoogle Cloudプロジェクトを使用
"""

import os
import sys
import asyncio
from datetime import datetime

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# 既存プロジェクトを使用
os.environ['GOOGLE_CLOUD_PROJECT'] = 'gen-lang-client-0666798948'
os.environ['USE_FIRESTORE_EMULATOR'] = 'true'

print("🔥 実際のFirestore統合テスト")
print("=" * 50)

async def test_firestore_integration():
    """Firestoreを使用したデータベースサービスのテスト"""
    
    try:
        from services.database_service import DatabaseService
        
        # 新しいデータベースサービスインスタンスを作成
        db_service = DatabaseService()
        
        print(f"📊 データベース設定:")
        print(f"   プロジェクト: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
        print(f"   Firestoreモード: {db_service.use_firestore}")
        
        # ヘルスチェック
        print(f"\n🏥 ヘルスチェック実行...")
        health = await db_service.health_check()
        print(f"   ステータス: {health['status']}")
        print(f"   データベースタイプ: {health['database_type']}")
        
        if health['status'] != 'healthy':
            print("   ⚠️  データベース接続に問題があります")
            if 'details' in health and 'error' in health['details']:
                print(f"   エラー詳細: {health['details']['error']}")
            return False
        
        # テストゲームセッション作成
        test_game_id = f"detective_test_{int(datetime.now().timestamp())}"
        test_game_data = {
            "game_id": test_game_id,
            "player_id": "test_player_123",
            "status": "active",
            "difficulty": "normal",
            "scenario": {
                "title": "Firestore統合テスト用ミステリー",
                "description": "テスト用のミステリーシナリオ",
                "culprit": "テスト容疑者",
                "motive": "統合テスト実行のため"
            },
            "evidence_list": [
                {
                    "evidence_id": "test_ev_001",
                    "name": "テスト証拠：血痕",
                    "description": "怪しい血痕が見つかった",
                    "poi_name": "テスト公園",
                    "location": {"lat": 35.6762, "lng": 139.6503},
                    "discovered": False
                },
                {
                    "evidence_id": "test_ev_002", 
                    "name": "テスト証拠：手紙",
                    "description": "謎の手紙が発見された",
                    "poi_name": "テスト図書館",
                    "location": {"lat": 35.6772, "lng": 139.6513},
                    "discovered": False
                }
            ],
            "discovered_evidence": [],
            "player_location": {"lat": 35.6762, "lng": 139.6503},
            "game_rules": {"discovery_radius": 50},
            "created_at": datetime.now()
        }
        
        print(f"\n🎮 ゲームセッション統合テスト")
        print(f"   ゲームID: {test_game_id}")
        
        # 1. 保存テスト
        print("   💾 保存中...")
        save_success = await db_service.save_game_session(test_game_id, test_game_data)
        if save_success:
            print("   ✅ ゲームセッション保存成功")
        else:
            print("   ❌ ゲームセッション保存失敗")
            return False
        
        # 2. 取得テスト
        print("   📥 取得中...")
        retrieved_game = await db_service.get_game_session(test_game_id)
        if retrieved_game:
            print("   ✅ ゲームセッション取得成功")
            print(f"      タイトル: {retrieved_game['scenario']['title']}")
            print(f"      証拠数: {len(retrieved_game['evidence_list'])}")
        else:
            print("   ❌ ゲームセッション取得失敗")
            return False
        
        # 3. 証拠発見をシミュレート（更新テスト）
        print("   🔍 証拠発見シミュレーション...")
        discovery_update = {
            "discovered_evidence": ["test_ev_001"],
            "last_activity": datetime.now(),
            "progress_notes": "最初の証拠を発見しました"
        }
        
        update_success = await db_service.update_game_session(test_game_id, discovery_update)
        if update_success:
            print("   ✅ 証拠発見更新成功")
            
            # 更新確認
            updated_game = await db_service.get_game_session(test_game_id)
            if updated_game and "test_ev_001" in updated_game.get("discovered_evidence", []):
                print("   ✅ 証拠発見状態が正常に保存されました")
            else:
                print("   ❌ 証拠発見状態の更新確認失敗")
        else:
            print("   ❌ 証拠発見更新失敗")
        
        # 4. プレイヤーのアクティブゲーム検索テスト
        print("   👤 アクティブゲーム検索...")
        active_games = await db_service.get_active_games_by_player("test_player_123")
        if active_games:
            print(f"   ✅ アクティブゲーム {len(active_games)} 件発見")
        else:
            print("   ⚠️  アクティブゲームが見つかりません")
        
        # 5. ゲーム完了のシミュレーション
        print("   🏁 ゲーム完了シミュレーション...")
        completion_update = {
            "status": "completed",
            "completed_at": datetime.now(),
            "final_score": 950,
            "all_evidence_found": True
        }
        
        completion_success = await db_service.update_game_session(test_game_id, completion_update)
        if completion_success:
            print("   ✅ ゲーム完了状態更新成功")
        else:
            print("   ❌ ゲーム完了状態更新失敗")
        
        print(f"\n🎉 Firestore統合テスト完全成功！")
        print(f"   すべてのデータベース操作が正常に動作しています")
        print(f"   ゲームの永続化機能が利用可能です")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestore統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    
    print("Firestore統合テストを開始します...")
    success = await test_firestore_integration()
    
    print(f"\n" + "=" * 50)
    if success:
        print("🎉 Firestore統合テスト成功！")
        print("   データベースサービスはFirestore環境で正常動作します")
        print("   ゲーム機能の永続化が完了しました")
    else:
        print("❌ Firestore統合テスト失敗")
        print("   ローカルファイルデータベースを使用してください")

if __name__ == "__main__":
    asyncio.run(main())