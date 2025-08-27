"""
AIミステリー散歩 - メインアプリケーション
"""

from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# ローカル環境用の設定読み込み
load_dotenv()

from .api.routes import game, evidence, deduction, poi
from .core.database import initialize_firestore
from .core.logging import setup_logging, get_logger, LogCategory
from .services.ai_service import AIService
from .config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # スタートアップ
    logger.info("Starting AI Mystery Walk API server")
    
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__, LogCategory.SYSTEM)
    
    # 統一設定管理を使用
    settings = get_settings()
    
    # 設定情報をログ出力
    logger.info(
        "Application startup",
        environment=settings.environment.value,
        database_project=settings.database.project_id,
        use_emulator=settings.database.use_emulator,
        structured_logging=settings.logging.enable_structured_logging
    )
    
    if settings.is_production:
        logger.info("Production environment configuration validated")
    elif settings.is_development:
        logger.info("Running in development environment")
    
    # Firestoreの初期化
    await initialize_firestore()
    
    # AIサービスの初期化
    from .services.ai_service import ai_service
    await ai_service.initialize()
    
    # POIサービスの初期化
    from .services.poi_service import poi_service
    poi_service.initialize()
    
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

# 統一設定から CORS 設定を取得
settings = get_settings()
cors_origins = settings.security.allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
async def root() -> Dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {
        "message": "AIミステリー散歩 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """ヘルスチェック"""
    settings = get_settings()
    
    # サービス状態を統一設定から取得
    services_status = {
        "api": "running",
        "environment": settings.environment.value
    }
    
    if settings.is_production:
        # 本番環境でのAPIキー検証
        services_status.update({
            "gemini_api": "available" if settings.api.gemini_api_key else "unavailable",
            "google_maps_api": "available" if settings.api.google_maps_api_key else "unavailable",
            "firestore": "connected",
            "secret_manager": "enabled" if settings.security.use_secret_manager else "disabled"
        })
    else:
        services_status.update({
            "firestore": "emulator" if settings.database.use_emulator else "production",
            "gemini": "available" if settings.api.gemini_api_key else "unavailable",
            "google_maps": "available" if settings.api.google_maps_api_key else "unavailable"
        })
    
    return {
        "status": "healthy",
        "services": services_status,
        "configuration": settings.to_dict() if settings.is_development else None
    }


# 静的ファイルの提供
@app.get("/web-demo.html")
async def serve_web_demo():
    """Web Demo HTMLファイル提供"""
    return FileResponse("/mnt/c/docker/detective-anywhere/web-demo.html")

@app.get("/mobile-app.html")
async def serve_mobile_app():
    """Mobile App HTMLファイル提供"""
    return FileResponse("/mnt/c/docker/detective-anywhere/mobile-app.html")

@app.get("/manifest.json")
async def serve_manifest():
    """PWA Manifestファイル提供"""
    return FileResponse("/mnt/c/docker/detective-anywhere/manifest.json")

@app.get("/service-worker.js")
async def serve_service_worker():
    """Service Workerファイル提供"""
    return FileResponse("/mnt/c/docker/detective-anywhere/service-worker.js")


# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> Dict[str, Any]:
    return {
        "error": {
            "code": "NOT_FOUND",
            "message": "リソースが見つかりません",
            "details": str(exc)
        }
    }


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> Dict[str, Any]:
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