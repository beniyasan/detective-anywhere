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
from shared.models.scenario import Scenario, ScenarioGenerationRequest
from shared.models.character import Character, Temperament, CharacterReaction
from shared.models.evidence import Evidence, EvidenceImportance
from shared.models.location import Location

from ..config.settings import get_settings
from ..config.secrets import get_api_key


class AIService:
    """AI サービス（Gemini）"""
    
    def __init__(self):
        self.model = None
        self.gemini_api_key = get_api_key("gemini")
        
        # Gemini API初期化
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            logger.info("Gemini API configured successfully")
        else:
            logger.warning("Gemini API key not found - using fallback mode")
        
        self.model_name = get_settings().api.gemini_model if hasattr(get_settings().api, 'gemini_model') else 'gemini-1.5-pro'
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
        self.max_retries = get_settings().api.max_scenario_generation_retries if hasattr(get_settings().api, 'max_scenario_generation_retries') else 3
        self.retry_delay = 2.0  # 2秒  # 2秒
    
    async def initialize(self) -> None:
        """AIサービスの初期化"""
        try:
            gemini_api_key = get_api_key('gemini')
            if not gemini_api_key:
                logger.error("Gemini API key取得失敗 - Secret ManagerまたはCloud Run環境変数を確認してください")
                raise RuntimeError("Gemini API keyが設定されていません")
            
            logger.info(f"Gemini API key取得成功 (長さ: {len(gemini_api_key)})")
            genai.configure(api_key=gemini_api_key)
            
            settings = get_settings()
            model_name = getattr(settings.api, 'gemini_model', 'gemini-1.5-flash')
            logger.info(f"Gemini model設定: {model_name}")
            
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # APIキーをインスタンス変数にも設定（重複初期化の解決）
            self.gemini_api_key = gemini_api_key
            
            logger.info("AI Service初期化完了")
            
        except Exception as e:
            logger.error(f"AI Service初期化エラー: {e}")
            raise RuntimeError(f"AI Service初期化に失敗しました: {str(e)}")
    
    async def _call_gemini_api(self, prompt: str) -> str:
        """Gemini APIを呼び出してレスポンスを取得"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        response = await model.generate_content_async(prompt)
        
        # JSONブロックを抽出
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "{" in text:
            # JSONオブジェクトの開始と終了を見つける
            start = text.index("{")
            end = text.rindex("}") + 1
            text = text[start:end]
        
        return text
    
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
                
                # Gemini APIでシナリオ生成
                if self.gemini_api_key:
                    logger.info("Using Gemini API for scenario generation")
                    response = await self._call_gemini_api(prompt)
                    json_str = self._clean_json_response(response)
                    scenario_data = json.loads(json_str)
                else:
                    # APIキーがない場合はランダムモックを使用
                    logger.info("No API key, using randomized mock scenario")
                    scenario_data = self._generate_random_scenario(request.location_context)
                
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

    async def generate_lightweight_scenario(
        self,
        request: ScenarioGenerationRequest
    ) -> Scenario:
        """
        軽量シナリオ生成（5-10秒で完了）
        - 基本骨格のみ生成
        - 詳細は後から段階的に追加
        """
        
        # 軽量プロンプト作成（文字数・複雑さを大幅削減）
        lightweight_prompt = self._create_lightweight_scenario_prompt(request)
        
        try:
            logger.info(f"軽量シナリオ生成開始 - 難易度: {request.difficulty}")
            logger.info(f"APIキー存在確認: {bool(self.gemini_api_key)}")
            
            # Gemini Flash（高速モデル）を使用
            if self.gemini_api_key:
                logger.info("Gemini API使用してシナリオ生成中...")
                logger.info(f"プロンプト内容（最初100文字）: {lightweight_prompt[:100]}")
                
                try:
                    response = await self._call_gemini_api_fast(lightweight_prompt)
                    logger.info(f"Gemini API応答受信 - 文字数: {len(response)}")
                    logger.info(f"応答内容（最初200文字）: {response[:200]}")
                    
                    try:
                        # マークダウンコードブロックを除去
                        json_str = self._clean_json_response(response)
                        scenario_data = json.loads(json_str)
                        logger.info(f"JSON解析成功 - タイトル: {scenario_data.get('title', '不明')}")
                        logger.info(f"説明文字数: {len(scenario_data.get('description', ''))}")
                        logger.info(f"説明内容: {scenario_data.get('description', '')[:100]}...")
                        
                        # 基本シナリオオブジェクト作成
                        scenario = self._parse_lightweight_scenario(scenario_data)
                        logger.info(f"軽量シナリオ生成完了: {scenario.title} (難易度: {request.difficulty})")
                        logger.info(f"最終説明文字数: {len(scenario.description)}")
                        return scenario
                        
                    except json.JSONDecodeError as je:
                        logger.error(f"Gemini API応答のJSON解析失敗: {je}")
                        logger.error(f"レスポンス内容: {response[:500]}...")
                        raise
                        
                except Exception as gemini_error:
                    logger.error(f"Gemini API呼び出しエラー: {gemini_error}")
                    logger.error(f"エラータイプ: {type(gemini_error).__name__}")
                    logger.error(f"エラー詳細: {repr(gemini_error)}")
                    raise  # エラーを再発生させてフォールバックへ
                    
            else:
                logger.warning("APIキーなし - モックシナリオ生成")
                # 高速モック生成
                scenario_data = self._generate_fast_mock_scenario(request.location_context, request.suspect_count_range)
                scenario = self._parse_lightweight_scenario(scenario_data)
                logger.info(f"モックシナリオ生成完了: {scenario.title}")
                return scenario
            
        except Exception as e:
            logger.error(f"軽量シナリオ生成エラー: {e}")
            logger.error(f"エラー詳細: {type(e).__name__}: {str(e)}")
            # フォールバック: 即座シナリオ生成
            logger.info("フォールバックシナリオ生成中...")
            fallback_data = self._generate_fast_mock_scenario(request.location_context, request.suspect_count_range)
            scenario = self._parse_lightweight_scenario(fallback_data)
            logger.info(f"フォールバックシナリオ生成完了: {scenario.title}")
            return scenario
    
    async def enhance_scenario_background(
        self,
        game_id: str,
        base_scenario: Scenario,
        request: ScenarioGenerationRequest
    ):
        """
        バックグラウンドでシナリオを詳細化
        - キャラクター背景強化
        - 複雑な推理要素追加
        - 動機・手法の詳細化
        """
        
        try:
            logger.info(f"シナリオ詳細化開始 game_id: {game_id}")
            
            # 詳細化プロンプト作成
            enhancement_prompt = self._create_enhancement_prompt(base_scenario, request)
            
            # バックグラウンドで詳細生成
            if self.gemini_api_key:
                enhanced_data = await self._call_gemini_api(enhancement_prompt)
                enhanced_scenario = self._merge_enhanced_scenario(base_scenario, enhanced_data)
            else:
                enhanced_scenario = self._enhance_mock_scenario(base_scenario)
            
            # データベースに更新保存
            from .database_service import database_service
            await database_service.update_game_scenario(game_id, enhanced_scenario)
            
            logger.info(f"シナリオ詳細化完了 game_id: {game_id}")
            
        except Exception as e:
            logger.error(f"シナリオ詳細化エラー game_id: {game_id}, error: {e}")
            # エラーでも基本ゲームは継続可能
    
    def _create_scenario_prompt(self, request: ScenarioGenerationRequest) -> str:
        """シナリオ生成用プロンプトを作成"""
        
        difficulty_settings = {
            "easy": {
                "suspects": 3, 
                "complexity": "シンプル", 
                "red_herrings": "少なめ",
                "description_length": "200-400文字",
                "detail_level": "基本的な情報と簡潔な背景説明"
            },
            "normal": {
                "suspects": 4, 
                "complexity": "適度", 
                "red_herrings": "適度",
                "description_length": "400-600文字",
                "detail_level": "詳細な背景情報と人間関係を含む"
            },
            "hard": {
                "suspects": 6, 
                "complexity": "複雑", 
                "red_herrings": "多め",
                "description_length": "600-1000文字",
                "detail_level": "非常に詳細な人間関係、複雑な背景設定、複数の伏線を含む"
            }
        }
        
        settings_info = difficulty_settings.get(request.difficulty, difficulty_settings["normal"])
        
        prompt = f"""
