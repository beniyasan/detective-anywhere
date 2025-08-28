#!/bin/bash

# Detective Anywhere本番デプロイスクリプト
# Project ID確認済み版

echo "=========================================="
echo "  Detective Anywhere - Production Deploy"
echo "  Project: detective-anywhere-app"
echo "=========================================="

# プロジェクトIDを設定
export GOOGLE_CLOUD_PROJECT_ID=detective-anywhere-app

# デプロイスクリプトを実行
./deploy_production.sh