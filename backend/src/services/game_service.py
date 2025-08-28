"""
ゲームサービス - ビジネスロジック
"""

import uuid
import time
import asyncio
import traceback
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .database_service import database_service
from ..core.logging import get_game_logger
from shared.models.game import (
    GameSession, GameStatus, Difficulty, GameScore, 
    DeductionRequest, DeductionResult
)
from shared.models.scenario import Scenario, ScenarioGenerationRequest
from shared.models.evidence import Evidence, EvidenceDiscoveryResult
from shared.models.location import Location
from shared.models.character import CharacterReaction

# LazyServiceManagerを使用して遅延初期化
from .lazy_service_manager import lazy_service_manager
from .gps_service import gps_service, GPSReading, GPSAccuracy


class GameService:
    def __init__(self):
        self.logger = get_game_logger(__name__)
    """ゲームサービス"""
    
    async def start_new_game(
        self,
        player_id: str,
        player_location: Location,
        difficulty: Difficulty,
        radius: int = 1000
    ) -> GameSession:
        """
        新しいゲームセッションを開始
        
        Args:
            player_id: プレイヤーID
            player_location: プレイヤーの現在位置
            difficulty: 難易度
            radius: 証拠検索半径（メートル）、デフォルト1000m
        
        Returns:
            GameSession: 作成されたゲームセッション
        """
        
        # 半径の妥当性チェック
        if radius not in [200, 500, 1000, 2000]:
            raise ValueError("検索半径は200m, 500m, 1000m, 2000mのいずれかを指定してください")
        
        # 位置の有効性チェック
        poi_service = await lazy_service_manager.get_poi_service()
        if not await poi_service.validate_location(player_location):
            raise ValueError("無効な位置情報です")
        
        # 同じプレイヤーのアクティブなゲーム数チェック
        active_games = await database_service.get_active_games_by_player(player_id)
        if len(active_games) >= 3:  # 最大3つまで
            raise ValueError("同時進行可能なゲーム数を超えています")
        
        # 拡張POIサービスを取得（遅延初期化）
        enhanced_poi_service = await lazy_service_manager.get_enhanced_poi_service()
        
        # 証拠配置に最適化されたPOI検索（動的半径を使用）
        evidence_count = self._get_evidence_count(difficulty)
        evidence_pois = await enhanced_poi_service.find_evidence_suitable_pois(
            player_location,
            radius=radius,  # 動的半径を使用
            evidence_count=evidence_count
        )
        
        if len(evidence_pois) < 3:
            raise ValueError(f"半径{radius}m内にゲーム作成に十分なPOI（最低3件）がありません。より大きな半径を選択してください。")
        
        # 地域コンテキスト取得
        location_context = await poi_service.get_location_context(player_location)
        
        # シナリオ生成リクエスト作成
        scenario_request = ScenarioGenerationRequest(
            difficulty=difficulty.value,
            location_context=location_context,
            poi_types=[poi.poi_type.value for poi in evidence_pois],
            suspect_count_range=self._get_suspect_count_range(difficulty)
        )
        
        # AIでシナリオ生成
        ai_service = await lazy_service_manager.get_ai_service()
        scenario = await ai_service.generate_mystery_scenario(scenario_request)
        
        # 証拠生成（選択されたPOIを使用）
        evidence_list = await ai_service.generate_evidence(
            scenario,
            [{"name": poi.name, "type": poi.poi_type.value, 
              "lat": poi.location.lat, "lng": poi.location.lng,
              "poi_id": poi.poi_id, "address": poi.address} for poi in evidence_pois],
            evidence_count
        )
        
        # ゲームセッション作成
        game_id = str(uuid.uuid4())
        game_session = GameSession(
            game_id=game_id,
            player_id=player_id,
            difficulty=difficulty,
            scenario=scenario,
            evidence_list=evidence_list,
            player_location=player_location
        )
        
        # データベースに保存
        await database_service.save_game_session(game_session.game_id, self._serialize_game_session(game_session))
        
        return game_session

    async def start_new_game_background(
        self,
        game_id: str,
        player_id: str,
        player_location: Location,
        difficulty: Difficulty,
        radius: int = 1000
    ) -> None:
        """
        バックグラウンドでゲームセッションを生成（軽量版を使用）
        
        Args:
            game_id: 事前生成されたゲームID
            player_id: プレイヤーID
            player_location: プレイヤーの現在位置
            difficulty: 難易度
            radius: 証拠検索半径（メートル）
        """
        try:
            # 初期状態をデータベースに保存
            initial_state = {
                "game_id": game_id,
                "player_id": player_id,
                "status": "generating",
                "difficulty": difficulty.value,
                "location": {"lat": player_location.lat, "lng": player_location.lng},
                "radius": radius,
                "created_at": time.time()
            }
            await database_service.save_game_session(game_id, initial_state)
            
            # 軽量版ゲーム生成を実行（高速化）
            game_session = await self.start_new_game_lightweight(
                player_id=player_id,
                player_location=player_location,
                difficulty=difficulty,
                radius=radius
            )
            
            # 生成されたゲームを指定のIDで保存
            game_session.game_id = game_id  # IDを上書き
            await database_service.save_game_session(game_id, self._serialize_game_session(game_session))
            
            logger.info(f"Background game generation completed for {game_id}")
            
        except Exception as e:
            logger.error(f"Background game generation failed for {game_id}: {e}")
            # エラー状態をデータベースに保存
            error_state = {
                "game_id": game_id,
                "status": "error",
                "error": str(e),
                "updated_at": time.time()
            }
            await database_service.save_game_session(game_id, error_state)

    
    async def start_new_game_lightweight(
        self,
        player_id: str,
        player_location: Location,
        difficulty: Difficulty,
        radius: int = 1000
    ) -> GameSession:
        """
        軽量版ゲーム開始（基本検証のみでより高速）
        
        Args:
            player_id: プレイヤーID
            player_location: プレイヤーの現在位置
            difficulty: 難易度
            radius: 証拠検索半径（メートル）
        
        Returns:
            GameSession: 作成されたゲームセッション
        """
        
        # 基本的な検証のみ実行
        if radius not in [200, 500, 1000, 2000]:
            raise ValueError("検索半径は200m, 500m, 1000m, 2000mのいずれかを指定してください")
        
        # POI Service を取得
        poi_service = await lazy_service_manager.get_poi_service()
        
        # 簡単な位置有効性チェック
        try:
            if not await poi_service.validate_location(player_location):
                logger.warning(f"Location validation failed for {player_location}, but continuing with lightweight mode")
        except Exception as e:
            logger.warning(f"Location validation error: {e}, continuing anyway")
        
        # Enhanced POI Service を使用してPOI検索
        enhanced_poi_service = await lazy_service_manager.get_enhanced_poi_service()
        evidence_count = self._get_evidence_count(difficulty)
        
        try:
            evidence_pois = await enhanced_poi_service.find_evidence_suitable_pois(
                player_location,
                radius=radius,
                evidence_count=evidence_count
            )
            
            if len(evidence_pois) < 3:
                # フォールバック: より大きな半径で再試行
                evidence_pois = await enhanced_poi_service.find_evidence_suitable_pois(
                    player_location,
                    radius=radius * 2,  # 半径を倍にして再試行
                    evidence_count=max(3, evidence_count // 2)  # 証拠数を減らす
                )
            
        except Exception as e:
            logger.error(f"POI search failed: {e}")
            # 最終フォールバック: デモ用POIを生成
            evidence_pois = self._generate_fallback_pois(player_location, radius)
        
        # 地域コンテキスト取得（エラー許容）
        try:
            location_context = await poi_service.get_location_context(player_location)
        except Exception as e:
            logger.warning(f"Location context error: {e}, using fallback")
            location_context = "都市部の商業地域"  # フォールバック
        
        # AI Service でシナリオ生成（軽量化）
        ai_service = await lazy_service_manager.get_ai_service()
        
        scenario_request = ScenarioGenerationRequest(
            difficulty=difficulty.value,
            location_context=location_context,
            poi_types=[poi.poi_type.value for poi in evidence_pois],
            suspect_count_range=self._get_suspect_count_range(difficulty)
        )
        
        try:
            scenario = await ai_service.generate_mystery_scenario(scenario_request)
            evidence_list = await ai_service.generate_evidence(
                scenario,
                [{"name": poi.name, "type": poi.poi_type.value, 
                  "lat": poi.location.lat, "lng": poi.location.lng,
                  "poi_id": poi.poi_id, "address": poi.address} for poi in evidence_pois],
                evidence_count
            )
        except Exception as e:
            logger.error(f"AI generation failed: {e}, using fallback")
            # フォールバック: 簡単なシナリオを生成
            scenario, evidence_list = self._generate_fallback_scenario(evidence_pois, difficulty)
        
        # ゲームセッション作成
        game_id = str(uuid.uuid4())
        game_session = GameSession(
            game_id=game_id,
            player_id=player_id,
            difficulty=difficulty,
            scenario=scenario,
            evidence_list=evidence_list,
            player_location=player_location
        )
        
        # データベースに保存
        await database_service.save_game_session(game_session.game_id, self._serialize_game_session(game_session))
        
        return game_session

    
    def _generate_fallback_pois(self, player_location: Location, radius: int):
        """フォールバック用のデモPOI生成"""
        from shared.models.location import POI, POIType
        
        # 基本的なPOIを player_location 周辺に生成
        fallback_pois = []
        poi_types = [POIType.CAFE, POIType.PARK, POIType.SHOP]
        
        for i, poi_type in enumerate(poi_types):
            # player_location から少し離れた場所にPOIを配置
            offset_lat = 0.001 * (i + 1)  # 約100mずつずらす
            offset_lng = 0.001 * (i + 1)
            
            poi = POI(
                poi_id=f"fallback_{poi_type.value}_{i}",
                name=f"デモ{poi_type.value}{i + 1}",
                poi_type=poi_type,
                location=Location(
                    lat=player_location.lat + offset_lat,
                    lng=player_location.lng + offset_lng
                ),
                address=f"デモ住所{i + 1}",
                phone="000-0000-0000",
                rating=4.0
            )
            fallback_pois.append(poi)
            
        return fallback_pois
    
    def _generate_fallback_scenario(self, evidence_pois, difficulty: Difficulty):
        """フォールバック用のシンプルなシナリオ生成"""
        from shared.models.scenario import Scenario, Character, Victim
        from shared.models.evidence import Evidence
        
        # シンプルな被害者
        victim = Victim(
            name="田中太郎",
            age=45,
            occupation="会社員",
            background="地元で働く普通のサラリーマン"
        )
        
        # シンプルな容疑者たち
        suspects = [
            Character(
                name="佐藤花子",
                age=35,
                occupation="カフェ店員",
                personality="内向的で真面目",
                relationship="同僚",
                alibi="その時間は店で働いていました",
                temperament="calm"
            ),
            Character(
                name="鈴木一郎",
                age=50,
                occupation="公園管理人",
                personality="頑固で短気",
                relationship="知人",
                alibi="公園の清掃をしていました",
                temperament="aggressive"  
            )
        ]
        
        scenario = Scenario(
            title="謎の失踪事件",
            description="田中太郎さんが突然姿を消しました。最後に目撃されたのは...",
            location_setting="住宅街",
            victim=victim,
            suspects=suspects,
            culprit_name="佐藤花子",
            motive="金銭トラブル",
            timeline="午後3時頃に最後の目撃情報"
        )
        
        # シンプルな証拠
        evidence_list = []
        for i, poi in enumerate(evidence_pois[:3]):  # 最大3個
            evidence = Evidence(
                evidence_id=f"fallback_evidence_{i}",
                name=f"証拠{i + 1}",
                description=f"{poi.name}で発見された重要な手がかり",
                discovery_text=f"ここで{['財布', '携帯電話', '手紙'][i]}を発見！",
                importance="high" if i == 0 else "medium",
                location=poi.location,
                poi_name=poi.name,
                poi_type=poi.poi_type.value
            )
            evidence_list.append(evidence)
            
        return scenario, evidence_list

    
    async def create_instant_game(
        self,
        player_id: str,
        player_location: Location,
        difficulty: Difficulty,
        radius: int = 1000
    ) -> GameSession:
        """
        即座にゲームを作成（プリセットシナリオ使用）
        
        Args:
            player_id: プレイヤーID
            player_location: プレイヤーの現在位置
            difficulty: 難易度
            radius: 証拠検索半径
        
        Returns:
            GameSession: 即座に作成されたゲームセッション
        """
        
        # プリセットPOIを生成（player_location周辺）
        evidence_pois = self._generate_fallback_pois(player_location, radius)
        
        # プリセットシナリオと証拠を生成
        scenario, evidence_list = self._generate_instant_scenario(evidence_pois, difficulty, player_location)
        
        # ゲームセッション作成
        game_id = str(uuid.uuid4())
        game_session = GameSession(
            game_id=game_id,
            player_id=player_id,
            difficulty=difficulty,
            scenario=scenario,
            evidence_list=evidence_list,
            player_location=player_location
        )
        
        # データベースに保存
        await database_service.save_game_session(game_session.game_id, self._serialize_game_session(game_session))
        
        return game_session

    async def start_progressive_ai_game(
        self,
        player_id: str,
        player_location: Location,
        difficulty: Difficulty,
        radius: int = 1000
    ) -> GameSession:
        """
        段階的AI生成ゲーム開始
        Phase 1: 軽量AI生成で即座開始（5-10秒）
        Phase 2: バックグラウンドで詳細化
        """
        
        self.logger.info(f"段階的AI生成ゲーム開始 - プレイヤー: {player_id}, 難易度: {difficulty.value}")
        
        # Phase 1: 軽量AI生成（5-10秒で完了）
        try:
            # 基本検証
            if radius not in [200, 500, 1000, 2000]:
                raise ValueError("検索半径は200m, 500m, 1000m, 2000mのいずれかを指定してください")
            
            self.logger.info(f"POI検索開始 - 位置: ({player_location.lat}, {player_location.lng}), 半径: {radius}m")
            
            # POI検索（キャッシュ活用で高速化）
            evidence_pois = await self._get_cached_pois(player_location, radius)
            self.logger.info(f"POI検索完了 - 発見数: {len(evidence_pois)}")
            
            if len(evidence_pois) < 3:
                # POIが不足の場合はフォールバックPOI生成
                self.logger.warning(f"POI不足 ({len(evidence_pois)}/3) - フォールバックPOI生成")
                evidence_pois = self._generate_fallback_pois(player_location, radius)
            
            # 軽量AIシナリオ生成
            self.logger.info("AI サービス初期化中...")
            ai_service = await lazy_service_manager.get_ai_service()
            poi_service = await lazy_service_manager.get_poi_service()
            
            self.logger.info("位置コンテキスト取得中...")
            location_context = await poi_service.get_location_context(player_location)
            self.logger.info(f"位置コンテキスト: {location_context[:50]}...")
            
            scenario_request = ScenarioGenerationRequest(
                difficulty=difficulty.value,
                location_context=location_context,
                poi_types=[poi.poi_type.value for poi in evidence_pois[:3]],  # 最初の3つのみ
                suspect_count_range=self._get_suspect_count_range(difficulty)
            )
            
            self.logger.info(f"軽量AIシナリオ生成開始 - 難易度: {scenario_request.difficulty}")
            # 軽量シナリオ生成（5-10秒）
            base_scenario = await ai_service.generate_lightweight_scenario(scenario_request)
            self.logger.info(f"軽量AIシナリオ生成完了 - タイトル: {base_scenario.title}")
            
            # 基本証拠生成（軽量版）
            self.logger.info("軽量証拠生成中...")
            evidence_list = await self._generate_lightweight_evidence(
                base_scenario, evidence_pois[:3]
            )
            self.logger.info(f"軽量証拠生成完了 - 証拠数: {len(evidence_list)}")
            
            # ゲームセッション作成
            game_id = str(uuid.uuid4())
            game_session = GameSession(
                game_id=game_id,
                player_id=player_id,
                difficulty=difficulty,
                scenario=base_scenario,
                evidence_list=evidence_list,
                player_location=player_location
            )
            
            self.logger.info(f"データベース保存中 - ゲームID: {game_id}")
            # データベースに保存
            await database_service.save_game_session(
                game_session.game_id, 
                self._serialize_game_session(game_session)
            )
            
            # Phase 2: バックグラウンドで詳細化開始
            self.logger.info("バックグラウンド詳細化開始...")
            asyncio.create_task(
                self._enhance_game_background(game_id, base_scenario, scenario_request, evidence_pois)
            )
            
            self.logger.info(f"段階的AI生成ゲーム開始完了 - ゲームID: {game_id}")
            return game_session
            
        except Exception as e:
            # 詳細なエラーログ
            self.logger.error(f"段階的AI生成エラー - タイプ: {type(e).__name__}")
            self.logger.error(f"段階的AI生成エラー - メッセージ: {str(e)}")
            self.logger.error(f"段階的AI生成エラー - 詳細: {repr(e)}")
            self.logger.error(f"段階的AI生成エラー - スタックトレース:\n{traceback.format_exc()}")
            
            # エラー時は即座ゲーム生成にフォールバック
            self.logger.warning("即座ゲーム生成へフォールバック中...")
            fallback_result = await self.create_instant_game(player_id, player_location, difficulty, radius)
            self.logger.info(f"フォールバック完了 - タイトル: {fallback_result.scenario.title}")
            return fallback_result
    
    async def _get_cached_pois(self, player_location: Location, radius: int):
        """キャッシュ活用POI取得（高速化）"""
        try:
            enhanced_poi_service = await lazy_service_manager.get_enhanced_poi_service()
            evidence_count = 3  # 軽量版は3つのみ
            
            # タイムアウト延長（20秒）でより確実なPOI取得
            evidence_pois = await asyncio.wait_for(
                enhanced_poi_service.find_evidence_suitable_pois(
                    player_location,
                    radius=radius,
                    evidence_count=evidence_count
                ),
                timeout=20.0
            )
            
            self.logger.info(f"実POI取得成功: {len(evidence_pois)}件")
            return evidence_pois
            
        except (asyncio.TimeoutError, Exception) as e:
            # タイムアウトまたはエラー時はフォールバック
            self.logger.warning(f"POI取得失敗: {type(e).__name__}: {str(e)}")
            self.logger.info("フォールバックPOI生成中...")
            return []
    
    async def _generate_lightweight_evidence(self, scenario: Scenario, evidence_pois) -> List[Evidence]:
        """軽量証拠生成（詳細はバックグラウンドで追加）"""
        from shared.models.evidence import Evidence
        
        evidence_list = []
        evidence_templates = [
            ("重要な手がかり", "事件に関わる重要な証拠", "critical"),
            ("目撃情報", "現場付近での目撃証言", "important"),
            ("物的証拠", "現場に残された証拠品", "important")
        ]
        
        for i, poi in enumerate(evidence_pois):
            if i < len(evidence_templates):
                name, desc, importance = evidence_templates[i]
                evidence = Evidence(
                    evidence_id=f"progressive_evidence_{i}",
                    name="？？？",  # 発見まで非表示
                    description="発見してください",
                    discovery_text=f"{poi.name}で{desc}を発見",
                    importance=importance,
                    location=poi.location,
                    poi_name=poi.name,
                    poi_type=poi.poi_type.value
                )
                evidence_list.append(evidence)
        
        return evidence_list
    
    async def _enhance_game_background(
        self, 
        game_id: str, 
        base_scenario: Scenario, 
        scenario_request: ScenarioGenerationRequest,
        evidence_pois
    ):
        """バックグラウンドでゲーム詳細化"""
        try:
            # Phase 2: シナリオ詳細化
            ai_service = await lazy_service_manager.get_ai_service()
            await ai_service.enhance_scenario_background(game_id, base_scenario, scenario_request)
            
            # Phase 3: 証拠詳細化
            await self._enhance_evidence_background(game_id, base_scenario, evidence_pois)
            
        except Exception as e:
            # バックグラウンド処理はエラーでも基本ゲーム継続
            pass
    
    async def _enhance_evidence_background(self, game_id: str, scenario: Scenario, evidence_pois):
        """バックグラウンドで証拠詳細化"""
        try:
            ai_service = await lazy_service_manager.get_ai_service()
            
            # 詳細証拠生成
            detailed_evidence = await ai_service.generate_evidence(
                scenario,
                [{
                    "name": poi.name, 
                    "type": poi.poi_type.value,
                    "lat": poi.location.lat, 
                    "lng": poi.location.lng,
                    "poi_id": poi.poi_id, 
                    "address": poi.address
                } for poi in evidence_pois],
                len(evidence_pois)
            )
            
            # データベース更新
            await database_service.update_game_evidence(game_id, detailed_evidence)
            
        except Exception as e:
            # エラーでも基本ゲーム継続
            pass
    
    def _generate_instant_scenario(self, evidence_pois, difficulty: Difficulty, player_location: Location):
        """即座用のプリセットシナリオ生成（地域適応版）"""
        from shared.models.scenario import Scenario
        from shared.models.character import Character
        from shared.models.evidence import Evidence
        
        # 地域に基づくシナリオバリエーション
        lat = player_location.lat
        lng = player_location.lng
        
        # 東京周辺かどうかで判定
        is_tokyo_area = (35.5 <= lat <= 35.8) and (139.3 <= lng <= 139.9)
        
        if is_tokyo_area:
            # 東京版シナリオ
            victim = Character(
                name="田中一郎",
                age=42,
                occupation="商社マン", 
                personality="真面目で責任感が強い",
                relationship="被害者",
                alibi="",
                temperament="calm"
            )
            
            suspects = [
                Character(
                    name="佐藤美香",
                    age=38,
                    occupation="カフェオーナー",
                    personality="社交的だが計算高い",
                    relationship="元恋人",
                    alibi="その時間はカフェで常連客と話していました",
                    temperament="nervous"
                ),
                Character(
                    name="山田健太",
                    age=45,
                    occupation="フリーランサー",
                    personality="内向的で嫉妬深い",
                    relationship="元同僚",
                    alibi="公園でジョギングしていました",
                    temperament="volatile"
                ),
                Character(
                    name="鈴木花子",
                    age=35,
                    occupation="書店員",
                    personality="真面目で慎重",
                    relationship="近所の人",
                    alibi="店番をしていました",
                    temperament="calm"
                )
            ]
            
            scenario = Scenario(
                title="消えたビジネスマン",
                description="成功した商社マンが突然姿を消した。最後に目撃されたのは、いつものカフェを出た後だった。",
                victim=victim,
                suspects=suspects,
                culprit="佐藤美香",
                motive="金銭トラブルと復讐心",
                method="計画的な行方不明偽装",
                timeline=["午後6時頃、仕事帰りにカフェを訪れた後に失踪"]
            )
        else:
            # 一般地域版シナリオ
            victim = Character(
                name="松本太郎",
                age=50,
                occupation="地元商店主",
                personality="地域で愛される人柄",
                relationship="被害者",
                alibi="",
                temperament="calm"
            )
            
            suspects = [
                Character(
                    name="林恵子",
                    age=42,
                    occupation="主婦",
                    personality="親切だが秘密主義",
                    relationship="常連客",
                    alibi="買い物に来ていました",
                    temperament="nervous"
                ),
                Character(
                    name="中村誠",
                    age=55,
                    occupation="配達員",
                    personality="無口で頑固",
                    relationship="商売敵",
                    alibi="配達ルートを回っていました",
                    temperament="defensive"
                )
            ]
            
            scenario = Scenario(
                title="商店街の謎",
                description="地域で親しまれていた商店主が行方不明に。商店街に隠された秘密とは？",
                victim=victim,
                suspects=suspects,
                culprit="中村誠",
                motive="商売上の恨み",
                method="計画的な犯行",
                timeline=["閉店後の午後8時頃に最後の目撃情報"]
            )
        
        # 証拠をPOIに配置
        evidence_list = []
        evidence_templates = [
            ("重要な手帳", "被害者の予定が書かれた手帳を発見", "critical"),
            ("目撃者の証言", "事件当日の怪しい人物の目撃情報", "important"),
            ("遺留品", "現場に残された重要な手がかり", "important"),
            ("防犯カメラの映像", "事件の決定的瞬間が映っている", "critical")
        ]
        
        for i, poi in enumerate(evidence_pois):
            if i < len(evidence_templates):
                name, desc, importance = evidence_templates[i]
                evidence = Evidence(
                    evidence_id=f"instant_evidence_{i}",
                    name=name,
                    description=f"{poi.name}で{desc}",
                    discovery_text=f"{poi.name}で重要な証拠を発見！{desc}",
                    importance=importance,
                    location=poi.location,
                    poi_name=poi.name,
                    poi_type=poi.poi_type.value
                )
                evidence_list.append(evidence)
        
        return scenario, evidence_list
    
    async def get_game_session(self, game_id: str) -> Optional[GameSession]:
        """ゲームセッションを取得"""
        
        game_data = await database_service.get_game_session(game_id)
        if not game_data:
            return None
        
        return self._deserialize_game_session(game_data)

    async def _validate_game_session(
        self,
        game_id: str,
        player_id: str
    ) -> Tuple[Optional[GameSession], Optional[EvidenceDiscoveryResult]]:
        """
        ゲームセッションの検証
        
        Returns:
            tuple: (game_session, error_result) 
                   エラーの場合は(None, error_result)を返す
        """
        game_session = await self.get_game_session(game_id)
        if not game_session:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "ゲームセッションが見つかりません"
            )
        
        if game_session.player_id != player_id:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "プレイヤーIDが一致しません"
            )
        
        if game_session.status != GameStatus.ACTIVE:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "ゲームは終了しています"
            )
        
        return game_session, None
    
    async def _validate_evidence(
        self,
        game_session: GameSession,
        evidence_id: str
    ) -> Tuple[Optional[Evidence], Optional[EvidenceDiscoveryResult]]:
        """
        証拠の検証
        
        Returns:
            tuple: (evidence, error_result)
                   エラーの場合は(None, error_result)を返す
        """
        # 証拠が既に発見済みかチェック
        if evidence_id in game_session.discovered_evidence:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "この証拠は既に発見済みです"
            )
        
        # 該当証拠を検索
        evidence = None
        for ev in game_session.evidence_list:
            if ev.evidence_id == evidence_id:
                evidence = ev
                break
        
        if not evidence:
            return None, EvidenceDiscoveryResult.failure_result(
                0.0, "指定された証拠が見つかりません"
            )
        
        return evidence, None
    
    async def _validate_distance_with_gps(
        self,
        gps_reading: GPSReading,
        evidence: Evidence,
        player_id: str,
        game_session: GameSession
    ) -> Tuple[float, Optional[EvidenceDiscoveryResult]]:
        """
        GPS検証付き距離チェック
        
        Returns:
            tuple: (distance, error_result)
                   成功の場合は(distance, None)を返す
        """
        # 高度なGPS検証
        validation_result = gps_service.validate_evidence_discovery(
            gps_reading, evidence.location, player_id
        )
        
        # GPS偽造検出
        spoofing_check = gps_service.detect_gps_spoofing(gps_reading, player_id)
        if spoofing_check["is_likely_spoofed"]:
            return validation_result.distance_to_target, EvidenceDiscoveryResult.failure_result(
                validation_result.distance_to_target,
                "位置情報に問題があります。GPS設定を確認してください。"
            )
        
        # 検証失敗の場合
        if not validation_result.is_valid:
            # 適応的な発見半径を計算
            adaptive_radius = gps_service.calculate_adaptive_discovery_radius(
                gps_reading, evidence.location, evidence.poi_type
            )
            
            return validation_result.distance_to_target, EvidenceDiscoveryResult.failure_result(
                validation_result.distance_to_target,
                f"証拠から{validation_result.distance_to_target:.1f}m離れています。"
                f"GPS精度: {gps_reading.accuracy.horizontal_accuracy:.1f}m "
                f"（{adaptive_radius:.1f}m以内に近づいてください）"
            )
        
        return validation_result.distance_to_target, None
    
    async def _validate_distance_simple(
        self,
        player_location: Location,
        evidence: Evidence,
        game_session: GameSession
    ) -> Tuple[float, Optional[EvidenceDiscoveryResult]]:
        """
        単純な距離チェック（GPS情報なしのフォールバック）
        
        Returns:
            tuple: (distance, error_result)
                   成功の場合は(distance, None)を返す
        """
        distance = player_location.distance_to(evidence.location)
        if distance > game_session.game_rules.discovery_radius:
            return distance, EvidenceDiscoveryResult.failure_result(
                distance, 
                f"証拠から{distance:.1f}m離れています。{game_session.game_rules.discovery_radius}m以内に近づいてください。"
            )
        return distance, None
    
    async def _process_evidence_discovery(
        self,
        game_session: GameSession,
        evidence: Evidence,
        evidence_id: str,
        distance: float
    ) -> EvidenceDiscoveryResult:
        """
        証拠発見処理の実行
        
        Returns:
            EvidenceDiscoveryResult: 発見結果
        """
        # 証拠発見処理
        game_session.discover_evidence(evidence_id)
        evidence.discover()
        
        # 次のヒント生成（オプション）
        next_clue = await self._generate_next_clue(game_session, evidence)
        
        # データベース更新
        await database_service.update_game_session(game_session.game_id, {
            "discovered_evidence": game_session.discovered_evidence,
            "last_activity": datetime.now()
        })
        
        return EvidenceDiscoveryResult.success_result(
            evidence, distance, next_clue
        )
    
    async def discover_evidence(
        self,
        game_id: str,
        player_id: str,
        player_location: Location,
        evidence_id: str,
        gps_reading: Optional[GPSReading] = None
    ) -> EvidenceDiscoveryResult:
        """
        証拠発見処理（GPS検証付き）
        
        Args:
            game_id: ゲームID
            player_id: プレイヤーID 
            player_location: プレイヤー現在位置
            evidence_id: 証拠ID
            gps_reading: GPS読み取り情報（精度情報含む）
        
        Returns:
            EvidenceDiscoveryResult: 発見結果
        """
        
        # ゲームセッションの検証
        game_session, error = await self._validate_game_session(game_id, player_id)
        if error:
            return error
        
        # 証拠の検証
        evidence, error = await self._validate_evidence(game_session, evidence_id)
        if error:
            return error
        
        # 距離検証
        if gps_reading:
            distance, error = await self._validate_distance_with_gps(
                gps_reading, evidence, player_id, game_session
            )
            if error:
                return error
        else:
            distance, error = await self._validate_distance_simple(
                player_location, evidence, game_session
            )
            if error:
                return error
        
        # 証拠発見処理の実行
        return await self._process_evidence_discovery(
            game_session, evidence, evidence_id, distance
        )
    
    async def submit_deduction(
        self,
        request: DeductionRequest
    ) -> DeductionResult:
        """
        推理回答を提出し判定
        
        Args:
            request: 推理リクエスト
        
        Returns:
            DeductionResult: 判定結果
        """
        
        # ゲームセッション取得
        game_session = await self.get_game_session(request.game_id)
        if not game_session:
            raise ValueError("ゲームセッションが見つかりません")
        
        if game_session.player_id != request.player_id:
            raise ValueError("プレイヤーIDが一致しません")
        
        if game_session.status != GameStatus.ACTIVE:
            raise ValueError("ゲームは終了しています")
        
        # 推理判定
        is_correct = game_session.scenario.is_culprit(request.suspect_name)
        
        # キャラクター反応生成
        ai_service = await lazy_service_manager.get_ai_service()
        reactions = await ai_service.judge_deduction(
            game_session.scenario,
            request.suspect_name,
            request.reasoning
        )
        
        # スコア計算
        progress = game_session.progress
        score = GameScore.calculate_score(
            evidence_found=progress.discovered_count,
            total_evidence=progress.total_evidence,
            correct_deduction=is_correct,
            time_elapsed=progress.time_elapsed,
            difficulty=game_session.difficulty,
            hints_used=progress.hints_used,
            discovery_bonus=0  # 証拠発見時に加算済み
        )
        
        # ゲーム完了処理
        game_session.complete_game(score)
        
        # データベース更新
        await database_service.update_game_session(game_session.game_id, {
            "status": "completed",
            "completed_at": game_session.completed_at,
            "final_score": score.total_score
        })
        
        # 履歴保存
        await self._save_game_history(game_session)
        
        return DeductionResult(
            correct=is_correct,
            culprit=game_session.scenario.culprit,
            reactions=reactions,
            game_completed=True,
            score=score,
            explanation=f"真犯人は{game_session.scenario.culprit}でした。動機: {game_session.scenario.motive}"
        )
    
    async def get_player_nearby_evidence(
        self,
        game_id: str,
        player_location: Location
    ) -> List[Evidence]:
        """プレイヤー付近の未発見証拠を取得"""
        
        game_session = await self.get_game_session(game_id)
        if not game_session:
            return []
        
        return game_session.is_evidence_nearby(player_location)
    
    def _get_suspect_count_range(self, difficulty: Difficulty) -> Tuple[int, int]:
        """難易度に応じた容疑者数範囲を取得"""
        ranges = {
            Difficulty.EASY: (3, 4),
            Difficulty.NORMAL: (4, 6),
            Difficulty.HARD: (6, 8)
        }
        return ranges.get(difficulty, (4, 6))
    
    def _get_evidence_count(self, difficulty: Difficulty) -> int:
        """難易度に応じた証拠数を取得"""
        counts = {
            Difficulty.EASY: 3,
            Difficulty.NORMAL: 5,
            Difficulty.HARD: 7
        }
        return counts.get(difficulty, 5)
    
    async def _generate_next_clue(
        self,
        game_session: GameSession,
        discovered_evidence: Evidence
    ) -> Optional[str]:
        """次のヒントを生成"""
        
        remaining = game_session.remaining_evidence
        if not remaining:
            return "全ての証拠を発見しました。推理を始めましょう。"
        
        # 簡単なヒント生成
        if len(remaining) == 1:
            next_evidence = remaining[0]
            return f"最後の証拠は{next_evidence.poi_name}の近くにありそうです。"
        elif len(remaining) <= 3:
            locations = [ev.poi_name for ev in remaining[:2]]
            return f"残りの証拠は{', '.join(locations)}周辺を探してみてください。"
        
        return None
    
    async def _save_game_history(self, game_session: GameSession) -> None:
        """ゲーム履歴を保存"""
        
        if not game_session.completed_at or not game_session.final_score:
            return
        
        duration = int((game_session.completed_at - game_session.created_at).total_seconds())
        
        history_data = {
            "game_id": game_session.game_id,
            "player_id": game_session.player_id,
            "title": game_session.scenario.title,
            "completed_at": game_session.completed_at,
            "score": game_session.final_score.total_score,
            "difficulty": game_session.difficulty.value,
            "location_name": "現在地周辺",  # 実装時により詳細に
            "duration": duration,
            "evidence_found_rate": (
                game_session.final_score.evidence_found / 
                game_session.final_score.total_evidence
            )
        }
        
        await database_service.save_game_history(
            f"{game_session.game_id}_history",
            history_data
        )
    
    def _serialize_game_session(self, game_session: GameSession) -> Dict[str, Any]:
        """GameSessionをFirestore保存用に変換"""
        return game_session.dict()
    
    def _deserialize_game_session(self, data: Dict[str, Any]) -> GameSession:
        """FirestoreデータからGameSessionを復元"""
        return GameSession(**data)


# グローバルゲームサービスインスタンス  
game_service = GameService()