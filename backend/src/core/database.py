"""
データベース接続とユーティリティ
"""

from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.cloud.firestore import AsyncClient
import asyncio
from datetime import datetime

from .config import settings, GAME_SESSIONS_COLLECTION, PLAYERS_COLLECTION, GAME_HISTORY_COLLECTION


class FirestoreClient:
    """Firestore非同期クライアント"""
    
    def __init__(self):
        self._client: Optional[AsyncClient] = None
    
    async def initialize(self):
        """クライアント初期化"""
        if not self._client:
            self._client = firestore.AsyncClient(project=settings.project_id)
    
    @property
    def client(self) -> AsyncClient:
        """クライアントインスタンスを取得"""
        if not self._client:
            raise RuntimeError("Firestoreクライアントが初期化されていません")
        return self._client
    
    async def close(self):
        """接続を閉じる"""
        if self._client:
            await self._client.close()
            self._client = None


# グローバルクライアントインスタンス
firestore_client = FirestoreClient()


async def initialize_firestore():
    """Firestoreの初期化"""
    await firestore_client.initialize()


async def get_firestore_client() -> AsyncClient:
    """Firestoreクライアントを取得"""
    return firestore_client.client


class BaseRepository:
    """基底リポジトリクラス"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    async def get_collection(self):
        """コレクションを取得"""
        client = await get_firestore_client()
        return client.collection(self.collection_name)
    
    async def create(self, document_id: str, data: Dict[str, Any]) -> str:
        """ドキュメントを作成"""
        collection = await self.get_collection()
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        
        await collection.document(document_id).set(data)
        return document_id
    
    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """ドキュメントを取得"""
        collection = await self.get_collection()
        doc = await collection.document(document_id).get()
        
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
    
    async def update(self, document_id: str, data: Dict[str, Any]) -> bool:
        """ドキュメントを更新"""
        collection = await self.get_collection()
        data["updated_at"] = datetime.now()
        
        try:
            await collection.document(document_id).update(data)
            return True
        except Exception:
            return False
    
    async def delete(self, document_id: str) -> bool:
        """ドキュメントを削除"""
        collection = await self.get_collection()
        
        try:
            await collection.document(document_id).delete()
            return True
        except Exception:
            return False
    
    async def list_by_field(
        self, 
        field: str, 
        value: Any, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """フィールドで検索"""
        collection = await self.get_collection()
        query = collection.where(field, "==", value).limit(limit)
        
        docs = await query.get()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        
        return results
    
    async def count_by_field(self, field: str, value: Any) -> int:
        """フィールド条件でカウント"""
        collection = await self.get_collection()
        query = collection.where(field, "==", value)
        
        docs = await query.get()
        return len(docs)


class GameSessionRepository(BaseRepository):
    """ゲームセッションリポジトリ"""
    
    def __init__(self):
        super().__init__(GAME_SESSIONS_COLLECTION)
    
    async def get_active_games_by_player(self, player_id: str) -> List[Dict[str, Any]]:
        """プレイヤーのアクティブなゲームを取得"""
        collection = await self.get_collection()
        query = collection.where("player_id", "==", player_id).where("status", "==", "active")
        
        docs = await query.get()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        
        return results
    
    async def get_games_by_location(
        self, 
        lat_min: float, 
        lat_max: float, 
        lng_min: float, 
        lng_max: float
    ) -> List[Dict[str, Any]]:
        """位置範囲でゲームを検索"""
        # Firestoreの地理クエリ制限のため、アプリケーション側でフィルタリング
        collection = await self.get_collection()
        docs = await collection.limit(1000).get()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            location = data.get("player_location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            
            if (lat is not None and lng is not None and
                lat_min <= lat <= lat_max and lng_min <= lng <= lng_max):
                data["id"] = doc.id
                results.append(data)
        
        return results


class PlayerRepository(BaseRepository):
    """プレイヤーリポジトリ"""
    
    def __init__(self):
        super().__init__(PLAYERS_COLLECTION)
    
    async def create_or_update_player(self, player_id: str, player_data: Dict[str, Any]) -> str:
        """プレイヤーを作成または更新"""
        existing = await self.get(player_id)
        
        if existing:
            await self.update(player_id, player_data)
        else:
            await self.create(player_id, player_data)
        
        return player_id


class GameHistoryRepository(BaseRepository):
    """ゲーム履歴リポジトリ"""
    
    def __init__(self):
        super().__init__(GAME_HISTORY_COLLECTION)
    
    async def get_player_history(
        self, 
        player_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """プレイヤーの履歴を取得"""
        collection = await self.get_collection()
        query = (collection
                .where("player_id", "==", player_id)
                .order_by("completed_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .offset(offset))
        
        docs = await query.get()
        results = []
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        
        return results


# リポジトリインスタンス
game_session_repo = GameSessionRepository()
player_repo = PlayerRepository()
game_history_repo = GameHistoryRepository()


async def health_check() -> Dict[str, str]:
    """データベース接続のヘルスチェック"""
    try:
        client = await get_firestore_client()
        # 簡単な読み取りテスト
        collection = client.collection("_health_check")
        await collection.limit(1).get()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}