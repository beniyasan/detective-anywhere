"""
AIミステリー散歩 - メインアプリケーション
"""

from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# ローカル環境用の設定読み込み
load_dotenv()

from .api.routes import game, evidence, deduction, poi, route
from .core.database import initialize_firestore
from .core.logging import setup_logging, get_logger, LogCategory
from .services.ai_service import AIService
from .config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # スタートアップ
    # ログ設定の初期化
    setup_logging()
    logger = get_logger(__name__, LogCategory.SYSTEM)
    
    # 統一設定管理を使用
    settings = get_settings()
    
    # 遅延初期化が有効かチェック
    if settings.api.lazy_init_enabled:
        logger.info("Starting AI Mystery Walk API server (Lazy Initialization Mode)")
        
        # 設定情報をログ出力
        logger.info(
            "Application startup",
            environment=settings.environment.value,
            database_project=settings.database.project_id,
            use_emulator=settings.database.use_emulator,
            structured_logging=settings.logging.enable_structured_logging,
            lazy_init_enabled=True
        )
        
        # LazyServiceManagerのインスタンスを作成（サービスはまだ初期化しない）
        from .services.lazy_service_manager import lazy_service_manager
        logger.info("LazyServiceManager initialized (services will be loaded on demand)")
        
        # バックグラウンドでクリティカルサービスのウォームアップを開始（非ブロッキング）
        async def warmup_services():
            """バックグラウンドでサービスをウォームアップ"""
            try:
                await asyncio.sleep(5)  # ヘルスチェック通過を待つ
                logger.info("Starting background service warmup...")
                await lazy_service_manager.warmup_critical_services()
                logger.info("Background service warmup completed")
            except Exception as e:
                logger.warning(f"Background warmup failed: {e}")
        
        # ウォームアップタスクを非ブロッキングで開始
        import asyncio
        asyncio.create_task(warmup_services())
        
        print("✅ 初期化完了（遅延初期化モード）")
    
    else:
        # 従来の初期化方式（開発環境など）
        logger.info("Starting AI Mystery Walk API server (Traditional Initialization Mode)")
        
        logger.info(
            "Application startup",
            environment=settings.environment.value,
            database_project=settings.database.project_id,
            use_emulator=settings.database.use_emulator,
            structured_logging=settings.logging.enable_structured_logging,
            lazy_init_enabled=False
        )
        
        # Firestoreの初期化
        try:
            await initialize_firestore()
            logger.info("Firestore initialized successfully")
        except Exception as e:
            logger.warning(f"Firestore initialization failed, using local database: {e}")
        
        # AI、POI、ルートサービスの初期化
        from .services.ai_service import ai_service
        from .services.poi_service import poi_service
        from .services.route_generation_service import route_generation_service
        
        await ai_service.initialize()
        await route_generation_service.initialize()
        
        print("✅ 初期化完了（従来モード）")
    
    if settings.is_production:
        logger.info("Production environment configuration validated")
    elif settings.is_development:
        logger.info("Running in development environment")
    
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

# Firebase Hostingからのアクセスのみ許可するミドルウェア
@app.middleware("http")
async def firebase_only_middleware(request: Request, call_next):
    """Firebase Hostingからのアクセスのみ許可"""
    
    # ヘルスチェックとルートエンドポイントは除外
    if request.url.path in ["/", "/health", "/warmup"]:
        response = await call_next(request)
        return response
    
    # 許可されたOriginをチェック
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    
    allowed_domains = [
        "detective-anywhere-hosting.web.app",
        "detective-anywhere-hosting.firebaseapp.com",
        "localhost",
        "127.0.0.1"
    ]
    
    is_allowed = False
    if origin:
        for domain in allowed_domains:
            if domain in origin:
                is_allowed = True
                break
    elif referer:
        for domain in allowed_domains:
            if domain in referer:
                is_allowed = True
                break
    
    if not is_allowed:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "ACCESS_FORBIDDEN",
                    "message": "Firebase Hosting経由でのみアクセス可能です",
                    "redirect": "https://detective-anywhere-hosting.web.app"
                }
            }
        )
    
    response = await call_next(request)
    return response

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

app.include_router(
    route.router,
    prefix="/api/v1/route",
    tags=["route"]
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
    """ヘルスチェック（軽量化版）"""
    settings = get_settings()
    
    # LazyServiceManagerから状態を取得
    from .services.lazy_service_manager import lazy_service_manager
    service_status = lazy_service_manager.get_service_status()
    
    # 基本的な応答のみ返す（実際のサービス接続チェックは行わない）
    return {
        "status": "healthy",
        "environment": settings.environment.value,
        "services": service_status,
        "startup_mode": "lazy_initialization",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/warmup")
async def warmup_services():
    """サービスのウォームアップ（事前初期化）"""
    from .services.lazy_service_manager import lazy_service_manager
    
    try:
        # バックグラウンドでクリティカルサービスをウォームアップ
        await lazy_service_manager.warmup_critical_services()
        
        service_status = lazy_service_manager.get_service_status()
        return {
            "status": "warmup_completed",
            "services": service_status,
            "message": "Critical services warmed up successfully"
        }
    except Exception as e:
        logger.error(f"Warmup failed: {e}")
        return {
            "status": "warmup_partial", 
            "services": lazy_service_manager.get_service_status(),
            "message": f"Warmup partially failed: {str(e)}"
        }


# 静的ファイルマウント
app.mount("/static", StaticFiles(directory="static"), name="static")

# 静的ファイルの提供
@app.get("/web-demo.html")
async def serve_web_demo():
    """Web Demo HTMLファイル提供"""
    return FileResponse("/app/web-demo.html")

@app.get("/mobile-app.html")
async def serve_mobile_app():
    """Mobile App HTMLファイル提供"""
    return FileResponse("/app/mobile-app.html")

@app.get("/manifest.json")
async def serve_manifest():
    """PWA Manifestファイル提供"""
    return FileResponse("/app/manifest.json")

@app.get("/service-worker.js")
async def serve_service_worker():
    """Service Workerファイル提供"""
    return FileResponse("/app/service-worker.js")


# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "リソースが見つかりません",
                "details": str(exc)
            }
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR", 
                "message": "内部サーバーエラーが発生しました",
                "details": str(exc)
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # 開発用サーバー起動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )