#!/bin/bash
# ローカル開発環境セットアップスクリプト

set -e

# カラー出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🏗️ AIミステリー散歩 - ローカル開発環境セットアップ${NC}"

# 1. 環境変数チェック
echo -e "${YELLOW}📋 環境変数をチェック中...${NC}"

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}⚠️ .env ファイルが見つかりません。.env.example からコピーしています...${NC}"
        cp .env.example .env
        echo -e "${RED}❗ .env ファイルを編集してAPI キーを設定してください${NC}"
    else
        echo -e "${RED}❌ .env.example が見つかりません${NC}"
        exit 1
    fi
fi

# 2. Docker環境の確認
echo -e "${YELLOW}🐳 Docker環境をチェック中...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Dockerがインストールされていません${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Composeがインストールされていません${NC}"
    exit 1
fi

# 3. 開発モード選択
echo -e "${YELLOW}🎯 開発モードを選択してください:${NC}"
echo "1. 完全環境 (Firestore エミュレーター + Redis)"
echo "2. 軽量環境 (モックデータのみ)"
echo "3. ローカル Python 環境"

read -p "選択してください [1-3]: " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 完全環境で起動中...${NC}"
        docker-compose up --build
        ;;
    2)
        echo -e "${GREEN}🚀 軽量環境で起動中...${NC}"
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    3)
        echo -e "${GREEN}🚀 ローカル Python 環境セットアップ中...${NC}"
        
        # Python環境チェック
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}❌ Python 3 がインストールされていません${NC}"
            exit 1
        fi
        
        # 仮想環境作成
        if [ ! -d "venv" ]; then
            echo -e "${YELLOW}📦 仮想環境を作成中...${NC}"
            python3 -m venv venv
        fi
        
        # 仮想環境アクティベート
        source venv/bin/activate
        
        # 依存関係インストール
        echo -e "${YELLOW}📦 依存関係をインストール中...${NC}"
        pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-dev.txt
        
        # 環境変数読み込み
        export $(grep -v '^#' .env | xargs)
        
        # サーバー起動
        echo -e "${GREEN}🚀 FastAPI サーバーを起動中...${NC}"
        cd backend
        uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        echo -e "${RED}❌ 無効な選択です${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ セットアップ完了!${NC}"
echo -e "${GREEN}🌐 API サーバー: http://localhost:8000${NC}"
echo -e "${GREEN}📚 API ドキュメント: http://localhost:8000/docs${NC}"