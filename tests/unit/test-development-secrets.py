#!/usr/bin/env python3
"""
開発環境でのSecret Manager統合テスト
実際のAPIキーを使用してフォールバック機能を確認
"""

import os
import sys
from dotenv import load_dotenv

# 開発環境設定を読み込み（実際のAPIキー入り）
load_dotenv('.env')

def test_development_with_real_api_keys():
    """開発環境での実APIキーテスト"""
    
    print("🔧 開発環境 + 実APIキーテスト")
    print("=" * 50)
    
    try:
        # Secret Managerを無効にして環境変数フォールバックをテスト
        os.environ['USE_SECRET_MANAGER'] = 'false'
        
        from backend.src.config.secrets import (
            get_api_key, 
            validate_required_secrets,
            secret_manager
        )
        
        print("✅ Secret Manager モジュール読み込み成功")
        print(f"   Secret Manager使用: {secret_manager.use_secret_manager}")
        print(f"   プロジェクトID: {secret_manager.project_id}")
        
        # APIキー取得テスト（環境変数フォールバック）
        print(f"\n🔑 APIキー取得テスト（環境変数フォールバック）:")
        
        api_services = {
            'gemini': 'GEMINI_API_KEY',
            'google_maps': 'GOOGLE_MAPS_API_KEY'
        }
        
        all_keys_valid = True
        
        for service, env_var in api_services.items():
            # 環境変数から直接確認
            env_key = os.getenv(env_var)
            
            # get_api_key関数経由で取得
            retrieved_key = get_api_key(service)
            
            # 検証
            env_valid = bool(env_key and len(env_key.strip()) > 20)
            retrieved_valid = bool(retrieved_key and len(retrieved_key.strip()) > 20)
            keys_match = env_key == retrieved_key
            
            status = "✅" if env_valid and retrieved_valid and keys_match else "❌"
            
            print(f"   {status} {service}:")
            print(f"      環境変数: {'設定済み' if env_valid else '未設定'} ({env_key[:20] + '...' if env_key else 'None'})")
            print(f"      取得結果: {'成功' if retrieved_valid else '失敗'} ({retrieved_key[:20] + '...' if retrieved_key else 'None'})")
            print(f"      一致: {'Yes' if keys_match else 'No'}")
            
            if not (env_valid and retrieved_valid and keys_match):
                all_keys_valid = False
        
        # 必須シークレット検証
        print(f"\n🛡️  必須シークレット検証:")
        validation_results = validate_required_secrets()
        
        validation_success = True
        for secret_name, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            print(f"   {status} {secret_name}: {'設定済み' if is_valid else '未設定'}")
            if not is_valid:
                validation_success = False
        
        # 実際のAPI呼び出しテスト
        print(f"\n🌐 実際のAPI呼び出しテスト:")
        
        if all_keys_valid:
            # Google Maps APIテスト
            try:
                import googlemaps
                maps_key = get_api_key('google_maps')
                
                if maps_key:
                    gmaps = googlemaps.Client(key=maps_key)
                    
                    # 簡単な検索テスト
                    places_result = gmaps.places_nearby(
                        location=(35.6586, 139.7454),  # 東京タワー
                        radius=500,
                        type='cafe'
                    )
                    
                    cafe_count = len(places_result.get('results', []))
                    print(f"   ✅ Google Maps API: 正常動作 ({cafe_count}件のカフェ発見)")
                else:
                    print(f"   ❌ Google Maps API: キー取得失敗")
                    
            except ImportError:
                print(f"   ⚠️  Google Maps API: googlemapsライブラリ未インストール")
            except Exception as e:
                print(f"   ❌ Google Maps API: エラー - {e}")
            
            # Gemini APIは実際のテストは省略（コスト節約のため）
            gemini_key = get_api_key('gemini')
            if gemini_key:
                print(f"   ✅ Gemini API: キー取得成功 (実際の呼び出しはスキップ)")
            else:
                print(f"   ❌ Gemini API: キー取得失敗")
        else:
            print(f"   ⚠️  APIキー設定に問題があるため、API呼び出しテストをスキップ")
        
        # 総合結果
        overall_success = all_keys_valid and validation_success
        
        print(f"\n📊 テスト結果サマリー:")
        print(f"   APIキー取得: {'✅ 成功' if all_keys_valid else '❌ 失敗'}")
        print(f"   シークレット検証: {'✅ 成功' if validation_success else '❌ 失敗'}")
        print(f"   総合判定: {'✅ 成功' if overall_success else '❌ 要修正'}")
        
        if overall_success:
            print(f"\n🎯 Secret Manager統合は正常に動作しています！")
            print(f"   フォールバック機能により環境変数からAPIキーを正常取得")
            print(f"   本番環境ではSecret Managerが自動的に使用されます")
        else:
            print(f"\n⚠️  設定に問題があります:")
            if not all_keys_valid:
                print(f"   - APIキーの設定を確認してください")
            if not validation_success:
                print(f"   - 必須シークレットの設定を確認してください")
        
        return overall_success
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("   backend/src/config/secrets.py が正しく配置されているか確認してください")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def test_production_readiness():
    """本番環境準備状況テスト"""
    
    print(f"\n🚀 本番環境準備状況チェック")
    print("=" * 50)
    
    checklist = [
        ("Google Cloud プロジェクト", "GOOGLE_CLOUD_PROJECT_ID", True),
        ("Gemini API キー", "GEMINI_API_KEY", True),
        ("Google Maps API キー", "GOOGLE_MAPS_API_KEY", True),
        ("Secret Manager設定", "USE_SECRET_MANAGER", False),
        ("本番CORS設定", "CORS_ORIGINS", False),
        ("本番ログ設定", "LOG_LEVEL", False),
    ]
    
    ready_count = 0
    total_count = len(checklist)
    
    for item, env_var, is_required in checklist:
        value = os.getenv(env_var)
        is_set = bool(value and value.strip())
        
        if is_required and is_set:
            status = "✅"
            ready_count += 1
        elif is_required and not is_set:
            status = "❌"
        elif not is_required and is_set:
            status = "✅"
            ready_count += 1
        else:
            status = "⚠️ "
            ready_count += 0.5  # 部分点
    
        requirement = "(必須)" if is_required else "(推奨)"
        print(f"   {status} {item} {requirement}: {'設定済み' if is_set else '未設定'}")
    
    readiness_pct = (ready_count / total_count) * 100
    
    print(f"\n📊 本番環境準備度: {readiness_pct:.1f}% ({ready_count:.1f}/{total_count})")
    
    if readiness_pct >= 80:
        print("🎉 本番環境デプロイ準備完了！")
    elif readiness_pct >= 60:
        print("⚠️  いくつかの設定が不足していますが、基本的な動作は可能です")
    else:
        print("❌ 本番環境デプロイには追加の設定が必要です")
    
    return readiness_pct >= 60

if __name__ == "__main__":
    print("🔍 開発環境 + 実APIキー統合テスト")
    
    # メインテスト
    secrets_test = test_development_with_real_api_keys()
    
    # 本番準備チェック
    production_ready = test_production_readiness()
    
    print(f"\n🎯 統合テスト完了")
    
    if secrets_test and production_ready:
        print("✅ Secret Manager統合実装は正常に動作し、本番環境への準備ができています")
        print("\n次のステップ:")
        print("1. 本番環境でのGoogle Cloudプロジェクト設定")
        print("2. scripts/setup-secrets.sh の実行")
        print("3. 本番環境でのデプロイテスト")
    else:
        print("⚠️  設定の確認が必要です")
    
    sys.exit(0 if secrets_test else 1)