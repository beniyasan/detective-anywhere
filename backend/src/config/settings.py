"""
統一設定管理
"""

import os
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field


class Environment(str, Enum):
    """環境種別"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class DatabaseConfig:
    """データベース設定"""
    project_id: Optional[str] = None
    collection_prefix: str = "mystery_walk"
    use_emulator: bool = False
    emulator_host: Optional[str] = None
    use_firestore: bool = True
    local_db_path: str = "local_db"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """環境変数からデータベース設定を作成"""
        return cls(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
            collection_prefix=os.getenv('FIRESTORE_COLLECTION_PREFIX', 'mystery_walk_prod'),
            use_emulator=os.getenv('USE_FIRESTORE_EMULATOR', 'false').lower() == 'true',
            emulator_host=os.getenv('FIRESTORE_EMULATOR_HOST'),
            use_firestore=os.getenv('USE_FIRESTORE', 'false').lower() == 'true',
            local_db_path=os.getenv('LOCAL_DB_PATH', 'local_db')
        )


@dataclass
class APIConfig:
    """外部API設定"""
    google_maps_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    google_cloud_project_id: Optional[str] = None
    lazy_init_enabled: bool = True  # 遅延初期化を有効化
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """環境変数からAPI設定を作成"""
        return cls(
            google_maps_api_key=os.getenv('GOOGLE_MAPS_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            google_cloud_project_id=os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
            lazy_init_enabled=os.getenv('LAZY_INIT_ENABLED', 'true').lower() == 'true'
        )


@dataclass
class SecurityConfig:
    """セキュリティ設定"""
    use_secret_manager: bool = False
    allowed_origins: List[str] = field(default_factory=lambda: ['*'])
    api_key_required: bool = False
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        """環境変数からセキュリティ設定を作成"""
        cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
        return cls(
            use_secret_manager=os.getenv('USE_SECRET_MANAGER', 'false').lower() == 'true',
            allowed_origins=[origin.strip() for origin in cors_origins],
            api_key_required=os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true'
        )


@dataclass
class GameConfig:
    """ゲーム設定"""
    max_concurrent_games: int = 3
    default_discovery_radius: float = 50.0
    evidence_generation_timeout: int = 30
    ai_model_name: str = "gemini-2.0-flash-exp"
    
    @classmethod
    def from_env(cls) -> 'GameConfig':
        """環境変数からゲーム設定を作成"""
        return cls(
            max_concurrent_games=int(os.getenv('MAX_CONCURRENT_GAMES', '3')),
            default_discovery_radius=float(os.getenv('DEFAULT_DISCOVERY_RADIUS', '50.0')),
            evidence_generation_timeout=int(os.getenv('EVIDENCE_GENERATION_TIMEOUT', '30')),
            ai_model_name=os.getenv('AI_MODEL_NAME', 'gemini-2.0-flash-exp')
        )


@dataclass
class LoggingConfig:
    """ログ設定"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_structured_logging: bool = False
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """環境変数からログ設定を作成"""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            enable_structured_logging=os.getenv('STRUCTURED_LOGGING', 'false').lower() == 'true'
        )


class Settings:
    """統一設定管理クラス"""
    
    def __init__(self):
        self._environment = Environment(os.getenv('ENV', 'development'))
        self._database = DatabaseConfig.from_env()
        self._api = APIConfig.from_env()
        self._security = SecurityConfig.from_env()
        self._game = GameConfig.from_env()
        self._logging = LoggingConfig.from_env()
        
        # 設定検証
        self._validate_configuration()
        
        # 初期化完了はメインアプリでログ出力
    
    @property
    def environment(self) -> Environment:
        """環境種別"""
        return self._environment
    
    @property
    def database(self) -> DatabaseConfig:
        """データベース設定"""
        return self._database
    
    @property
    def api(self) -> APIConfig:
        """API設定"""
        return self._api
    
    @property
    def security(self) -> SecurityConfig:
        """セキュリティ設定"""
        return self._security
    
    @property
    def game(self) -> GameConfig:
        """ゲーム設定"""
        return self._game
    
    @property
    def logging(self) -> LoggingConfig:
        """ログ設定"""
        return self._logging
    
    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self._environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self._environment == Environment.PRODUCTION
    
    @property
    def is_test(self) -> bool:
        """テスト環境かどうか"""
        return self._environment == Environment.TEST
    
    def get_collection_name(self, base_name: str) -> str:
        """コレクション名を取得（プレフィックス付き）"""
        return f"{self._database.collection_prefix}_{base_name}"
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """シークレット取得（Secret Manager または環境変数）"""
        if self._security.use_secret_manager:
            from .secrets import secret_manager
            return secret_manager.get_secret(secret_name) or default
        return os.getenv(secret_name, default)
    
    def _validate_configuration(self):
        """設定の検証"""
        errors = []
        
        # 本番環境での必須チェック
        if self.is_production:
            if not self._api.google_maps_api_key:
                errors.append("Google Maps API key is required in production")
            
            if not self._api.gemini_api_key:
                errors.append("Gemini API key is required in production")
            
            if self._database.use_firestore and not self._database.project_id:
                errors.append("Google Cloud Project ID is required for Firestore in production")
        
        # 開発環境での警告
        if self.is_development:
            if not self._api.google_maps_api_key:
                print("WARNING: Google Maps API key not set - some features may not work")
            
            if not self._api.gemini_api_key:
                print("WARNING: Gemini API key not set - AI features may not work")
        
        if errors:
            error_msg = "Configuration validation failed: " + "; ".join(errors)
            print(f"ERROR: {error_msg}")
            raise ValueError(error_msg)
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得（デバッグ用）"""
        return {
            "environment": self._environment.value,
            "database": {
                "project_id": self._database.project_id,
                "collection_prefix": self._database.collection_prefix,
                "use_emulator": self._database.use_emulator,
                "use_firestore": self._database.use_firestore,
            },
            "api": {
                "has_google_maps_key": bool(self._api.google_maps_api_key),
                "has_gemini_key": bool(self._api.gemini_api_key),
                "project_id": self._api.google_cloud_project_id,
            },
            "security": {
                "use_secret_manager": self._security.use_secret_manager,
                "allowed_origins": self._security.allowed_origins,
                "api_key_required": self._security.api_key_required,
            },
            "game": {
                "max_concurrent_games": self._game.max_concurrent_games,
                "default_discovery_radius": self._game.default_discovery_radius,
                "ai_model_name": self._game.ai_model_name,
            },
            "logging": {
                "level": self._logging.level,
                "structured": self._logging.enable_structured_logging,
            }
        }


# グローバル設定インスタンス
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """設定インスタンスを取得"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings():
    """設定をリセット（テスト用）"""
    global _settings_instance
    _settings_instance = None


# よく使用される設定のショートカット
def get_database_config() -> DatabaseConfig:
    """データベース設定取得"""
    return get_settings().database


def get_api_config() -> APIConfig:
    """API設定取得"""
    return get_settings().api


def is_production() -> bool:
    """本番環境判定"""
    return get_settings().is_production


def is_development() -> bool:
    """開発環境判定"""
    return get_settings().is_development