あなたは優秀な推理小説作家です。GPS連動のミステリーゲーム用に、論理的で魅力的な事件シナリオを作成してください。

## 重要な要件
**3つの証拠から論理的に犯人を特定できるシナリオを作成してください。**
- 証拠1: 犯人でない容疑者を除外できる証拠
- 証拠2: さらに別の容疑者を除外できる証拠
- 証拠3: 残った容疑者が犯人であることを示す決定的証拠

## 条件設定
- 難易度: {request.difficulty}
- 場所: {request.location_context}
- 利用可能なPOI: {', '.join(request.poi_types)}
- 容疑者数: {settings_info['suspects']}名（必ず3名）
- 複雑さ: {settings_info['complexity']}
- ミスリード要素: {settings_info['red_herrings']}
- 説明文の長さ: **{settings_info['description_length']}**
- 詳細レベル: {settings_info['detail_level']}

## シナリオ作成のルール
1. 各容疑者に明確で異なる動機を設定
2. 各容疑者のアリバイに穴や矛盾を設定（犯人は致命的な矛盾）
3. 証拠は段階的に真相に近づくよう設計
4. 毎回異なるシナリオを生成（ランダム要素を含める）
5. 現実的で信憑性のある事件設定

## 出力形式（必ずJSON形式で出力）
{{
  "title": "事件のタイトル",
  "description": "導入文（**必ず{settings_info['description_length']}で作成**、ドラマチック、{settings_info['detail_level']}）",
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
  "red_herrings": ["ミスリード要因1", "ミスリード要因2"]
}}

