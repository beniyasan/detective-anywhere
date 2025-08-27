"""
共通エラーハンドリングユーティリティ
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException


class APIError:
    """API共通エラークラス"""
    
    @staticmethod
    def bad_request(
        code: str = "INVALID_REQUEST",
        message: str = "不正なリクエストです",
        details: Optional[str] = None
    ) -> HTTPException:
        """400 Bad Request エラーを生成"""
        detail = {
            "error": {
                "code": code,
                "message": message
            }
        }
        if details:
            detail["error"]["details"] = details
        return HTTPException(status_code=400, detail=detail)
    
    @staticmethod
    def unauthorized(
        code: str = "UNAUTHORIZED",
        message: str = "認証が必要です"
    ) -> HTTPException:
        """401 Unauthorized エラーを生成"""
        return HTTPException(status_code=401, detail={
            "error": {
                "code": code,
                "message": message
            }
        })
    
    @staticmethod
    def forbidden(
        code: str = "FORBIDDEN",
        message: str = "アクセスが拒否されました"
    ) -> HTTPException:
        """403 Forbidden エラーを生成"""
        return HTTPException(status_code=403, detail={
            "error": {
                "code": code,
                "message": message
            }
        })
    
    @staticmethod
    def not_found(
        code: str = "NOT_FOUND",
        message: str = "リソースが見つかりません",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> HTTPException:
        """404 Not Found エラーを生成"""
        detail: Dict[str, Any] = {
            "error": {
                "code": code,
                "message": message
            }
        }
        if resource_type:
            detail["error"]["resource_type"] = resource_type
        if resource_id:
            detail["error"]["resource_id"] = resource_id
        return HTTPException(status_code=404, detail=detail)
    
    @staticmethod
    def internal_server_error(
        code: str = "INTERNAL_ERROR",
        message: str = "サーバーエラーが発生しました",
        details: Optional[str] = None
    ) -> HTTPException:
        """500 Internal Server Error エラーを生成"""
        detail = {
            "error": {
                "code": code,
                "message": message
            }
        }
        if details:
            detail["error"]["details"] = details
        return HTTPException(status_code=500, detail=detail)
    
    @staticmethod
    def bad_gateway(
        code: str = "BAD_GATEWAY",
        message: str = "外部サービスへの接続に失敗しました",
        service: Optional[str] = None
    ) -> HTTPException:
        """502 Bad Gateway エラーを生成"""
        detail = {
            "error": {
                "code": code,
                "message": message
            }
        }
        if service:
            detail["error"]["service"] = service
        return HTTPException(status_code=502, detail=detail)


class GameAPIError(APIError):
    """ゲーム関連API専用エラークラス"""
    
    @staticmethod
    def game_not_found(game_id: str) -> HTTPException:
        """ゲームが見つからないエラー"""
        return APIError.not_found(
            code="GAME_NOT_FOUND",
            message="ゲームセッションが見つかりません",
            resource_type="game",
            resource_id=game_id
        )
    
    @staticmethod
    def game_already_completed(game_id: str) -> HTTPException:
        """ゲーム終了済みエラー"""
        return APIError.forbidden(
            code="GAME_ALREADY_COMPLETED",
            message="このゲームは既に終了しています"
        )
    
    @staticmethod
    def scenario_generation_failed(details: Optional[str] = None) -> HTTPException:
        """シナリオ生成失敗エラー"""
        return APIError.internal_server_error(
            code="SCENARIO_GENERATION_FAILED",
            message="シナリオ生成に失敗しました",
            details=details
        )


class EvidenceAPIError(APIError):
    """証拠関連API専用エラークラス"""
    
    @staticmethod
    def evidence_not_found(evidence_id: str) -> HTTPException:
        """証拠が見つからないエラー"""
        return APIError.not_found(
            code="EVIDENCE_NOT_FOUND",
            message="指定された証拠が見つかりません",
            resource_type="evidence",
            resource_id=evidence_id
        )
    
    @staticmethod
    def evidence_already_discovered(evidence_id: str) -> HTTPException:
        """証拠発見済みエラー"""
        return APIError.forbidden(
            code="EVIDENCE_ALREADY_DISCOVERED",
            message="この証拠は既に発見済みです"
        )
    
    @staticmethod
    def evidence_too_far(distance: float, required_radius: float) -> HTTPException:
        """証拠が遠すぎるエラー"""
        return APIError.forbidden(
            code="EVIDENCE_TOO_FAR",
            message=f"証拠から{distance:.1f}m離れています。{required_radius}m以内に近づいてください"
        )


class POIAPIError(APIError):
    """POI関連API専用エラークラス"""
    
    @staticmethod
    def invalid_location() -> HTTPException:
        """無効な位置情報エラー"""
        return APIError.bad_request(
            code="INVALID_LOCATION",
            message="無効な位置情報です"
        )
    
    @staticmethod
    def poi_search_failed(service: str = "Google Maps API") -> HTTPException:
        """POI検索失敗エラー"""
        return APIError.bad_gateway(
            code="POI_SEARCH_FAILED",
            message="POI検索に失敗しました",
            service=service
        )