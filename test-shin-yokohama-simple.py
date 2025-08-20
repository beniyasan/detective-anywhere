#!/usr/bin/env python3
"""
新横浜駅周辺での簡易Geminiテスト
"""

import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

async def test_shin_yokohama_gemini():
    """新横浜駅でのGemini APIテスト"""
    print("🚄 新横浜駅ミステリーシナリオ生成テスト")
    print("=" * 50)
    
    # API設定
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY が設定されていません")
        return False
    
    print(f"🔑 APIキー取得成功: {api_key[:10]}...")
    
    try:
        # Gemini設定
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # 新横浜駅用プロンプト
        prompt = """
あなたは優秀な推理小説作家です。新横浜駅周辺を舞台にしたミステリーシナリオを作成してください。

## 条件設定
- 場所: 新横浜駅周辺の商業・オフィス地区
- 難易度: 普通
- 容疑者数: 4名
- 複雑さ: 適度
- 新幹線駅として多くの人が行き交う場所の特徴を活かす

## 出力形式（必ずJSON形式で出力）
{
  "title": "事件のタイトル",
  "description": "導入文（300字程度、ドラマチック）",
  "victim": {
    "name": "被害者名",
    "age": 年齢,
    "occupation": "職業",
    "personality": "性格・特徴",
    "background": "背景情報"
  },
  "suspects": [
    {
      "name": "容疑者名",
      "age": 年齢,
      "occupation": "職業",
      "personality": "性格・特徴",
      "relationship": "被害者との関係",
      "alibi": "アリバイ",
      "motive": "動機"
    }
  ],
  "culprit": "真犯人の名前",
  "motive": "真の犯行動機",
  "method": "犯行手口",
  "timeline": [
    "時系列1",
    "時系列2",
    "時系列3"
  ]
}

新横浜駅の特徴（新幹線、商業施設、オフィスビル）を活かしたリアルなシナリオを生成してください。
"""
        
        print("⏳ AIでシナリオ生成中...")
        response = model.generate_content(prompt)
        
        if response.text:
            print("✅ シナリオ生成成功！")
            print("\n" + "=" * 50)
            print("📚 生成されたミステリーシナリオ")
            print("=" * 50)
            
            # JSONをパースして表示
            import json
            try:
                scenario_data = json.loads(response.text)
                
                print(f"🎬 タイトル: {scenario_data['title']}")
                print(f"\n📖 あらすじ:")
                print(f"{scenario_data['description']}")
                
                print(f"\n💀 被害者: {scenario_data['victim']['name']} ({scenario_data['victim']['age']}歳)")
                print(f"   職業: {scenario_data['victim']['occupation']}")
                print(f"   性格: {scenario_data['victim']['personality']}")
                
                print(f"\n🔍 容疑者一覧 ({len(scenario_data['suspects'])}名):")
                for i, suspect in enumerate(scenario_data['suspects'], 1):
                    marker = "👑" if suspect['name'] == scenario_data['culprit'] else "👤"
                    print(f"   {marker} {i}. {suspect['name']} ({suspect['age']}歳) - {suspect['occupation']}")
                    print(f"      性格: {suspect['personality']}")
                    print(f"      関係: {suspect['relationship']}")
                    print(f"      アリバイ: {suspect['alibi']}")
                    print(f"      動機: {suspect['motive']}")
                
                print(f"\n🎯 真犯人: {scenario_data['culprit']}")
                print(f"💡 犯行動機: {scenario_data['motive']}")
                print(f"🔧 犯行手口: {scenario_data['method']}")
                
                print(f"\n⏰ 事件の流れ:")
                for i, timeline in enumerate(scenario_data['timeline'], 1):
                    print(f"   {i}. {timeline}")
                
                print("\n" + "=" * 50)
                print("🎉 新横浜駅ミステリーシナリオ生成テスト完了!")
                print("🚄 新幹線駅の特徴を活かしたシナリオが正常に生成されました")
                
                return True
                
            except json.JSONDecodeError:
                print("⚠️  JSON形式でないレスポンスですが、内容を表示します:")
                print(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
                return True
        else:
            print("❌ レスポンスが空です")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

async def main():
    success = await test_shin_yokohama_gemini()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)