## 重要な注意事項
1. 容疑者のうち1名が必ず真犯人
2. temperament は必ず指定の5種類から選択
3. 日本の法律に違反しない範囲で作成
4. 実在する人物・団体は使用しない
5. 過度に暴力的・グロテスクな描写は避ける
6. プレイヤーが推理できる論理的な手がかりを含む
7. **最重要: 難易度{request.difficulty}に応じて、説明文を必ず{settings_info['description_length']}の範囲で作成し、{settings_info['detail_level']}**

シナリオを生成してください。
"""
        return prompt

    def _create_lightweight_scenario_prompt(self, request: ScenarioGenerationRequest) -> str:
        """軽量シナリオ生成用プロンプト（高速・最小限）"""
        import random
        import time
        
        # 難易度による文字数調整
        difficulty_settings = {
            "easy": {
                "description_length": "120-200文字",
                "complexity": "単純で分かりやすい",
                "suspects": request.suspect_count_range[1]
            },
            "normal": {
                "description_length": "200-350文字", 
                "complexity": "適度に複雑な",
                "suspects": request.suspect_count_range[1]
            },
            "hard": {
                "description_length": "350-500文字",
                "complexity": "複雑で手の込んだ",
                "suspects": request.suspect_count_range[1]
            }
        }
        
        settings = difficulty_settings.get(request.difficulty, difficulty_settings["normal"])
        
        # ユニークネス確保
        random_seed = random.randint(1000, 9999)
        timestamp = int(time.time())
        
        # シンプルなバリエーション
        themes = ["人間関係", "金銭問題", "秘密", "裏切り"]
        crimes = ["失踪", "盗難", "詐欺", "恐喝"]
        
        selected_theme = random.choice(themes)
        selected_crime = random.choice(crimes)
        
        # location_contextの処理
        location_info = request.location_context
        if not location_info or location_info == "不明な地域の情報です。":
            location_info = "都市部の商業地域"
        location_clean = location_info.rstrip('。')
        
        # 容疑者のJSONテンプレートを動的生成
        suspects_template = []
        temperaments = ["nervous", "volatile", "sarcastic", "defensive", "calm"]
        
        for i in range(settings["suspects"]):
            suspect_num = i + 1
            temperament = temperaments[i % len(temperaments)]
            suspects_template.append(f'''    {{
      "name": "容疑者{suspect_num}名",
      "age": 年齢,
      "occupation": "職業", 
      "personality": "性格",
      "temperament": "{temperament}",
      "relationship": "{selected_theme}に関連する関係",
      "alibi": "具体的アリバイ",
      "motive": null,
      "background": null
    }}''')
        
        suspects_json = ",\n".join(suspects_template)
        
        # よりシンプルなプロンプト
        prompt = f"""推理ゲーム用のミステリー事件シナリオをJSON形式で作成してください。

場所: {location_clean}
難易度: {request.difficulty}
テーマ: {selected_theme}を背景とした{selected_crime}事件
容疑者数: {settings["suspects"]}人

【厳守事項】:
- description文字数: 必ず{settings["description_length"]}（最低でも{settings["description_length"].split('-')[0]}文字以上）
- 短い文章は絶対禁止 - 「○○事件。証拠を集めて推理を進めよう」のような短文は不可
- 毎回異なるユニークなシナリオ生成
- 具体的で詳細な事件描写が必要
- 容疑者は必ず{settings["suspects"]}人生成

