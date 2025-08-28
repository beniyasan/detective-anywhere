"""
Google Cloud Secret Manager統合
本番環境でのAPIキー管理
"""

import os
import logging
from typing import Optional, Dict, Any
from google.cloud import secretmanager
from google.api_core import exceptions

logger = logging.getLogger(__name__)

class SecretManager:
    """Google Cloud Secret Manager クライアント"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.use_secret_manager = os.getenv('USE_SECRET_MANAGER', 'false').lower() == 'true'
        self.client = None
        self._cache = {}
        
        logger.info(f"Secret Manager設定: USE_SECRET_MANAGER={self.use_secret_manager}, PROJECT_ID={self.project_id}")
        
        if self.use_secret_manager and self.project_id:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info(f"Secret Manager初期化完了: project={self.project_id}")
            except Exception as e:
                logger.error(f"Secret Manager初期化失敗: {e}")
                logger.error("フォールバックモードで環境変数を使用します")
                self.client = None
        elif not self.use_secret_manager:
            logger.info("Secret Manager無効 - 環境変数モードで動作")
        elif not self.project_id:
            logger.error("GOOGLE_CLOUD_PROJECT_IDが設定されていません")
    
    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """シークレット値取得"""
        
        # キャッシュから取得
        cache_key = f"{secret_name}:{version}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Secret Manager未使用の場合は環境変数から取得
        if not self.use_secret_manager or not self.client:
            env_value = os.getenv(secret_name)
            if env_value:
                self._cache[cache_key] = env_value
                logger.debug(f"環境変数からシークレット取得成功: {secret_name}")
            else:
                logger.warning(f"環境変数が見つかりません: {secret_name} (USE_SECRET_MANAGER={self.use_secret_manager}, client={self.client is not None})")
            return env_value
        
        try:
            # Secret Managerからシークレット取得
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self.client.access_secret_version(request={"name": secret_path})
            secret_value = response.payload.data.decode("UTF-8")
            
            # キャッシュに保存
            self._cache[cache_key] = secret_value
            logger.debug(f"シークレット取得成功: {secret_name}")
            
            return secret_value
            
        except exceptions.NotFound:
            logger.warning(f"Secret Managerでシークレットが見つかりません: {secret_name}")
            # フォールバック: 環境変数から取得
            fallback_value = os.getenv(secret_name)
            if fallback_value:
                logger.info(f"フォールバックで環境変数から取得成功: {secret_name}")
                self._cache[cache_key] = fallback_value
            return fallback_value
            
        except Exception as e:
            logger.error(f"Secret Manager取得エラー: {secret_name}, {e}")
            # フォールバック: 環境変数から取得
            fallback_value = os.getenv(secret_name)
            if fallback_value:
                logger.info(f"エラー後フォールバックで環境変数から取得: {secret_name}")
                self._cache[cache_key] = fallback_value
            return fallback_value
    
    def create_secret(self, secret_name: str, secret_value: str) -> bool:
        """新しいシークレット作成"""
        if not self.use_secret_manager or not self.client:
            logger.warning("Secret Manager未使用のため、シークレット作成をスキップ")
            return False
        
        try:
            # シークレット作成
            secret_path = f"projects/{self.project_id}"
            secret = {"replication": {"automatic": {}}}
            
            response = self.client.create_secret(
                request={
                    "parent": secret_path,
                    "secret_id": secret_name,
                    "secret": secret
                }
            )
            
            # シークレット値を追加
            self.client.add_secret_version(
                request={
                    "parent": response.name,
                    "payload": {"data": secret_value.encode("UTF-8")}
                }
            )
            
            logger.info(f"シークレット作成成功: {secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"シークレット作成エラー: {secret_name}, {e}")
            return False

# グローバルインスタンス
secret_manager = SecretManager()

# 便利関数
def get_api_key(service_name: str) -> Optional[str]:
    """APIキー取得の便利関数"""
    secret_name_map = {
        'gemini': 'GEMINI_API_KEY',
        'google_maps': 'GOOGLE_MAPS_API_KEY',
        'jwt': 'JWT_SECRET_KEY',
        'redis': 'REDIS_URL'
    }
    
    secret_name = secret_name_map.get(service_name)
    if not secret_name:
        logger.error(f"不明なサービス名: {service_name}")
        return None
    
    logger.debug(f"APIキー取得開始: service={service_name}, secret_name={secret_name}")
    result = secret_manager.get_secret(secret_name)
    
    if result:
        logger.info(f"APIキー取得成功: {service_name} (長さ: {len(result)})")
    else:
        logger.error(f"APIキー取得失敗: {service_name} - {secret_name}が見つかりません")
    
    return result

def get_database_config() -> Dict[str, Any]:
    """データベース設定取得"""
    return {
        'project_id': os.getenv('GOOGLE_CLOUD_PROJECT_ID'),
        'collection_prefix': os.getenv('FIRESTORE_COLLECTION_PREFIX', 'mystery_walk_prod'),
        'use_emulator': os.getenv('USE_FIRESTORE_EMULATOR', 'false').lower() == 'true'
    }

def validate_required_secrets() -> Dict[str, bool]:
    """必須シークレットの検証"""
    required_secrets = [
        'GEMINI_API_KEY',
        'GOOGLE_MAPS_API_KEY'
    ]
    
    validation_results = {}
    
    for secret_name in required_secrets:
        secret_value = secret_manager.get_secret(secret_name)
        validation_results[secret_name] = bool(secret_value and len(secret_value.strip()) > 0)
    
    return validation_results