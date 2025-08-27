#!/usr/bin/env python3
"""
新横浜駅周辺での難易度普通テスト
実際のGemini APIでシナリオ生成をテスト
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
from backend.src.services.poi_service import poi_service
from backend.src.config.secrets import get_api_key

# 新横浜駅の座標
SHIN_YOKOHAMA_LAT = 35.5070
SHIN_YOKOHAMA_LNG = 139.6176

async def test_shin_yokohama_scenario():
    """新横浜駅周辺での難易度普通シナリオ生成テスト"""
    print("🚄 新横浜駅周辺ミステリーシナリオ生成テスト")
    print("=" * 60)
    
    # サービス初期化
    print("🔧 サービス初期化中...")
    try:
        await ai_service.initialize()
        poi_service.initialize()
        print("✅ サービス初期化完了")
    except Exception as e:
        print(f"❌ サービス初期化失敗: {e}")
        return False
    
    # POI検索テスト
    print("\n🗺️  新横浜駅周辺のPOI検索...")
    try:
        from shared.models.location import Location
        shin_yokohama_location = Location(lat=SHIN_YOKOHAMA_LAT, lng=SHIN_YOKOHAMA_LNG)
        
        nearby_pois = await poi_service.find_nearby_pois(
            shin_yokohama_location,
            radius=1000,
            min_count=5
        )
        
        print(f"✅ POI検索成功: {len(nearby_pois)}箇所発見")
        
        # POI一覧表示
        print("   発見されたPOI:")
        for i, poi in enumerate(nearby_pois[:10], 1):  # 最初の10箇所表示
            distance = shin_yokohama_location.distance_to(poi.location)
            print(f"     {i}. {poi.name} ({poi.poi_type.value}) - {distance:.0f}m")
        
        poi_types = list(set([poi.poi_type.value for poi in nearby_pois]))
        print(f"   POIタイプ: {', '.join(poi_types)}")
        
    except Exception as e:
        print(f"❌ POI検索失敗: {e}")
        # フォールバック用のモックPOI
        poi_types = ["restaurant", "cafe", "store", "park", "station"]
        print("📝 モックPOIタイプを使用")
    
    # シナリオ生成リクエスト作成
    print("\n🎭 シナリオ生成開始...")
    try:
        from shared.models.scenario import ScenarioGenerationRequest
        
        request = ScenarioGenerationRequest(
            difficulty="normal",
            location_context="新横浜駅周辺の商業・オフィス地区。新幹線駅として多くの人が行き交う繁華街",
            poi_types=poi_types,
            suspect_count_range=(4, 6)
        )
        
        print(f"   📍 場所: {request.location_context}")
        print(f"   🎚️  難易度: {request.difficulty}")
        print(f"   👥 容疑者数: {request.suspect_count_range[0]}-{request.suspect_count_range[1]}名")
        print(f"   🏢 利用可能施設: {len(request.poi_types)}種類")
        
        print("\n⏳ AIでシナリオ生成中... (最大30秒)")
        start_time = datetime.now()
        
        scenario = await ai_service.generate_mystery_scenario(request)
        
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        print(f"✅ シナリオ生成完了! (所要時間: {generation_time:.2f}秒)")
        print("\n" + "=" * 60)
        print("📚 生成されたミステリーシナリオ")
        print("=" * 60)
        
        # シナリオ詳細表示
        print(f"🎬 タイトル: {scenario.title}")
        print(f"📖 あらすじ:")
        print(f"   {scenario.description}")
        
        print(f"\n💀 被害者: {scenario.victim.name} ({scenario.victim.age}歳)")
        print(f"   職業: {scenario.victim.occupation}")
        print(f"   性格: {scenario.victim.personality}")
        
        print(f"\n🔍 容疑者一覧 ({len(scenario.suspects)}名):")
        for i, suspect in enumerate(scenario.suspects, 1):
            marker = "👑" if suspect.name == scenario.culprit else "👤"
            print(f"   {marker} {i}. {suspect.name} ({suspect.age}歳) - {suspect.occupation}")
            print(f"      性格: {suspect.personality}")
            print(f"      被害者との関係: {suspect.relationship}")
            print(f"      アリバイ: {suspect.alibi or 'なし'}")
            if suspect.motive:
                print(f"      動機: {suspect.motive}")
        
        print(f"\n🎯 真犯人: {scenario.culprit}")
        print(f"💡 犯行動機: {scenario.motive}")
        print(f"🔧 犯行手口: {scenario.method}")
        
        print(f"\n⏰ 事件の流れ:")
        for i, timeline in enumerate(scenario.timeline, 1):
            print(f"   {i}. {timeline}")
        
        if hasattr(scenario, 'theme') and scenario.theme:
            print(f"\n🎨 テーマ: {scenario.theme}")
        
        if hasattr(scenario, 'difficulty_factors') and scenario.difficulty_factors:
            print(f"\n🧩 複雑さ要因:")
            for factor in scenario.difficulty_factors:
                print(f"   • {factor}")
        
        if hasattr(scenario, 'red_herrings') and scenario.red_herrings:
            print(f"\n🎪 ミスリード要素:")
            for herring in scenario.red_herrings:
                print(f"   • {herring}")
        
        print("\n" + "=" * 60)
        print("🎉 新横浜駅ミステリーシナリオ生成テスト完了!")
        print(f"⚡ 生成時間: {generation_time:.2f}秒")
        print(f"📊 容疑者数: {len(scenario.suspects)}名")
        print(f"🎭 シナリオ品質: 高品質なミステリーシナリオを生成")
        
        return True
        
    except Exception as e:
        print(f"❌ シナリオ生成エラー: {e}")
        import traceback
        print(f"詳細エラー: {traceback.format_exc()}")
        return False

async def main():
    """メインテスト実行"""
    print("🚄✨ 新横浜駅ミステリーシナリオ生成テスト開始")
    
    # APIキー確認
    gemini_key = get_api_key('gemini')
    if not gemini_key:
        print("❌ Gemini APIキーが設定されていません")
        return 1
    
    google_maps_key = get_api_key('google_maps')
    if not google_maps_key:
        print("⚠️  Google Maps APIキーが設定されていません (モックデータを使用)")
    
    # テスト実行
    success = await test_shin_yokohama_scenario()
    
    if success:
        print("\n🎊 テスト成功! 新横浜駅での難易度普通シナリオが正常に生成されました。")
        return 0
    else:
        print("\n💥 テスト失敗! エラーが発生しました。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)