JSON出力:
{{
  "title": "ユニークな事件タイトル（10-15文字）",
  "description": "【重要】必ず{settings['description_length']}で記述してください。{location_clean}で起きた{selected_theme}に関連する{selected_crime}事件の詳細な描写。被害者の状況、事件の経緯、現場の様子、不可解な謎、関係者の動き、時系列などを含む魅力的で引き込まれる事件説明。「証拠を集めて推理を進めよう」のような短い文ではなく、具体的で詳細な事件ストーリーを{settings['description_length']}で記述。",
  "victim": {{
    "name": "被害者名",
    "age": 年齢,
    "occupation": "職業",
    "personality": "性格",
    "temperament": "calm",
    "relationship": "被害者",
    "alibi": ""
  }},
  "suspects": [
{suspects_json}
  ],
  "culprit": "容疑者1名",
  "motive": "具体的な動機",
  "method": "手口", 
  "timeline": ["時系列"],
  "theme": "human_drama",
  "difficulty_factors": [],
  "red_herrings": []
}}

注意: 
- temperamentは calm|volatile|sarcastic|defensive|nervous から選択必須
- ユニーク性のためのID: {random_seed}-{timestamp}
- 【最重要】description は必ず{settings["description_length"]}で詳細に記述してください
"""
        return prompt
    
    def _create_enhancement_prompt(self, base_scenario: Scenario, request: ScenarioGenerationRequest) -> str:
        """シナリオ詳細化用プロンプト"""
        
        prompt = f"""
以下の基本シナリオを詳細化してください。

## 基本シナリオ
タイトル: {base_scenario.title}
説明: {base_scenario.description}
被害者: {base_scenario.victim.name}
容疑者: {[s.name for s in base_scenario.suspects]}
真犯人: {base_scenario.culprit}

## 詳細化要求
- 各キャラクターの背景を詳細化
- 複雑な人間関係を追加
- 動機を深掘り
- ミスリード要素を追加
- 推理要素を強化

## 出力形式（JSON）
基本シナリオの全フィールドを含め、以下を詳細化：
- description: 400-800文字に拡張
- 各キャラクターのbackground, motive を詳細化
- difficulty_factors と red_herrings を追加
- timeline を詳細化

