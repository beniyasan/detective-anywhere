#!/usr/bin/env python3
"""
本番環境設定テストスクリプト
Secret Managerとの統合動作確認
"""

import os
import sys
from dotenv import load_dotenv

# 本番環境設定を読み込み
load_dotenv('.env.production')

def test_production_config():
    """本番環境設定テスト"""
    
    print("🔧 本番環境設定テスト")
    print("=" * 50)
    
    # 環境変数確認
    required_env_vars = [
        'ENV',
        'GOOGLE_CLOUD_PROJECT_ID',
        'USE_SECRET_MANAGER',
        'USE_MOCK_DATA'
    ]
    
    print("📋 環境変数確認:")
    for var in required_env_vars:
        value = os.getenv(var, 'NOT_SET')
        status = "✅" if value != 'NOT_SET' else "❌"
        print(f"   {status} {var}: {value}")
    
    # Secret Manager 統合テスト
    print(f"\n🔐 Secret Manager統合テスト:")
    
    try:
        from backend.src.config.secrets import (
            secret_manager, 
            get_api_key, 
            validate_required_secrets,
            get_database_config
        )
        
        print("✅ Secret Manager モジュール読み込み成功")
        
        # Secret Manager 初期化確認
        use_sm = os.getenv('USE_SECRET_MANAGER', 'false').lower() == 'true'
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        
        print(f"   Secret Manager使用: {use_sm}")
        print(f"   プロジェクトID: {project_id}")
        
        if use_sm and not project_id:
            print("⚠️  SECRET_MANAGER使用が有効ですが、プロジェクトIDが未設定")
            return False
        
        # API キー取得テスト
        print(f"\n🔑 APIキー取得テスト:")
        api_keys = ['gemini', 'google_maps']
        
        for service in api_keys:
            try:
                key = get_api_key(service)
                status = "✅" if key else "❌"
                key_preview = f"{key[:10]}..." if key else "未設定"
                print(f"   {status} {service}: {key_preview}")
            except Exception as e:
                print(f"   ❌ {service}: エラー - {e}")
        
        # 必須シークレット検証
        print(f"\n🛡️  必須シークレット検証:")
        validation_results = validate_required_secrets()
        
        all_valid = True
        for secret_name, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            print(f"   {status} {secret_name}: {'設定済み' if is_valid else '未設定'}")
            if not is_valid:
                all_valid = False
        
        # データベース設定確認
        print(f"\n💾 データベース設定:")
        db_config = get_database_config()
        
        for key, value in db_config.items():
            print(f"   📊 {key}: {value}")
        
        print(f"\n📊 テスト結果:")
        print(f"   全体ステータス: {'✅ 成功' if all_valid else '⚠️  設定不備があります'}")
        
        if not all_valid:
            print(f"\n🔧 推奨アクション:")
            print(f"   1. Google Cloud プロジェクトの設定確認")
            print(f"   2. 必要なAPIキーの取得と設定")
            print(f"   3. scripts/setup-secrets.sh の実行")
            print(f"   4. docs/GOOGLE_CLOUD_SETUP.md の確認")
        
        return all_valid
        
    except ImportError as e:
        print(f"❌ モジュール読み込みエラー: {e}")
        print("   必要な依存関係がインストールされているか確認してください")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def test_mock_vs_production():
    """モック環境と本番環境の比較"""
    
    print(f"\n🔄 環境設定比較:")
    print("=" * 50)
    
    # 開発環境設定読み込み
    load_dotenv('.env', override=True)
    dev_env = os.getenv('ENV', 'development')
    dev_mock = os.getenv('USE_MOCK_DATA', 'true')
    
    # 本番環境設定読み込み
    load_dotenv('.env.production', override=True) 
    prod_env = os.getenv('ENV', 'production')
    prod_mock = os.getenv('USE_MOCK_DATA', 'false')
    
    comparison_data = [
        ('環境', dev_env, prod_env),
        ('モックデータ使用', dev_mock, prod_mock),
        ('Secret Manager', 'false', 'true'),
        ('CORS Origins', '*', 'https://detective-anywhere.app,...'),
        ('Debug', 'true', 'false'),
        ('Log Level', 'DEBUG', 'INFO')
    ]
    
    print(f"{'項目':<20} {'開発環境':<15} {'本番環境':<20}")
    print("-" * 60)
    
    for item, dev_val, prod_val in comparison_data:
        print(f"{item:<20} {dev_val:<15} {prod_val:<20}")
    
    print(f"\n💡 本番環境への移行チェックリスト:")
    checklist = [
        "✓ Google Cloud プロジェクト作成",
        "✓ 必要なAPIの有効化", 
        "✓ APIキーの取得と設定",
        "✓ Secret Manager設定",
        "✓ サービスアカウント作成",
        "✓ CORS設定の更新",
        "✓ ログ設定の適用"
    ]
    
    for item in checklist:
        print(f"   {item}")

if __name__ == "__main__":
    print("🚀 本番環境設定テスト開始")
    
    # 本番設定テスト
    success = test_production_config()
    
    # 環境比較
    test_mock_vs_production()
    
    print(f"\n🎯 テスト完了")
    
    if success:
        print("✅ 本番環境設定は正常です")
    else:
        print("⚠️  本番環境設定に問題があります。上記の推奨アクションを実行してください。")
    
    sys.exit(0 if success else 1)