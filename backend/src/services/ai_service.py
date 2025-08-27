"""
AI サービス - Gemini APIを使用したシナリオ生成と推理判定
"""

import json
import asyncio
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from ..core.logging import get_ai_logger

logger = get_ai_logger(__name__)
from ....shared.models.scenario import Scenario, ScenarioGenerationRequest
from ....shared.models.character import Character, Temperament, CharacterReaction
from ....shared.models.evidence import Evidence, EvidenceImportance
from ....shared.models.location import Location

from ..config.settings import get_settings
from ..config.secrets import get_api_key


class AIService:
    """AI サービス（Gemini）"""
    
    def __init__(self):
        self.model = None
        self.generation_config = {
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 4096,
        }
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # レート制限とリトライ設定
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1秒間隔
        self.max_retries = settings.max_scenario_generation_retries
        self.retry_delay = 2.0  # 2秒
    
    async def initialize(self) -> None:
        """AIサービスの初期化"""
        gemini_api_key = get_api_key('gemini')
        if not gemini_api_key:
            raise RuntimeError("Gemini API keyが設定されていません")
            
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    async def _wait_for_rate_limit(self) -> None:
        """レート制限のための待機"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def generate_mystery_scenario(
        self,
        request: ScenarioGenerationRequest
    ) -> Scenario:
        """ミステリーシナリオを生成"""
        
        prompt = self._create_scenario_prompt(request)
        
        for attempt in range(self.max_retries):
            try:
                # レート制限待機
                await self._wait_for_rate_limit()
                
                logger.info(f"シナリオ生成開始 (試行 {attempt + 1}/{self.max_retries})")
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        prompt
                    ),
                    timeout=settings.scenario_generation_timeout
                )
                
                # JSONレスポンスをパース
                scenario_data = json.loads(response.text)
                
                # Scenarioオブジェクトに変換
                scenario = self._parse_scenario_response(scenario_data)
                logger.info(f"シナリオ生成成功: {scenario.title}")
                return scenario
                
            except asyncio.TimeoutError:
                logger.warning(f"シナリオ生成がタイムアウトしました (試行 {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError("シナリオ生成がタイムアウトしました")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"JSONパースエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError(f"シナリオ生成のレスポンス形式が不正です: {str(e)}")
                    
            except Exception as e:
                logger.error(f"シナリオ生成エラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError(f"シナリオ生成に失敗しました: {str(e)}")
        
        raise RuntimeError("最大リトライ回数を超えました")
    
    def _create_scenario_prompt(self, request: ScenarioGenerationRequest) -> str:
        """シナリオ生成用プロンプトを作成"""
        
        difficulty_settings = {
            "easy": {"suspects": 3, "complexity": "シンプル", "red_herrings": "少なめ"},
            "normal": {"suspects": 4, "complexity": "適度", "red_herrings": "適度"},
            "hard": {"suspects": 6, "complexity": "複雑", "red_herrings": "多め"}
        }
        
        settings_info = difficulty_settings.get(request.difficulty, difficulty_settings["normal"])
        
        prompt = f"""
あなたは優秀な推理小説作家です。GPS連動のミステリーゲーム用に、リアリティがあり魅力的な事件シナリオを作成してください。

## 条件設定
- 難易度: {request.difficulty}
- 場所: {request.location_context}
- 利用可能なPOI: {', '.join(request.poi_types)}
- 容疑者数: {settings_info['suspects']}名
- 複雑さ: {settings_info['complexity']}
- ミスリード要素: {settings_info['red_herrings']}

## 出力形式（必ずJSON形式で出力）
{{
  "title": "事件のタイトル",
  "description": "導入文（200-500字、ドラマチック）",
  "victim": {{
    "name": "被害者名",
    "age": 年齢,
    "occupation": "職業",
    "personality": "性格・特徴",
    "temperament": "calm",
    "relationship": "事件との関係",
    "background": "背景情報"
  }},
  "suspects": [
    {{
      "name": "容疑者名",
      "age": 年齢,
      "occupation": "職業", 
      "personality": "性格・特徴",
      "temperament": "calm|volatile|sarcastic|defensive|nervous",
      "relationship": "被害者との関係",
      "alibi": "アリバイ",
      "motive": "動機（犯人以外は薄い動機）",
      "background": "背景情報"
    }}
  ],
  "culprit": "真犯人の名前",
  "motive": "真の犯行動機",
  "method": "犯行手口",
  "timeline": [
    "時系列1",
    "時系列2",
    "時系列3"
  ],
  "theme": "human_drama|time_complex|misdirection|psychological|classic",
  "difficulty_factors": ["複雑さ要因1", "複雑さ要因2"],
  "red_herrings": ["ミスリード要素1", "ミスリード要素2"]
}}

