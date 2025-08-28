"""
遅延初期化サービスマネージャー
Cloud Run起動時間を最適化するため、各サービスを必要時に初期化する
"""
import asyncio
from typing import Optional, Dict, Any
from enum import Enum
import time

from ..core.logging import get_logger, LogCategory
from ..config.settings import get_settings
from ..config.secrets import get_api_key

logger = get_logger(__name__, LogCategory.SYSTEM)


class ServiceStatus(Enum):
    """サービスの初期化状態"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"


class LazyServiceManager:
    """
    シングルトンパターンで実装された遅延初期化サービスマネージャー
    各サービスは初回アクセス時に初期化される
    """
    
    _instance: Optional['LazyServiceManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls) -> 'LazyServiceManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # サービスインスタンス
        self._ai_service: Optional[Any] = None
        self._poi_service: Optional[Any] = None
        self._route_service: Optional[Any] = None
        self._enhanced_poi_service: Optional[Any] = None
        self._firestore_db: Optional[Any] = None
        
        # サービスの初期化状態
        self._service_status: Dict[str, ServiceStatus] = {
            "ai_service": ServiceStatus.NOT_INITIALIZED,
            "poi_service": ServiceStatus.NOT_INITIALIZED,
            "route_service": ServiceStatus.NOT_INITIALIZED,
            "enhanced_poi_service": ServiceStatus.NOT_INITIALIZED,
            "firestore": ServiceStatus.NOT_INITIALIZED
        }
        
        # 初期化時刻の記録
        self._initialization_times: Dict[str, float] = {}
        
        # 初期化用のロック（サービスごと）
        self._service_locks: Dict[str, asyncio.Lock] = {
            "ai_service": asyncio.Lock(),
            "poi_service": asyncio.Lock(),
            "route_service": asyncio.Lock(),
            "enhanced_poi_service": asyncio.Lock(),
            "firestore": asyncio.Lock()
        }
        
        logger.info("LazyServiceManager initialized (services not yet loaded)")
    
    async def get_ai_service(self):
        """AI Service (Gemini) を取得（必要時に初期化）"""
        if self._service_status["ai_service"] == ServiceStatus.READY:
            return self._ai_service
        
        async with self._service_locks["ai_service"]:
            # ロック取得後に再確認（二重初期化防止）
            if self._service_status["ai_service"] == ServiceStatus.READY:
                return self._ai_service
            
            if self._service_status["ai_service"] == ServiceStatus.ERROR:
                raise RuntimeError("AI Service initialization previously failed")
            
            try:
                self._service_status["ai_service"] = ServiceStatus.INITIALIZING
                start_time = time.time()
                logger.info("Initializing AI Service...")
                
                from .ai_service import ai_service
                await ai_service.initialize()
                
                self._ai_service = ai_service
                self._service_status["ai_service"] = ServiceStatus.READY
                self._initialization_times["ai_service"] = time.time() - start_time
                
                logger.info(f"AI Service initialized successfully (took {self._initialization_times['ai_service']:.2f}s)")
                return self._ai_service
                
            except Exception as e:
                self._service_status["ai_service"] = ServiceStatus.ERROR
                logger.error(f"Failed to initialize AI Service: {e}")
                raise
    
    async def get_poi_service(self):
        """POI Service を取得（必要時に初期化）"""
        if self._service_status["poi_service"] == ServiceStatus.READY:
            return self._poi_service
        
        async with self._service_locks["poi_service"]:
            if self._service_status["poi_service"] == ServiceStatus.READY:
                return self._poi_service
            
            if self._service_status["poi_service"] == ServiceStatus.ERROR:
                raise RuntimeError("POI Service initialization previously failed")
            
            try:
                self._service_status["poi_service"] = ServiceStatus.INITIALIZING
                start_time = time.time()
                logger.info("Initializing POI Service...")
                
                from .poi_service import poi_service
                
                self._poi_service = poi_service
                self._service_status["poi_service"] = ServiceStatus.READY
                self._initialization_times["poi_service"] = time.time() - start_time
                
                logger.info(f"POI Service initialized successfully (took {self._initialization_times['poi_service']:.2f}s)")
                return self._poi_service
                
            except Exception as e:
                self._service_status["poi_service"] = ServiceStatus.ERROR
                logger.error(f"Failed to initialize POI Service: {e}")
                raise
    
    async def get_route_service(self):
        """Route Generation Service を取得（必要時に初期化）"""
        if self._service_status["route_service"] == ServiceStatus.READY:
            return self._route_service
        
        async with self._service_locks["route_service"]:
            if self._service_status["route_service"] == ServiceStatus.READY:
                return self._route_service
            
            if self._service_status["route_service"] == ServiceStatus.ERROR:
                raise RuntimeError("Route Service initialization previously failed")
            
            try:
                self._service_status["route_service"] = ServiceStatus.INITIALIZING
                start_time = time.time()
                logger.info("Initializing Route Generation Service...")
                
                from .route_generation_service import route_generation_service
                await route_generation_service.initialize()
                
                self._route_service = route_generation_service
                self._service_status["route_service"] = ServiceStatus.READY
                self._initialization_times["route_service"] = time.time() - start_time
                
                logger.info(f"Route Service initialized successfully (took {self._initialization_times['route_service']:.2f}s)")
                return self._route_service
                
            except Exception as e:
                self._service_status["route_service"] = ServiceStatus.ERROR
                logger.error(f"Failed to initialize Route Service: {e}")
                raise

    
    async def get_enhanced_poi_service(self):
        """Enhanced POI Service を取得（必要時に初期化）"""
        if self._service_status["enhanced_poi_service"] == ServiceStatus.READY:
            return self._enhanced_poi_service
        
        async with self._service_locks["enhanced_poi_service"]:
            if self._service_status["enhanced_poi_service"] == ServiceStatus.READY:
                return self._enhanced_poi_service
            
            if self._service_status["enhanced_poi_service"] == ServiceStatus.ERROR:
                raise RuntimeError("Enhanced POI Service initialization previously failed")
            
            try:
                self._service_status["enhanced_poi_service"] = ServiceStatus.INITIALIZING
                start_time = time.time()
                logger.info("Initializing Enhanced POI Service...")
                
                from .enhanced_poi_service import enhanced_poi_service
                await enhanced_poi_service.initialize()
                
                self._enhanced_poi_service = enhanced_poi_service
                self._service_status["enhanced_poi_service"] = ServiceStatus.READY
                self._initialization_times["enhanced_poi_service"] = time.time() - start_time
                
                logger.info(f"Enhanced POI Service initialized successfully (took {self._initialization_times['enhanced_poi_service']:.2f}s)")
                return self._enhanced_poi_service
                
            except Exception as e:
                self._service_status["enhanced_poi_service"] = ServiceStatus.ERROR
                logger.error(f"Failed to initialize Enhanced POI Service: {e}")
                raise
    
    async def get_firestore(self):
        """Firestore を取得（必要時に初期化）"""
        if self._service_status["firestore"] == ServiceStatus.READY:
            return self._firestore_db
        
        async with self._service_locks["firestore"]:
            if self._service_status["firestore"] == ServiceStatus.READY:
                return self._firestore_db
            
            if self._service_status["firestore"] == ServiceStatus.ERROR:
                # Firestoreが失敗した場合はローカルDBにフォールバック
                logger.warning("Firestore unavailable, using local database")
                return None
            
            try:
                self._service_status["firestore"] = ServiceStatus.INITIALIZING
                start_time = time.time()
                logger.info("Initializing Firestore...")
                
                from ..core.database import initialize_firestore
                await initialize_firestore()
                
                # Firestoreのdbインスタンスを取得
                from ..core.database import db
                self._firestore_db = db
                
                self._service_status["firestore"] = ServiceStatus.READY
                self._initialization_times["firestore"] = time.time() - start_time
                
                logger.info(f"Firestore initialized successfully (took {self._initialization_times['firestore']:.2f}s)")
                return self._firestore_db
                
            except Exception as e:
                self._service_status["firestore"] = ServiceStatus.ERROR
                logger.warning(f"Failed to initialize Firestore (will use local DB): {e}")
                return None
    
    def get_service_status(self) -> Dict[str, str]:
        """全サービスの初期化状態を取得"""
        return {
            name: status.value 
            for name, status in self._service_status.items()
        }
    
    def get_initialization_metrics(self) -> Dict[str, Any]:
        """初期化メトリクスを取得"""
        return {
            "status": self.get_service_status(),
            "initialization_times": self._initialization_times,
            "total_initialized": sum(
                1 for status in self._service_status.values() 
                if status == ServiceStatus.READY
            ),
            "total_services": len(self._service_status)
        }
    
    async def warmup_critical_services(self):
        """
        クリティカルなサービスを事前に初期化
        ヘルスチェック通過後、バックグラウンドで実行可能
        """
        try:
            # AI Serviceは最も重要なので優先的に初期化
            await self.get_ai_service()
        except Exception as e:
            logger.warning(f"Failed to warmup AI Service: {e}")
        
        try:
            # POI Serviceも事前に初期化
            await self.get_poi_service()
        except Exception as e:
            logger.warning(f"Failed to warmup POI Service: {e}")
            
        try:
            # Enhanced POI Serviceも事前に初期化（ゲーム開始で必要）
            await self.get_enhanced_poi_service()
        except Exception as e:
            logger.warning(f"Failed to warmup Enhanced POI Service: {e}")
            
        try:
            # Firestoreも事前に初期化を試行（失敗してもローカルDBにフォールバック）
            await self.get_firestore()
        except Exception as e:
            logger.warning(f"Failed to warmup Firestore (will use local DB): {e}")
    
    def reset(self):
        """
        テスト用：全サービスの状態をリセット
        本番環境では使用しない
        """
        settings = get_settings()
        if settings.is_production:
            raise RuntimeError("reset() is not allowed in production")
        
        self._ai_service = None
        self._poi_service = None
        self._route_service = None
        self._enhanced_poi_service = None
        self._firestore_db = None
        
        for key in self._service_status:
            self._service_status[key] = ServiceStatus.NOT_INITIALIZED
        
        self._initialization_times.clear()
        logger.info("LazyServiceManager reset completed")


# グローバルインスタンス
lazy_service_manager = LazyServiceManager()