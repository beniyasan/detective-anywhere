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
from .config.secrets import validate_required_secrets, get_database_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # スタートアップ
    print("🚀 AIミステリー散歩 API サーバーを起動中...")
    
    # 本番環境でのシークレット検証
    env = os.getenv('ENV', 'development')
    if env == 'production':
        print("🔐 本番環境: APIキーの検証中...")
        secrets_validation = validate_required_secrets()
        
        for secret_name, is_valid in secrets_validation.items():
            status = "✅" if is_valid else "❌"
            print(f"   {status} {secret_name}: {'設定済み' if is_valid else '未設定'}")
        
        if not all(secrets_validation.values()):
            print("❌ 必須APIキーが不足しています。docs/GOOGLE_CLOUD_SETUP.md を参照してください。")
            raise RuntimeError("必須APIキーが設定されていません")
        
        print("✅ 本番環境APIキー検証完了")
    
    # データベース設定取得
    db_config = get_database_config()
    print(f"📊 データベース設定: {db_config['project_id']} (エミュレーター: {db_config['use_emulator']})")
    
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
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
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
    env = os.getenv('ENV', 'development')
    
    # 本番環境での詳細ヘルスチェック
    services_status = {
        "api": "running",
        "environment": env
    }
    
    if env == 'production':
        # 本番環境でのAPIキー検証
        secrets_validation = validate_required_secrets()
        services_status.update({
            "gemini_api": "available" if secrets_validation.get('GEMINI_API_KEY', False) else "unavailable",
            "google_maps_api": "available" if secrets_validation.get('GOOGLE_MAPS_API_KEY', False) else "unavailable",
            "firestore": "connected",
            "secret_manager": "enabled"
        })
    else:
        services_status.update({
            "firestore": "mocked" if os.getenv('USE_FIRESTORE_EMULATOR', 'false') == 'false' else "emulator",
            "gemini": "mocked" if os.getenv('USE_MOCK_DATA', 'true') == 'true' else "connected"
        })
    
    return {
        "status": "healthy",
        "services": services_status
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