## 重要な注意事項
1. 容疑者のうち1名が必ず真犯人
2. temperament は必ず指定の5種類から選択
3. 日本の法律に違反しない範囲で作成
4. 実在する人物・団体は使用しない
5. 過度に暴力的・グロテスクな描写は避ける
6. プレイヤーが推理できる論理的な手がかりを含む

シナリオを生成してください。
"""
        return prompt
    
    def _parse_scenario_response(self, data: Dict[str, Any]) -> Scenario:
        """AIレスポンスをScenarioオブジェクトに変換"""
        
        # 被害者の作成
        victim_data = data["victim"]
        victim = Character(
            name=victim_data["name"],
            age=victim_data["age"],
            occupation=victim_data["occupation"],
            personality=victim_data["personality"],
            temperament=Temperament(victim_data["temperament"]),
            relationship=victim_data["relationship"],
            background=victim_data.get("background")
        )
        
        # 容疑者リストの作成
        suspects = []
        for suspect_data in data["suspects"]:
            suspect = Character(
                name=suspect_data["name"],
                age=suspect_data["age"],
                occupation=suspect_data["occupation"],
                personality=suspect_data["personality"],
                temperament=Temperament(suspect_data["temperament"]),
                relationship=suspect_data["relationship"],
                alibi=suspect_data.get("alibi"),
                motive=suspect_data.get("motive"),
                background=suspect_data.get("background")
            )
            suspects.append(suspect)
        
        return Scenario(
            title=data["title"],
            description=data["description"],
            victim=victim,
            suspects=suspects,
            culprit=data["culprit"],
            motive=data["motive"],
            method=data["method"],
            timeline=data["timeline"],
            theme=data.get("theme"),
            difficulty_factors=data.get("difficulty_factors", []),
            red_herrings=data.get("red_herrings", [])
        )
    
    async def generate_evidence(
        self,
        scenario: Scenario,
        poi_list: List[Dict[str, Any]],
        evidence_count: int = 5
    ) -> List[Evidence]:
        """証拠を生成して POI に配置"""
        
        prompt = f"""
以下のミステリーシナリオ用に、POIに配置する証拠を生成してください。

## シナリオ情報
タイトル: {scenario.title}
犯人: {scenario.culprit}
犯行動機: {scenario.motive}
犯行手口: {scenario.method}

## 容疑者情報
{json.dumps([{"name": s.name, "relationship": s.relationship} for s in scenario.suspects], ensure_ascii=False)}

## 利用可能なPOI
{json.dumps(poi_list, ensure_ascii=False)}

## 要求
- 証拠数: {evidence_count}個
- 重要度のバランス: critical(1個), important(2-3個), misleading(1-2個), background(残り)
- 各証拠は異なるPOIに配置

## 出力形式（JSON）
{{
  "evidence": [
    {{
      "name": "証拠名",
      "description": "証拠の詳細説明",
      "discovery_text": "発見時のドラマチックな描写",
      "importance": "critical|important|misleading|background",
      "poi_name": "配置するPOI名（poi_listから選択）",
      "related_character": "関連キャラクター名（オプション）",
      "clue_text": "次のヒント（オプション）"
    }}
  ]
}}

