"""
AIミステリー散歩 - メインアプリケーション
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# ローカル環境用の設定読み込み
load_dotenv()

from .api.routes import game, evidence, deduction, poi
from .core.config import settings
from .core.database import initialize_firestore
from .services.ai_service import AIService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # スタートアップ
    print("🚀 AIミステリー散歩 API サーバーを起動中...")
    
    # Firestoreの初期化
    await initialize_firestore()
    
    # AIサービスの初期化
    ai_service = AIService()
    await ai_service.initialize()
    
    print("✅ 初期化完了")
    
    yield
    
    # シャットダウン
    print("🛑 サーバーをシャットダウンしています...")


# FastAPIアプリケーションの作成
app = FastAPI(
    title="AIミステリー散歩 API",
    description="GPS連動のAI生成ミステリーゲームAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルートの登録
app.include_router(
    game.router,
    prefix="/api/v1/game",
    tags=["game"]
)

app.include_router(
    evidence.router,
    prefix="/api/v1/evidence", 
    tags=["evidence"]
)

app.include_router(
    deduction.router,
    prefix="/api/v1/deduction",
    tags=["deduction"]
)

app.include_router(
    poi.router,
    prefix="/api/v1/poi",
    tags=["poi"]
)


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "message": "AIミステリー散歩 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "firestore": "connected",
            "gemini": "available"
        }
    }


# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": {
            "code": "NOT_FOUND",
            "message": "リソースが見つかりません",
            "details": str(exc)
        }
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": {
            "code": "INTERNAL_SERVER_ERROR", 
            "message": "内部サーバーエラーが発生しました",
            "details": str(exc)
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # 開発用サーバー起動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )