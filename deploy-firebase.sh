#!/bin/bash
# Firebase Hosting デプロイスクリプト

set -e

echo "🔥 Firebase Hosting - PWAデプロイ開始"

# 1. プロジェクト確認
echo "📋 Firebaseプロジェクト確認"
firebase projects:list

# 2. プロジェクト選択（必要に応じて）
echo "🎯 プロジェクト設定"
firebase use detective-anywhere-hosting

# 3. プレビュー（オプション）
read -p "プレビューを確認しますか？ (y/N): " preview
if [[ $preview =~ ^[Yy]$ ]]; then
    echo "👀 プレビュー開始（別ターミナルでCtrl+Cで終了）"
    firebase serve --only hosting &
    PREVIEW_PID=$!
    echo "プレビューURL: http://localhost:5000"
    read -p "プレビューを確認したらEnterを押してください"
    kill $PREVIEW_PID 2>/dev/null || true
fi

# 4. デプロイ
echo "🚀 Firebase Hosting にデプロイ中..."
firebase deploy --only hosting

# 5. 結果表示
PROJECT_ID=$(firebase projects:list --json | jq -r '.[] | select(.projectId) | .projectId' | head -1)
echo ""
echo "✅ デプロイ完了！"
echo "🌐 PWA URL: https://$PROJECT_ID.web.app"
echo "📱 または: https://$PROJECT_ID.firebaseapp.com"
echo "🔧 API URL: https://detective-anywhere-32kach3lzq-an.a.run.app"