証拠を生成してください。
"""
        
        for attempt in range(self.max_retries):
            try:
                # レート制限待機
                await self._wait_for_rate_limit()
                
                logger.info(f"証拠生成開始 (試行 {attempt + 1}/{self.max_retries})")
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        prompt
                    ),
                    timeout=settings.scenario_generation_timeout
                )
                
                evidence_data = json.loads(response.text)
                evidence_list = []
                
                for i, item in enumerate(evidence_data["evidence"]):
                    # POI情報を取得
                    poi_info = next(
                        (poi for poi in poi_list if poi["name"] == item["poi_name"]),
                        poi_list[i % len(poi_list)]  # フォールバック
                    )
                    
                    evidence = Evidence(
                        evidence_id=f"evidence_{i+1}",
                        name=item["name"],
                        description=item.get("description", f"詳しい情報は{poi_info['name']}で発見してください"),
                        discovery_text=item.get("discovery_text", f"あなたは{poi_info['name']}で{item['name']}を発見した！これは事件に関わる重要な手がかりのようだ..."),
                        importance=EvidenceImportance(item["importance"]),
                        location=Location(
                            lat=poi_info["lat"],
                            lng=poi_info["lng"]
                        ),
                        poi_name=poi_info["name"],
                        poi_type=poi_info.get("type", "unknown"),
                        related_character=item.get("related_character"),
                        clue_text=item.get("clue_text")
                    )
                    evidence_list.append(evidence)
                
                logger.info(f"証拠生成成功: {len(evidence_list)}個の証拠を生成")
                return evidence_list
                
            except asyncio.TimeoutError:
                logger.warning(f"証拠生成がタイムアウトしました (試行 {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError("証拠生成がタイムアウトしました")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"証拠生成JSONパースエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError(f"証拠生成のレスポンス形式が不正です: {str(e)}")
                    
            except Exception as e:
                logger.error(f"証拠生成エラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError(f"証拠生成に失敗しました: {str(e)}")
        
        raise RuntimeError("最大リトライ回数を超えました")
    
    async def judge_deduction(
        self,
        scenario: Scenario,
        suspect_name: str,
        reasoning: Optional[str] = None
    ) -> List[CharacterReaction]:
        """推理を判定し、キャラクター反応を生成"""
        
        is_correct = scenario.is_culprit(suspect_name)
        culprit_character = scenario.culprit_character
        accused_character = scenario.get_suspect_by_name(suspect_name)
        
        prompt = f"""
推理小説の結末シーンを作成してください。

## シナリオ
タイトル: {scenario.title}
真犯人: {scenario.culprit}
犯行動機: {scenario.motive}

## プレイヤーの推理
推理した犯人: {suspect_name}
正解: {"正解" if is_correct else "不正解"}

## キャラクター情報
{json.dumps([
    {
        "name": c.name, 
        "temperament": c.temperament.value,
        "personality": c.personality
    } for c in scenario.suspects
], ensure_ascii=False)}

## 要求
推理結果に応じた各キャラクターの反応を生成。

## 出力形式（JSON）
{{
  "reactions": [
    {{
      "character_name": "キャラクター名",
      "reaction": "反応テキスト（気質に応じて）",
      "reaction_type": "confession|denial|surprise|praise",
      "emotion_intensity": 0.8
    }}
  ]
}}

キャラクター反応を生成してください。
"""
        
        for attempt in range(self.max_retries):
            try:
                # レート制限待機
                await self._wait_for_rate_limit()
                
                logger.info(f"推理判定開始 (試行 {attempt + 1}/{self.max_retries})")
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.model.generate_content,
                        prompt
                    ),
                    timeout=settings.scenario_generation_timeout
                )
                
                reaction_data = json.loads(response.text)
                reactions = []
                
                for item in reaction_data["reactions"]:
                    character = scenario.get_suspect_by_name(item["character_name"])
                    if character:
                        reaction = CharacterReaction(
                            character_name=item["character_name"],
                            reaction=item["reaction"],
                            reaction_type=item["reaction_type"],
                            temperament=character.temperament,
                            emotion_intensity=item.get("emotion_intensity", 0.5)
                        )
                        reactions.append(reaction)
                
                logger.info(f"推理判定成功: {len(reactions)}個の反応を生成")
                return reactions
                
            except asyncio.TimeoutError:
                logger.warning(f"推理判定がタイムアウトしました (試行 {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError("推理判定がタイムアウトしました")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"推理判定JSONパースエラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError(f"推理判定のレスポンス形式が不正です: {str(e)}")
                    
            except Exception as e:
                logger.error(f"推理判定エラー (試行 {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    raise RuntimeError(f"推理判定に失敗しました: {str(e)}")
        
        raise RuntimeError("最大リトライ回数を超えました")


# グローバルAIサービスインスタンス
ai_service = AIService()