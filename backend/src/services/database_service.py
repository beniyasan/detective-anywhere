"""
データベースサービス - Firestore統合の改良版
ローカル開発とクラウド環境の両方に対応
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from ..core.logging import get_database_logger

logger = get_database_logger(__name__)

class LocalFileDatabase:
    """ローカルファイルベースのデータベース（開発用）"""
    
    def __init__(self, data_dir: str = "local_db"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # コレクション別ディレクトリを作成
        (self.data_dir / "game_sessions").mkdir(exist_ok=True)
        (self.data_dir / "players").mkdir(exist_ok=True) 
        (self.data_dir / "game_history").mkdir(exist_ok=True)
    
    def _get_file_path(self, collection: str, document_id: str) -> Path:
        return self.data_dir / collection / f"{document_id}.json"
    
    async def save_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> bool:
        """ドキュメントを保存"""
        try:
            file_path = self._get_file_path(collection, document_id)
            
            # datetimeオブジェクトをISOフォーマットに変換
            serializable_data = self._serialize_data(data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            logger.db_operation(
                operation="save_document",
                collection=collection,
                document_id=document_id,
                success=True
            )
            return True
            
        except Exception as e:
            logger.db_error(
                operation="save_document",
                error_message="Document save failed",
                collection=collection,
                document_id=document_id,
                exception=e
            )
            return False
    
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """ドキュメントを取得"""
        try:
            file_path = self._get_file_path(collection, document_id)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # ISO文字列をdatetimeに変換
            return self._deserialize_data(data)
            
        except Exception as e:
            logger.error(f"ドキュメント取得エラー: {e}")
            return None
    
    async def update_document(self, collection: str, document_id: str, update_data: Dict[str, Any]) -> bool:
        """ドキュメントを更新"""
        try:
            existing_data = await self.get_document(collection, document_id)
            if existing_data is None:
                return False
            
            # データをマージ
            existing_data.update(update_data)
            existing_data["updated_at"] = datetime.now()
            
            return await self.save_document(collection, document_id, existing_data)
            
        except Exception as e:
            logger.error(f"ドキュメント更新エラー: {e}")
            return False
    
    async def delete_document(self, collection: str, document_id: str) -> bool:
        """ドキュメントを削除"""
        try:
            file_path = self._get_file_path(collection, document_id)
            
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"ドキュメント削除成功: {collection}/{document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"ドキュメント削除エラー: {e}")
            return False
    
    async def query_documents(
        self, 
        collection: str, 
        field: str = None, 
        value: Any = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """ドキュメントを検索"""
        try:
            collection_dir = self.data_dir / collection
            if not collection_dir.exists():
                return []
            
            results = []
            for json_file in collection_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    data = self._deserialize_data(data)
                    data["id"] = json_file.stem  # ファイル名をIDとして追加
                    
                    # フィルタリング
                    if field and value is not None:
                        if data.get(field) == value:
                            results.append(data)
                    else:
                        results.append(data)
                    
                    if len(results) >= limit:
                        break
                        
                except Exception as file_error:
                    logger.warning(f"ファイル読み取りエラー: {json_file}, {file_error}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"ドキュメント検索エラー: {e}")
            return []
    
    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データのシリアライゼーション（JSON保存用）"""
        serialized = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_data(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_data(item) if isinstance(item, dict) else 
                    item.isoformat() if isinstance(item, datetime) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        
        return serialized
    
    def _deserialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データのデシリアライゼーション（JSON読み込み用）"""
        deserialized = {}
        
        for key, value in data.items():
            if isinstance(value, str) and self._is_iso_datetime(value):
                deserialized[key] = datetime.fromisoformat(value)
            elif isinstance(value, dict):
                deserialized[key] = self._deserialize_data(value)
            elif isinstance(value, list):
                deserialized[key] = [
                    self._deserialize_data(item) if isinstance(item, dict) else
                    datetime.fromisoformat(item) if isinstance(item, str) and self._is_iso_datetime(item) else item
                    for item in value
                ]
            else:
                deserialized[key] = value
        
        return deserialized
    
    def _is_iso_datetime(self, value: str) -> bool:
        """ISO形式のdatetime文字列かチェック"""
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False


class DatabaseService:
    """統合データベースサービス"""
    
    def __init__(self):
        from ..config.settings import get_settings
        settings = get_settings()
        
        self.use_firestore = settings.database.use_firestore
        self.firestore_client = None
        self.local_db = None
        
        if self.use_firestore:
            self._initialize_firestore()
        else:
            self.local_db = LocalFileDatabase()
            logger.info("Using local file database", database_type="local_file")
    
    def _initialize_firestore(self):
        """Firestore初期化"""
        try:
            from google.cloud import firestore
            
            from ..config.settings import get_settings
            settings = get_settings()
            
            project_id = settings.database.project_id or 'detective-anywhere-local'
            
            # エミュレーター設定
            if settings.database.use_emulator and settings.database.emulator_host:
                os.environ['FIRESTORE_EMULATOR_HOST'] = settings.database.emulator_host
                logger.info(f"Firestoreエミュレーターを使用: {settings.database.emulator_host}")
            
            self.firestore_client = firestore.Client(project=project_id)
            logger.info("Firestoreクライアント初期化成功")
            
        except Exception as e:
            logger.warning(f"Firestore初期化失敗、ローカルDBにフォールバック: {e}")
            self.use_firestore = False
            self.local_db = LocalFileDatabase()
    
    async def save_game_session(self, game_id: str, game_data: Dict[str, Any]) -> bool:
        """ゲームセッションを保存"""
        game_data["created_at"] = game_data.get("created_at", datetime.now())
        game_data["updated_at"] = datetime.now()
        
        if self.use_firestore and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection('game_sessions').document(game_id)
                doc_ref.set(game_data)
                logger.info(f"ゲームセッション保存成功 (Firestore): {game_id}")
                return True
            except Exception as e:
                logger.error(f"Firestore保存エラー: {e}")
                return False
        else:
            return await self.local_db.save_document("game_sessions", game_id, game_data)
    
    async def get_game_session(self, game_id: str) -> Optional[Dict[str, Any]]:
        """ゲームセッションを取得"""
        if self.use_firestore and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection('game_sessions').document(game_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    logger.debug(f"ゲームセッション取得成功 (Firestore): {game_id}")
                    return data
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"Firestore取得エラー: {e}")
                return None
        else:
            return await self.local_db.get_document("game_sessions", game_id)
    
    async def update_game_session(self, game_id: str, update_data: Dict[str, Any]) -> bool:
        """ゲームセッションを更新"""
        update_data["updated_at"] = datetime.now()
        
        if self.use_firestore and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection('game_sessions').document(game_id)
                doc_ref.update(update_data)
                logger.info(f"ゲームセッション更新成功 (Firestore): {game_id}")
                return True
            except Exception as e:
                logger.error(f"Firestore更新エラー: {e}")
                return False
        else:
            return await self.local_db.update_document("game_sessions", game_id, update_data)
    
    async def get_active_games_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        """プレイヤーのアクティブゲームを取得"""
        if self.use_firestore and self.firestore_client:
            try:
                query = (self.firestore_client.collection('game_sessions')
                        .where('player_id', '==', player_id)
                        .where('status', '==', 'active'))
                
                docs = query.stream()
                results = []
                for doc in docs:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    results.append(data)
                
                return results
                
            except Exception as e:
                logger.error(f"Firestoreクエリエラー: {e}")
                return []
        else:
            all_games = await self.local_db.query_documents("game_sessions")
            return [
                game for game in all_games 
                if game.get("player_id") == player_id and game.get("status") == "active"
            ]
    
    async def save_player_data(self, player_id: str, player_data: Dict[str, Any]) -> bool:
        """プレイヤーデータを保存"""
        if self.use_firestore and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection('players').document(player_id)
                doc_ref.set(player_data, merge=True)  # 既存データとマージ
                logger.info(f"プレイヤーデータ保存成功 (Firestore): {player_id}")
                return True
            except Exception as e:
                logger.error(f"Firestoreプレイヤー保存エラー: {e}")
                return False
        else:
            return await self.local_db.save_document("players", player_id, player_data)
    
    async def get_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """プレイヤーデータを取得"""
        if self.use_firestore and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection('players').document(player_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    return doc.to_dict()
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"Firestoreプレイヤー取得エラー: {e}")
                return None
        else:
            return await self.local_db.get_document("players", player_id)
    
    async def save_game_history(self, history_id: str, history_data: Dict[str, Any]) -> bool:
        """ゲーム履歴を保存"""
        if self.use_firestore and self.firestore_client:
            try:
                doc_ref = self.firestore_client.collection('game_history').document(history_id)
                doc_ref.set(history_data)
                logger.info(f"ゲーム履歴保存成功 (Firestore): {history_id}")
                return True
            except Exception as e:
                logger.error(f"Firestore履歴保存エラー: {e}")
                return False
        else:
            return await self.local_db.save_document("game_history", history_id, history_data)
    
    async def health_check(self) -> Dict[str, Any]:
        """データベース接続のヘルスチェック"""
        health_info = {
            "database_type": "firestore" if self.use_firestore else "local_file",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if self.use_firestore and self.firestore_client:
                # Firestoreへの簡単な読み取りテスト
                test_collection = self.firestore_client.collection('_health_check')
                list(test_collection.limit(1).stream())
                
                health_info["status"] = "healthy"
                health_info["details"]["firestore_connected"] = True
                
            else:
                # ローカルDBのヘルスチェック
                test_data = {"test": "health_check", "timestamp": datetime.now()}
                save_success = await self.local_db.save_document("_health", "test", test_data)
                
                if save_success:
                    retrieved = await self.local_db.get_document("_health", "test") 
                    await self.local_db.delete_document("_health", "test")
                    
                    health_info["status"] = "healthy" if retrieved else "unhealthy"
                    health_info["details"]["local_db_operational"] = retrieved is not None
                else:
                    health_info["status"] = "unhealthy"
                    
        except Exception as e:
            health_info["status"] = "unhealthy"
            health_info["details"]["error"] = str(e)
        
        return health_info


# グローバルインスタンス
database_service = DatabaseService()