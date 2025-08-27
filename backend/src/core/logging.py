"""
統一ログ管理システム
"""

import logging
import json
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path

from ..config.settings import get_settings


class LogLevel(str, Enum):
    """ログレベル"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """ログカテゴリ"""
    API = "api"
    DATABASE = "database"
    AI_SERVICE = "ai_service"
    GPS_SERVICE = "gps_service"
    POI_SERVICE = "poi_service"
    GAME_SERVICE = "game_service"
    CONFIG = "config"
    SECURITY = "security"
    SYSTEM = "system"


class StructuredLogger:
    """構造化ロガー"""
    
    def __init__(self, name: str, category: LogCategory = LogCategory.SYSTEM):
        self.name = name
        self.category = category
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """ロガー設定"""
        settings = get_settings()
        
        # ログレベル設定
        level = getattr(logging, settings.logging.level.upper())
        self.logger.setLevel(level)
        
        # ハンドラーが既に追加されている場合はスキップ
        if self.logger.handlers:
            return
        
        # ハンドラー作成
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # フォーマッター設定
        if settings.logging.enable_structured_logging:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(settings.logging.format)
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 重複ログ防止
        self.logger.propagate = False
    
    def _log_structured(
        self, 
        level: LogLevel, 
        message: str, 
        **kwargs
    ):
        """構造化ログ出力"""
        extra = {
            'category': self.category.value,
            'structured_data': kwargs
        }
        
        # ログレベルに応じて出力
        if level == LogLevel.DEBUG:
            self.logger.debug(message, extra=extra)
        elif level == LogLevel.INFO:
            self.logger.info(message, extra=extra)
        elif level == LogLevel.WARNING:
            self.logger.warning(message, extra=extra)
        elif level == LogLevel.ERROR:
            self.logger.error(message, extra=extra)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        self._log_structured(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        self._log_structured(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        self._log_structured(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """エラーログ"""
        if exception:
            kwargs.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        self._log_structured(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """重要エラーログ"""
        if exception:
            kwargs.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        self._log_structured(LogLevel.CRITICAL, message, **kwargs)
    
    # API操作用の専用メソッド
    def api_request(
        self, 
        method: str, 
        path: str, 
        status_code: int = None, 
        duration_ms: float = None,
        **kwargs
    ):
        """APIリクエストログ"""
        self.info(
            f"API {method} {path}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def api_error(
        self, 
        method: str, 
        path: str, 
        status_code: int, 
        error_message: str,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """APIエラーログ"""
        self.error(
            f"API Error {method} {path}: {error_message}",
            method=method,
            path=path,
            status_code=status_code,
            error_message=error_message,
            exception=exception,
            **kwargs
        )
    
    # データベース操作用の専用メソッド
    def db_operation(
        self, 
        operation: str, 
        collection: str = None, 
        document_id: str = None,
        duration_ms: float = None,
        **kwargs
    ):
        """データベース操作ログ"""
        self.info(
            f"Database {operation}",
            operation=operation,
            collection=collection,
            document_id=document_id,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def db_error(
        self, 
        operation: str, 
        error_message: str,
        collection: str = None,
        document_id: str = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """データベースエラーログ"""
        self.error(
            f"Database Error {operation}: {error_message}",
            operation=operation,
            collection=collection,
            document_id=document_id,
            error_message=error_message,
            exception=exception,
            **kwargs
        )
    
    # AI/外部サービス用の専用メソッド
    def external_service(
        self, 
        service_name: str, 
        operation: str,
        duration_ms: float = None,
        **kwargs
    ):
        """外部サービス呼び出しログ"""
        self.info(
            f"External Service {service_name}: {operation}",
            service_name=service_name,
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def external_service_error(
        self, 
        service_name: str, 
        operation: str,
        error_message: str,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """外部サービスエラーログ"""
        self.error(
            f"External Service Error {service_name} {operation}: {error_message}",
            service_name=service_name,
            operation=operation,
            error_message=error_message,
            exception=exception,
            **kwargs
        )


class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードを構造化JSON形式にフォーマット"""
        
        # 基本情報
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # カテゴリ情報
        if hasattr(record, 'category'):
            log_entry["category"] = record.category
        
        # 構造化データ
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # 例外情報
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


# ロガー作成のヘルパー関数
def get_logger(name: str, category: LogCategory = LogCategory.SYSTEM) -> StructuredLogger:
    """構造化ロガーを取得"""
    return StructuredLogger(name, category)


# よく使用されるロガーのショートカット
def get_api_logger(name: str) -> StructuredLogger:
    """APIロガーを取得"""
    return get_logger(name, LogCategory.API)


def get_database_logger(name: str) -> StructuredLogger:
    """データベースロガーを取得"""
    return get_logger(name, LogCategory.DATABASE)


def get_ai_logger(name: str) -> StructuredLogger:
    """AIサービスロガーを取得"""
    return get_logger(name, LogCategory.AI_SERVICE)


def get_game_logger(name: str) -> StructuredLogger:
    """ゲームサービスロガーを取得"""
    return get_logger(name, LogCategory.GAME_SERVICE)


# ログ設定の初期化
def setup_logging():
    """ログ設定の初期化"""
    settings = get_settings()
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.level.upper()))
    
    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 新しいハンドラーを追加
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.logging.level.upper()))
    
    if settings.logging.enable_structured_logging:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(settings.logging.format)
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # サードパーティライブラリのログレベル調整
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # 初期化完了ログ
    logger = get_logger(__name__, LogCategory.SYSTEM)
    logger.info(
        "Logging system initialized",
        structured_logging=settings.logging.enable_structured_logging,
        log_level=settings.logging.level
    )