詳細化されたシナリオを生成してください。
"""
        return prompt

    def _clean_json_response(self, response: str) -> str:
        """Gemini APIのレスポンスからマークダウンコードブロックを除去"""
        if response.startswith("```json"):
            return response.replace("```json", "").replace("```", "").strip()
        elif response.startswith("```"):
            return response.replace("```", "").strip()
        return response
    
    async def _call_gemini_api_fast(self, prompt: str) -> str:
        """Gemini Flash（高速モデル）でAPI呼び出し"""
        
        try:
            logger.info("Gemini API呼び出し開始")
            logger.info(f"使用モデル: gemini-1.5-flash")
            logger.info(f"プロンプト文字数: {len(prompt)}")
            
            # より軽量なGemini 1.5 Flash モデルを使用
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # より軽量な設定（レスポンス速度重視）
            generation_config = genai.types.GenerationConfig(
                temperature=0.5,  # より低い温度で安定性向上
                max_output_tokens=2000,  # 適度に制限
                top_p=0.8,
                top_k=20,  # 選択肢を絞って高速化
                candidate_count=1
            )
            
            logger.info("Gemini API リクエスト送信中...")
            
            # タイムアウト60秒
            response = await asyncio.wait_for(
                model.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    ]
                ),
                timeout=60.0  # 60秒に延長
            )
            
            logger.info("Gemini API レスポンス受信成功")
            logger.info(f"レスポンス文字数: {len(response.text)}")
            
            return response.text
            
        except asyncio.TimeoutError:
            logger.error("Gemini API タイムアウト (60秒)")
            raise TimeoutError("Gemini Flash API call timed out")
        except Exception as e:
            logger.error(f"Gemini Flash API エラー: {e}")
            logger.error(f"エラータイプ: {type(e).__name__}")
            raise

    def _generate_fast_mock_scenario(self, location_context: str, suspect_count_range: tuple = (3, 3)) -> dict:
        """高速モックシナリオ生成"""
        
        import random
        
        titles = ["突然の失踪", "謎の訪問者", "消えた証拠", "偽りの証言"]
        occupations = ["会社員", "店主", "学生", "主婦", "フリーランサー"]
        
        # 容疑者数を動的に決定
        suspect_count = random.randint(suspect_count_range[0], suspect_count_range[1])
        
        # 容疑者名のプール
        suspect_names = [
            "佐藤花子", "田中一郎", "鈴木次郎", "高橋美咲", "渡辺健太",
            "伊藤良子", "山田浩二", "中村真理", "小林隆史", "加藤恵美"
        ]
        
        # 容疑者をランダムに生成
        suspects = []
        selected_names = random.sample(suspect_names, suspect_count)
        temperaments = ["nervous", "volatile", "defensive", "calm"]
        
        for i, name in enumerate(selected_names):
            suspects.append({
                "name": name,
                "age": random.randint(25, 60),
                "occupation": random.choice(occupations),
                "personality": random.choice(["社交的だが秘密主義", "無口で頑固", "神経質で疑い深い", "明るく積極的"]),
                "temperament": random.choice(temperaments),
                "relationship": random.choice(["知人", "同僚", "近隣住民", "関係者"]),
                "alibi": random.choice(["仕事をしていました", "家にいました", "買い物に出ていました", "友人と会っていました"]),
                "motive": None,
                "background": None
            })
        
        return {
            "title": random.choice(titles),
            "description": f"{location_context}で起きた不可解な事件。真相を探るため、証拠を集めて推理を進めよう。",
            "victim": {
                "name": "山田太郎",
                "age": random.randint(25, 60),
                "occupation": random.choice(occupations),
                "personality": "真面目で責任感が強い",
                "temperament": "calm",
                "relationship": "被害者",
                "alibi": ""
            },
            "suspects": suspects,
            "culprit": suspects[0]["name"],  # 最初の容疑者を犯人に設定
            "motive": "金銭トラブル",
            "method": "計画的犯行",
            "timeline": ["事件発生前の異変"],
            "theme": "human_drama",
            "difficulty_factors": [],
            "red_herrings": []
        }

    def _parse_lightweight_scenario(self, scenario_data: dict) -> Scenario:
        """軽量シナリオデータをScenarioオブジェクトに変換"""
        
        from shared.models.character import Character
        from shared.models.scenario import Scenario
        
        # 被害者作成
        victim_data = scenario_data["victim"]
        victim = Character(
            name=victim_data["name"],
            age=victim_data["age"],
            occupation=victim_data["occupation"],
            personality=victim_data["personality"],
            temperament=victim_data["temperament"],
            relationship=victim_data["relationship"],
            alibi=victim_data.get("alibi", "")
        )
        
        # 容疑者リスト作成
        suspects = []
        for suspect_data in scenario_data["suspects"]:
            suspect = Character(
                name=suspect_data["name"],
                age=suspect_data["age"],
                occupation=suspect_data["occupation"],
                personality=suspect_data["personality"],
                temperament=suspect_data["temperament"],
                relationship=suspect_data["relationship"],
                alibi=suspect_data.get("alibi", "")
            )
            suspects.append(suspect)
        
        # Scenarioオブジェクト作成
        scenario = Scenario(
            title=scenario_data["title"],
            description=scenario_data["description"],
            victim=victim,
            suspects=suspects,
            culprit=scenario_data["culprit"],
            motive=scenario_data["motive"],
            method=scenario_data["method"],
            timeline=scenario_data.get("timeline", []),
            theme=scenario_data.get("theme"),
            difficulty_factors=scenario_data.get("difficulty_factors", []),
            red_herrings=scenario_data.get("red_herrings", [])
        )
        
        return scenario

    def _create_fallback_scenario(self, location_context: str, suspect_count_range: tuple = (3, 3)) -> Scenario:
        """フォールバック用即座シナリオ"""
        fallback_data = self._generate_fast_mock_scenario(location_context, suspect_count_range)
        return self._parse_lightweight_scenario(fallback_data)
    
    def _generate_random_scenario(self, location_context: str) -> Dict[str, Any]:
        """ランダムな要素を含むモックシナリオを生成"""
        import random
        
        # シナリオテンプレート
        scenario_templates = [
            {
                "title": "深夜のカフェ殺人事件",
                "victim": {"name": "木村太郎", "age": 42, "occupation": "カフェオーナー"},
                "location": "深夜営業のカフェ",
                "time": "午後11時",
                "method": "毒殺",
                "culprit_index": 0
            },
            {
                "title": "公園の謎の失踪事件",
                "victim": {"name": "高橋美咲", "age": 28, "occupation": "ジョガー"},
                "location": "早朝の公園",
                "time": "午前5時",
                "method": "突き落とし",
                "culprit_index": 1
            },
            {
                "title": "商店街の密室殺人",
                "victim": {"name": "渡辺次郎", "age": 55, "occupation": "商店主"},
                "location": "閉店後の商店",
                "time": "午後9時",
                "method": "絞殺",
                "culprit_index": 2
            },
            {
                "title": "オフィスビルの転落事件",
                "victim": {"name": "斉藤花子", "age": 35, "occupation": "会社員"},
                "location": "オフィスビルの屋上",
                "time": "午後7時",
                "method": "転落",
                "culprit_index": 0
            },
            {
                "title": "駐車場の襲撃事件",
                "victim": {"name": "伊藤健一", "age": 48, "occupation": "タクシー運転手"},
                "location": "地下駐車場",
                "time": "午前2時",
                "method": "鈍器による殴打",
                "culprit_index": 1
            }
        ]
        
        # 容疑者テンプレート
        suspect_templates = [
            {"name": "山田太郎", "age": 30, "occupation": "会社員", "personality": "神経質で短気"},
            {"name": "佐藤花子", "age": 25, "occupation": "パート店員", "personality": "表面上は明るいが計算高い"},
            {"name": "鈴木一郎", "age": 40, "occupation": "自営業", "personality": "プライドが高く頑固"},
            {"name": "田中美咲", "age": 35, "occupation": "主婦", "personality": "嫉妬深く執念深い"},
            {"name": "高橋健太", "age": 28, "occupation": "フリーター", "personality": "怠惰だが賢い"},
            {"name": "渡辺真理", "age": 45, "occupation": "教師", "personality": "厳格で融通が利かない"},
            {"name": "伊藤次郎", "age": 50, "occupation": "警備員", "personality": "無口で観察力が鋭い"},
            {"name": "斉藤美香", "age": 32, "occupation": "看護師", "personality": "献身的だが秘密主義"}
        ]
        
        # ランダムに選択
        template = random.choice(scenario_templates)
        selected_suspects = random.sample(suspect_templates, 3)
        
        # 動機のリスト
        motives = [
            "金銭トラブルで恨みを持っていた",
            "不倫関係が暴露されることを恐れた",
            "過去の秘密を握られていた",
            "仕事上の対立があった",
            "嫉妬と怒りが爆発した",
            "復讐のため計画的に実行した"
        ]
        
        # 犯人を決定
        culprit_index = template["culprit_index"]
        culprit_name = selected_suspects[culprit_index]["name"]
        
        # シナリオデータを生成
        return {
            "title": template["title"],
            "description": f"{location_context}で起きた衝撃的な事件。{template['time']}、{template['location']}で{template['victim']['name']}さん（{template['victim']['age']}歳・{template['victim']['occupation']}）が遺体で発見された。現場の状況から{template['method']}と推定される。警察の捜査により、3人の重要参考人が浮上。それぞれに動機があり、アリバイも曖昧だ。限られた証拠から真犯人を見つけ出せ！",
            "victim": {
                "name": template["victim"]["name"],
                "age": template["victim"]["age"],
                "occupation": template["victim"]["occupation"],
                "personality": "真面目で几帳面な性格",
                "temperament": "calm",
                "relationship": "被害者",
                "background": f"{location_context}で{template['victim']['occupation']}として働いていた"
            },
            "suspects": [
                {
                    "name": suspect["name"],
                    "age": suspect["age"],
                    "occupation": suspect["occupation"],
                    "personality": suspect["personality"],
                    "temperament": random.choice(["calm", "nervous", "defensive"]),
                    "relationship": random.choice(["同僚", "近隣住民", "知人", "取引相手"]),
                    "alibi": f"事件当時、{'自宅にいた' if i != culprit_index else '現場付近にいた'}と主張",
                    "motive": random.choice(motives) if i == culprit_index else random.choice(motives[:3]),
                    "background": f"{location_context}在住"
                }
                for i, suspect in enumerate(selected_suspects)
            ],
            "culprit": culprit_name,
            "motive": random.choice(motives),
            "method": template["method"],
            "timeline": [
                f"{template['time']}の30分前: 被害者が{template['location']}に到着",
                f"{template['time']}: 事件発生",
                f"{template['time']}の30分後: 遺体発見、通報"
            ],
            "theme": "classic_mystery",
            "difficulty_factors": [],
            "red_herrings": []
        }
    
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
以下のミステリーシナリオ用に、3つの証拠で論理的に犯人を特定できる証拠を生成してください。

## シナリオ情報
タイトル: {scenario.title}
犯人: {scenario.culprit}
犯行動機: {scenario.motive}
犯行手口: {scenario.method}

## 容疑者情報
{json.dumps([{"name": s.name, "alibi": s.alibi, "motive": s.motive} for s in scenario.suspects], ensure_ascii=False)}

## 利用可能なPOI
{json.dumps(poi_list, ensure_ascii=False)}

## 重要：3つの証拠の論理構造
1. **第1の証拠（除外証拠）**: 容疑者Aが犯人でないことを示す証拠
   - 例：容疑者Aが事件時刻に別の場所にいたことを証明する防犯カメラ映像
   
2. **第2の証拠（除外証拠）**: 容疑者Bが犯人でないことを示す証拠
   - 例：容疑者Bのアリバイを裏付ける第三者の証言記録

3. **第3の証拠（決定的証拠）**: 容疑者C（真犯人）の犯行を示す証拠
   - 例：犯人しか知りえない情報、凶器に残された痕跡、決定的な矛盾の証明

## 要求
- 証拠数: 3個（必須）
- 各証拠は異なるPOIに配置
- 証拠の重要度: critical(1個：決定的証拠), important(2個：除外証拠)
- 論理的に推理可能な構成にする

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
                
                # Gemini APIで証拠生成  
                if self.gemini_api_key:
                    logger.info("Using Gemini API for evidence generation")
                    response = await self._call_gemini_api(prompt)
                    json_str = self._clean_json_response(response)
                    evidence_data = json.loads(json_str)
                else:
                    # APIキーがない場合はモックを使用
                    logger.info("No API key, using mock evidence data")
                    evidence_data = {
                    "evidence": [
                        {
                            "name": "血痕の付いた花瓶",
                            "description": "コミュニティセンター会議室の床に落ちていた陶製の花瓶。被害者の血液と複数人の指紋が付着している。",
                            "discovery_text": "会議室の床に散らばった花瓶の破片を発見した。底の部分に血痕があり、持ち手部分には複数の指紋が確認できる。田中、佐藤、鈴木の指紋が全て検出された...",
                            "importance": "critical",
                            "poi_name": poi_list[0]["name"] if poi_list else "近所の公園",
                            "related_character": "全容疑者",
                            "clue_text": "全員の指紋があるため、まだ犯人を特定できない"
                        },
                        {
                            "name": "破れた騒音苦情書",
                            "description": "ゴミ箱から発見された、田中直筆の騒音苦情書。山田に対する強い怒りの言葉が書かれ、最後に「もう我慢の限界だ」と記されている。",
                            "discovery_text": "ゴミ箱の中から破り捨てられた苦情書を発見した。田中の直筆で書かれており、山田への激しい怒りと「今夜話し合いに行く」という予告が記されている...",
                            "importance": "important", 
                            "poi_name": poi_list[1]["name"] if len(poi_list) > 1 else "ニュータウン広場",
                            "related_character": "田中太郎",
                            "clue_text": "田中が事件当夜に山田と会う予定だったことを示す"
                        },
                        {
                            "name": "防犯カメラの映像",
                            "description": "会議終了後の映像記録。佐藤と鈴木は8時45分に帰宅、田中のみ9時まで残り、その後会議室へ向かう姿が記録されている。",
                            "discovery_text": "防犯カメラの映像を詳しく分析すると、他の参加者は早めに帰宅しているが、田中だけが最後まで残り、一人で会議室に向かっている決定的な瞬間が記録されていた...",
                            "importance": "critical",
                            "poi_name": poi_list[2]["name"] if len(poi_list) > 2 else "港北ニュータウン駅",
                            "related_character": "田中太郎",
                            "clue_text": "他の容疑者にはアリバイがあり、田中のみが犯行可能時間に現場にいた"
                        }
                    ]
                }
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
                    timeout=get_settings().api.scenario_generation_timeout if hasattr(get_settings().api, 'scenario_generation_timeout') else 30
                )
                
                json_str = self._clean_json_response(response.text)
                reaction_data = json.loads(json_str)
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