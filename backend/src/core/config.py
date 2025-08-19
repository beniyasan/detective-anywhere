"""
アプリケーション設定
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # アプリケーション基本設定
    app_name: str = "AIミステリー散歩"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Google Cloud設定
    project_id: str = Field(..., env="GOOGLE_CLOUD_PROJECT_ID")
    location: str = Field(default="asia-northeast1", env="GOOGLE_CLOUD_LOCATION")
    
    # Gemini AI設定
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-pro", env="GEMINI_MODEL")
    
    # Google Maps設定
    google_maps_api_key: str = Field(..., env="GOOGLE_MAPS_API_KEY")
    
    # Firestore設定
    firestore_collection_prefix: str = Field(default="mystery_walk", env="FIRESTORE_COLLECTION_PREFIX")
    
    # Redis設定（キャッシュ用）
    redis_url: Optional[str] = Field(None, env="REDIS_URL")
    
    # ゲーム設定
    default_evidence_discovery_radius: float = 50.0  # メートル
    max_game_duration: int = 3600  # 秒（1時間）
    max_concurrent_games_per_player: int = 3
    
    # AIシナリオ生成設定
    max_scenario_generation_retries: int = 3
    scenario_generation_timeout: float = 30.0  # 秒
    
    # セキュリティ設定
    api_key_header: str = "X-API-Key"
    cors_origins: list = ["*"]
    
    # ログ設定
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# グローバル設定インスタンス
settings = Settings()


def get_settings() -> Settings:
    """設定を取得"""
    return settings


# 環境別の設定検証
def validate_production_settings():
    """本番環境用設定の検証"""
    required_vars = [
        "GOOGLE_CLOUD_PROJECT_ID",
        "GEMINI_API_KEY", 
        "GOOGLE_MAPS_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}")


def get_firestore_collection_name(collection_type: str) -> str:
    """Firestoreのコレクション名を取得"""
    return f"{settings.firestore_collection_prefix}_{collection_type}"


# 各コレクション名の定数
GAME_SESSIONS_COLLECTION = get_firestore_collection_name("game_sessions")
PLAYERS_COLLECTION = get_firestore_collection_name("players")
GAME_HISTORY_COLLECTION = get_firestore_collection_name("game_history")