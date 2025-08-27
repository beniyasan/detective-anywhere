#!/usr/bin/env python3
"""
簡易APIキーテスト
Gemini APIキーとGoogle Maps APIキーが正常に動作するかチェック
"""

import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
import googlemaps

# 環境変数読み込み
load_dotenv()

def test_gemini_api():
    """Gemini API単体テスト"""
    print("🤖 Gemini APIテスト開始")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY環境変数が設定されていません")
        return False
    
    print(f"   APIキー取得: {api_key[:10]}...")
    
    try:
        # Gemini設定
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # 簡単なテスト
        response = model.generate_content("Hello, please respond with 'API working' in Japanese.")
        
        if response.text:
            print(f"✅ Gemini API応答成功: {response.text[:50]}...")
            return True
        else:
            print("❌ Gemini APIから応答なし")
            return False
            
    except Exception as e:
        print(f"❌ Gemini APIエラー: {e}")
        return False

def test_google_maps_api():
    """Google Maps API単体テスト"""
    print("\n🗺️  Google Maps APIテスト開始")
    
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY環境変数が設定されていません")
        return False
    
    print(f"   APIキー取得: {api_key[:10]}...")
    
    try:
        # Google Maps クライアント作成
        gmaps = googlemaps.Client(key=api_key)
        
        # 簡単なテスト（東京駅周辺の場所検索）
        places_result = gmaps.places_nearby(
            location=(35.6762, 139.6503),  # 東京駅
            radius=1000,
            type='restaurant'
        )
        
        if places_result.get('results'):
            results_count = len(places_result['results'])
            print(f"✅ Google Maps API応答成功: {results_count}件の結果")
            
            # 最初の結果を表示
            if results_count > 0:
                first_place = places_result['results'][0]
                print(f"   サンプル結果: {first_place.get('name', 'N/A')}")
            
            return True
        else:
            print("❌ Google Maps APIから結果なし")
            return False
            
    except Exception as e:
        print(f"❌ Google Maps APIエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🔑 APIキー単体テスト開始")
    print("=" * 40)
    
    results = []
    
    # Gemini APIテスト
    gemini_result = test_gemini_api()
    results.append(("Gemini API", gemini_result))
    
    # Google Maps APIテスト
    maps_result = test_google_maps_api()
    results.append(("Google Maps API", maps_result))
    
    print("\n" + "=" * 40)
    print("📊 テスト結果")
    print("=" * 40)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            success_count += 1
    
    print(f"\n成功: {success_count}/{len(results)} API")
    
    if success_count == len(results):
        print("🎉 全APIが正常に動作しています！")
        return 0
    else:
        print("⚠️  一部のAPIが正常に動作していません。APIキーを確認してください。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)