#!/usr/bin/env python3
"""
Firestore基本接続テスト
"""

import os
import sys
from datetime import datetime

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# Firestore設定を環境変数で設定
os.environ['GOOGLE_CLOUD_PROJECT'] = 'detective-anywhere-local'

print("🚀 Firestore基本接続テスト")
print("=" * 50)

try:
    # 基本インポートテスト
    from google.cloud import firestore
    print("✅ google-cloud-firestoreのインポート成功")
    
    # プロジェクト情報
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'detective-anywhere-local')
    print(f"📍 プロジェクトID: {project_id}")
    
    # Firestoreクライアント作成テスト
    try:
        # 実際のFirestoreサービスへの接続を試行
        client = firestore.Client(project=project_id)
        print("✅ Firestoreクライアント作成成功")
        
        # 簡単な書き込みテスト
        test_doc_ref = client.collection('test').document('connection_test')
        test_data = {
            'message': 'Hello Firestore!',
            'timestamp': datetime.now(),
            'test_type': 'connection'
        }
        
        # 書き込み実行
        test_doc_ref.set(test_data)
        print("✅ テストデータ書き込み成功")
        
        # 読み取りテスト
        doc = test_doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"✅ テストデータ読み取り成功: {data['message']}")
        else:
            print("❌ テストデータが見つかりません")
        
        # クリーンアップ
        test_doc_ref.delete()
        print("✅ テストデータクリーンアップ完了")
        
        print("\n🎉 Firestore基本接続テスト完了！")
        print("📊 結果: Firestoreサービスは正常に動作しています")
        
    except Exception as firestore_error:
        print(f"❌ Firestore接続エラー: {firestore_error}")
        print("\n💡 解決方法:")
        print("1. Google Cloud認証を確認:")
        print("   gcloud auth application-default login")
        print("2. プロジェクトを設定:")
        print("   gcloud config set project detective-anywhere-local")
        print("3. Firestore APIを有効化:")
        print("   gcloud services enable firestore.googleapis.com")
        
except ImportError as import_error:
    print(f"❌ インポートエラー: {import_error}")
    print("\n💡 解決方法:")
    print("pip install google-cloud-firestore")

except Exception as general_error:
    print(f"❌ 一般エラー: {general_error}")
    
print("\n" + "=" * 50)
print("📋 Firestore設定確認:")
print(f"   GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT', '未設定')}")
print(f"   FIRESTORE_EMULATOR_HOST: {os.environ.get('FIRESTORE_EMULATOR_HOST', '未設定')}")

# 認証状態確認
try:
    import subprocess
    result = subprocess.run(['gcloud', 'auth', 'list', '--format=value(account)'], 
                           capture_output=True, text=True, timeout=5)
    if result.stdout.strip():
        print(f"   Google Cloud認証: {result.stdout.strip()}")
    else:
        print("   Google Cloud認証: 未認証")
except:
    print("   Google Cloud認証: 確認できませんでした")