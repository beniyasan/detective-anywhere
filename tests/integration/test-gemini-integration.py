#!/usr/bin/env python3
"""
Gemini API統合テストスクリプト
Issue #3の実装テスト用
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# パスを設定してバックエンドモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__)))

from backend.src.services.ai_service import ai_service
from backend.src.config.secrets import get_api_key, validate_required_secrets

async def test_secret_manager():
    """Secret Manager統合テスト"""
    print("🔐 Secret Manager統合テスト開始")
    
    # 必須シークレットの検証
    validation_results = validate_required_secrets()
    
    for secret_name, is_valid in validation_results.items():
        status = "✅" if is_valid else "❌"
        print(f"   {status} {secret_name}: {'設定済み' if is_valid else '未設定'}")
    
    # Gemini APIキー個別チェック
    gemini_key = get_api_key('gemini')
    if gemini_key:
        print(f"✅ Gemini APIキー取得成功: {gemini_key[:10]}...")
    else:
        print("❌ Gemini APIキー取得失敗")
        return False
    
    return all(validation_results.values())

async def test_ai_service_initialization():
    """AIサービス初期化テスト"""
    print("\n🤖 AIサービス初期化テスト開始")
    
    try:
        await ai_service.initialize()
        print("✅ AIサービス初期化成功")
        return True
    except Exception as e:
        print(f"❌ AIサービス初期化失敗: {e}")
        return False

async def test_scenario_generation():
    """シナリオ生成テスト"""
    print("\n📚 シナリオ生成テスト開始")
    
    try:
        # テスト用のシナリオ生成リクエスト
        test_location = Location(lat=35.6762, lng=139.6503)  # 東京駅周辺
        
        request = ScenarioGenerationRequest(
            difficulty="easy",
            location_context="東京駅周辺のオフィス街",
            poi_types=["restaurant", "cafe", "store", "park"],
            suspect_count_range=(3, 4)
        )
        
        print(f"   リクエスト: 難易度={request.difficulty}, 場所={request.location_context}")
        print("   シナリオ生成中...")
        
        start_time = datetime.now()
        scenario = await ai_service.generate_mystery_scenario(request)
        end_time = datetime.now()
        
        generation_time = (end_time - start_time).total_seconds()
        
        print(f"✅ シナリオ生成成功 (所要時間: {generation_time:.2f}秒)")
        print(f"   タイトル: {scenario.title}")
        print(f"   容疑者数: {len(scenario.suspects)}名")
        print(f"   真犯人: {scenario.culprit}")
        print(f"   動機: {scenario.motive}")
        
        # 容疑者情報表示
        print("   容疑者一覧:")
        for i, suspect in enumerate(scenario.suspects, 1):
            print(f"     {i}. {suspect.name} ({suspect.age}歳) - {suspect.occupation}")
        
        return True
        
    except Exception as e:
        print(f"❌ シナリオ生成失敗: {e}")
        return False

async def test_evidence_generation():
    """証拠生成テスト"""
    print("\n🔍 証拠生成テスト開始")
    
    try:
        # 簡単なテスト用シナリオを作成
        from shared.models.scenario import Scenario
        from shared.models.character import Character, Temperament
        
        # テスト用の簡単なシナリオ
        victim = Character(
            name="田中太郎",
            age=45,
            occupation="会社員",
            personality="真面目で几帳面",
            temperament=Temperament.CALM,
            relationship="被害者"
        )
        
        suspects = [
            Character(
                name="佐藤花子",
                age=35,
                occupation="同僚",
                personality="野心的",
                temperament=Temperament.DEFENSIVE,
                relationship="同僚",
                alibi="会議中だった"
            )
        ]
        
        test_scenario = Scenario(
            title="オフィスでの事件",
            description="オフィスで起きた謎の事件",
            victim=victim,
            suspects=suspects,
            culprit="佐藤花子",
            motive="昇進への嫉妬",
            method="トリックを使った犯行",
            timeline=["午前9時", "午前10時", "午前11時"]
        )
        
        # テスト用POIリスト
        test_pois = [
            {"name": "東京駅", "type": "station", "lat": 35.6762, "lng": 139.6503},
            {"name": "皇居東御苑", "type": "park", "lat": 35.6851, "lng": 139.7544},
            {"name": "丸の内カフェ", "type": "cafe", "lat": 35.6795, "lng": 139.7638}
        ]
        
        print("   証拠生成中...")
        start_time = datetime.now()
        evidence_list = await ai_service.generate_evidence(
            test_scenario, test_pois, 3
        )
        end_time = datetime.now()
        
        generation_time = (end_time - start_time).total_seconds()
        
        print(f"✅ 証拠生成成功 (所要時間: {generation_time:.2f}秒)")
        print(f"   証拠数: {len(evidence_list)}個")
        
        for i, evidence in enumerate(evidence_list, 1):
            print(f"   {i}. {evidence.name} ({evidence.importance.value})")
            print(f"      場所: {evidence.poi_name}")
            print(f"      説明: {evidence.description[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 証拠生成失敗: {e}")
        return False

async def main():
    """メインテスト実行"""
    print("🧪 Gemini API統合テスト開始")
    print("=" * 50)
    
    tests = [
        ("Secret Manager", test_secret_manager),
        ("AIサービス初期化", test_ai_service_initialization),
        ("シナリオ生成", test_scenario_generation),
        ("証拠生成", test_evidence_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テストで予期しないエラー: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            success_count += 1
    
    print(f"\n成功: {success_count}/{len(results)} テスト")
    
    if success_count == len(results):
        print("🎉 全テスト成功！Gemini API統合は正常に動作しています。")
        return 0
    else:
        print("⚠️  一部テストが失敗しました。設定を確認してください。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)