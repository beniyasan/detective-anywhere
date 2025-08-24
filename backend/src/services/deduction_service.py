"""
推理フェーズのサービス
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from ..services.ai_service import ai_service
from ..services.database_service import database_service
from ...shared.models.game import GameSession, GameStatus
from ...shared.models.scenario import Scenario

logger = logging.getLogger(__name__)


class DeductionService:
    """推理フェーズのサービス"""
    
    def __init__(self):
        self.max_questions_per_game = 10  # ゲームごとの最大質問回数
        self.question_history = {}  # ゲームごとの質問履歴
        
    async def ask_suspect_question(
        self,
        game_id: str,
        suspect_name: str,
        question_type: str,
        custom_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        容疑者に質問する
        
        Args:
            game_id: ゲームID
            suspect_name: 容疑者名
            question_type: 質問タイプ
            custom_question: カスタム質問文
            
        Returns:
            質問と回答の結果
        """
        
        # ゲームセッション取得
        game_session = await database_service.get_game_session(game_id)
        if not game_session:
            raise ValueError(f"ゲームが見つかりません: {game_id}")
        
        # 質問履歴の確認
        if game_id not in self.question_history:
            self.question_history[game_id] = []
        
        questions_asked = len(self.question_history[game_id])
        if questions_asked >= self.max_questions_per_game:
            raise ValueError(f"質問回数の上限({self.max_questions_per_game}回)に達しています")
        
        # シナリオから容疑者情報を取得
        scenario = game_session.get("scenario", {})
        suspects = scenario.get("suspects", [])
        suspect = next((s for s in suspects if s["name"] == suspect_name), None)
        
        if not suspect:
            raise ValueError(f"容疑者が見つかりません: {suspect_name}")
        
        # 真犯人かどうか確認
        is_culprit = suspect_name == scenario.get("culprit")
        
        # 質問文の生成
        question = self._generate_question_text(question_type, custom_question)
        
        # AIで容疑者の回答を生成
        answer_data = await self._generate_suspect_answer(
            suspect=suspect,
            question=question,
            question_type=question_type,
            is_culprit=is_culprit,
            scenario=scenario
        )
        
        # 質問履歴に追加
        self.question_history[game_id].append({
            "suspect": suspect_name,
            "question": question,
            "answer": answer_data["answer"],
            "timestamp": datetime.now().isoformat()
        })
        
        # ゲームセッション更新
        await database_service.update_game_session(game_id, {
            "question_count": questions_asked + 1,
            "last_question_time": datetime.now()
        })
        
        return {
            "suspect_name": suspect_name,
            "question": question,
            "answer": answer_data["answer"],
            "reaction": answer_data["reaction"],
            "is_lying": answer_data.get("is_lying", False),
            "hint_revealed": answer_data.get("hint"),
            "questions_remaining": self.max_questions_per_game - questions_asked - 1
        }
    
    async def submit_deduction(
        self,
        game_id: str,
        player_id: str,
        culprit_guess: str,
        motive_guess: str,
        method_guess: Optional[str] = None,
        evidence_reasoning: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        推理を提出して判定する
        
        Args:
            game_id: ゲームID
            player_id: プレイヤーID
            culprit_guess: 犯人の推理
            motive_guess: 動機の推理
            method_guess: 犯行手口の推理
            evidence_reasoning: 証拠と推理の関連付け
            
        Returns:
            推理結果とスコア
        """
        
        # ゲームセッション取得
        game_session = await database_service.get_game_session(game_id)
        if not game_session:
            raise ValueError(f"ゲームが見つかりません: {game_id}")
        
        scenario = game_session.get("scenario", {})
        true_culprit = scenario.get("culprit")
        true_motive = scenario.get("motive", "")
        true_method = scenario.get("method", "")
        
        # 正解判定
        culprit_correct = culprit_guess == true_culprit
        motive_similarity = self._calculate_motive_similarity(motive_guess, true_motive)
        motive_correct = motive_similarity > 0.7  # 70%以上の類似度で正解
        
        # スコア計算
        score_details = self._calculate_score(
            game_session=game_session,
            culprit_correct=culprit_correct,
            motive_correct=motive_correct,
            questions_asked=len(self.question_history.get(game_id, []))
        )
        
        # 真相の文章生成
        full_story = await self._generate_full_story(scenario)
        
        # ゲーム完了処理
        await database_service.update_game_session(game_id, {
            "status": "completed",
            "completed_at": datetime.now(),
            "final_score": score_details["total_score"],
            "culprit_guessed": culprit_guess,
            "culprit_correct": culprit_correct,
            "motive_correct": motive_correct
        })
        
        # ゲーム履歴保存
        await database_service.save_game_history(
            f"{game_id}_history",
            {
                "game_id": game_id,
                "player_id": player_id,
                "title": scenario.get("title", "Unknown Mystery"),
                "completed_at": datetime.now(),
                "score": score_details["total_score"],
                "culprit_correct": culprit_correct,
                "motive_correct": motive_correct,
                "difficulty": game_session.get("difficulty", "normal"),
                "duration": self._calculate_game_duration(game_session)
            }
        )
        
        return {
            "is_correct": culprit_correct and motive_correct,
            "culprit_correct": culprit_correct,
            "motive_correct": motive_correct,
            "base_score": score_details["base_score"],
            "evidence_bonus": score_details["evidence_bonus"],
            "question_efficiency_bonus": score_details["question_efficiency_bonus"],
            "time_bonus": score_details["time_bonus"],
            "total_score": score_details["total_score"],
            "true_culprit": true_culprit,
            "true_motive": true_motive,
            "true_method": true_method,
            "full_story": full_story,
            "rank": None,  # TODO: ランキング実装
            "high_score": score_details["total_score"] > 800
        }
    
    async def generate_hint(
        self,
        game_id: str,
        hint_level: int = 1
    ) -> Dict[str, Any]:
        """
        ヒントを生成する
        
        Args:
            game_id: ゲームID
            hint_level: ヒントレベル（1-3）
            
        Returns:
            ヒントと減点情報
        """
        
        # ゲームセッション取得
        game_session = await database_service.get_game_session(game_id)
        if not game_session:
            raise ValueError(f"ゲームが見つかりません: {game_id}")
        
        scenario = game_session.get("scenario", {})
        discovered_evidence = game_session.get("discovered_evidence", [])
        
        # ヒントレベルに応じた内容生成
        hint = ""
        score_penalty = 0
        
        if hint_level == 1:
            # 軽いヒント
            hint = self._generate_light_hint(scenario, discovered_evidence)
            score_penalty = 50
        elif hint_level == 2:
            # 重要なヒント
            hint = self._generate_important_hint(scenario, discovered_evidence)
            score_penalty = 100
        elif hint_level == 3:
            # 決定的ヒント
            hint = self._generate_critical_hint(scenario)
            score_penalty = 200
        else:
            raise ValueError(f"無効なヒントレベル: {hint_level}")
        
        # ヒント使用履歴更新
        hints_used = game_session.get("hints_used", [])
        hints_used.append({
            "level": hint_level,
            "timestamp": datetime.now().isoformat(),
            "penalty": score_penalty
        })
        
        await database_service.update_game_session(game_id, {
            "hints_used": hints_used,
            "hint_penalty_total": sum(h["penalty"] for h in hints_used)
        })
        
        return {
            "hint": hint,
            "hint_level": hint_level,
            "score_penalty": score_penalty,
            "next_hint_available": hint_level < 3
        }
    
    async def get_deduction_status(self, game_id: str) -> Dict[str, Any]:
        """
        推理フェーズの状態を取得
        
        Args:
            game_id: ゲームID
            
        Returns:
            推理フェーズの状態情報
        """
        
        game_session = await database_service.get_game_session(game_id)
        if not game_session:
            raise ValueError(f"ゲームが見つかりません: {game_id}")
        
        questions_asked = len(self.question_history.get(game_id, []))
        hints_used = game_session.get("hints_used", [])
        discovered_evidence = game_session.get("discovered_evidence", [])
        evidence_list = game_session.get("evidence_list", [])
        
        return {
            "game_id": game_id,
            "questions_asked": questions_asked,
            "questions_remaining": self.max_questions_per_game - questions_asked,
            "hints_used": len(hints_used),
            "hint_penalty_total": sum(h.get("penalty", 0) for h in hints_used),
            "evidence_discovered": len(discovered_evidence),
            "evidence_total": len(evidence_list),
            "discovery_rate": len(discovered_evidence) / len(evidence_list) if evidence_list else 0,
            "ready_for_deduction": len(discovered_evidence) >= 3,
            "game_duration": self._calculate_game_duration(game_session)
        }
    
    # プライベートメソッド
    def _generate_question_text(self, question_type: str, custom_question: Optional[str]) -> str:
        """質問文を生成"""
        if custom_question:
            return custom_question
        
        question_templates = {
            "alibi": "事件当時、あなたはどこで何をしていましたか？",
            "motive": "被害者との関係について教えてください。何か問題はありましたか？",
            "relationship": "被害者とはどのような関係でしたか？",
            "witness": "他の人の行動で気になったことはありませんか？",
            "behavior": "事件当日の行動について詳しく教えてください。"
        }
        
        return question_templates.get(question_type, "何か知っていることを教えてください。")
    
    async def _generate_suspect_answer(
        self,
        suspect: Dict[str, Any],
        question: str,
        question_type: str,
        is_culprit: bool,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AIで容疑者の回答を生成"""
        
        prompt = f"""
以下の容疑者として質問に答えてください。

容疑者情報:
- 名前: {suspect['name']}
- 年齢: {suspect['age']}
- 職業: {suspect['occupation']}
- 性格: {suspect['personality']}
- 被害者との関係: {suspect['relationship']}
- アリバイ: {suspect.get('alibi', '不明')}
- 真犯人かどうか: {'はい' if is_culprit else 'いいえ'}

事件の真相:
- 真犯人: {scenario.get('culprit')}
- 真の動機: {scenario.get('motive', '不明')}

質問: {question}

回答ガイドライン:
1. キャラクターの性格に合った話し方をする
2. 真犯人の場合は巧妙に嘘を混ぜる（ただし矛盾は作る）
3. 無実の場合は基本的に正直に答える
4. 感情的な反応も含める

JSON形式で回答:
{{
  "answer": "質問への回答（100-200字）",
  "reaction": "態度や表情の描写（50字程度）",
  "is_lying": true/false,
  "hint": "プレイヤーへのヒント（オプション）"
}}
"""
        
        try:
            response = await ai_service.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONブロックを抽出
            if "```json" in response_text:
                json_start = response_text.index("```json") + 7
                json_end = response_text.index("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            answer_data = json.loads(response_text)
            return answer_data
            
        except Exception as e:
            logger.error(f"容疑者回答生成エラー: {e}")
            # フォールバック回答
            return {
                "answer": suspect.get('alibi', 'その時のことはよく覚えていません...'),
                "reaction": "少し困った様子を見せる",
                "is_lying": is_culprit,
                "hint": None
            }
    
    def _calculate_motive_similarity(self, guess: str, truth: str) -> float:
        """動機の類似度を計算（簡易版）"""
        # TODO: より高度な自然言語処理での類似度計算
        guess_lower = guess.lower()
        truth_lower = truth.lower()
        
        # キーワードマッチング
        keywords = ["金", "恨み", "嫉妬", "復讐", "愛", "秘密", "脅迫", "事故"]
        matches = sum(1 for keyword in keywords if keyword in guess_lower and keyword in truth_lower)
        
        # 文字列の部分一致
        if truth_lower in guess_lower or guess_lower in truth_lower:
            return 1.0
        
        return min(matches * 0.3, 1.0)
    
    def _calculate_score(
        self,
        game_session: Dict[str, Any],
        culprit_correct: bool,
        motive_correct: bool,
        questions_asked: int
    ) -> Dict[str, Any]:
        """スコアを計算"""
        
        # 基本スコア
        base_score = 0
        if culprit_correct:
            base_score += 500
        if motive_correct:
            base_score += 300
        
        # 証拠収集ボーナス
        evidence_list = game_session.get("evidence_list", [])
        discovered_evidence = game_session.get("discovered_evidence", [])
        discovery_rate = len(discovered_evidence) / len(evidence_list) if evidence_list else 0
        evidence_bonus = int(discovery_rate * 200)
        
        # 質問効率ボーナス
        question_efficiency_bonus = max(0, (10 - questions_asked) * 20)
        
        # 時間ボーナス
        duration = self._calculate_game_duration(game_session)
        if duration < 600:  # 10分以内
            time_bonus = 100
        elif duration < 1200:  # 20分以内
            time_bonus = 50
        else:
            time_bonus = 0
        
        # ヒント減点
        hint_penalty = game_session.get("hint_penalty_total", 0)
        
        total_score = max(0, base_score + evidence_bonus + question_efficiency_bonus + time_bonus - hint_penalty)
        
        return {
            "base_score": base_score,
            "evidence_bonus": evidence_bonus,
            "question_efficiency_bonus": question_efficiency_bonus,
            "time_bonus": time_bonus,
            "hint_penalty": hint_penalty,
            "total_score": total_score
        }
    
    async def _generate_full_story(self, scenario: Dict[str, Any]) -> str:
        """事件の全容を生成"""
        
        prompt = f"""
以下のミステリーシナリオの真相を、小説風の文章で説明してください。

シナリオ情報:
- タイトル: {scenario.get('title')}
- 被害者: {scenario.get('victim', {}).get('name')}
- 真犯人: {scenario.get('culprit')}
- 動機: {scenario.get('motive')}
- 犯行手口: {scenario.get('method', '不明')}

200-300字で、事件の真相を明らかにする文章を作成してください。
"""
        
        try:
            response = await ai_service.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"真相文章生成エラー: {e}")
            return f"{scenario.get('culprit')}が犯人でした。動機は{scenario.get('motive')}でした。"
    
    def _calculate_game_duration(self, game_session: Dict[str, Any]) -> int:
        """ゲーム時間を計算（秒）"""
        created_at = game_session.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            return 0
        
        return int((datetime.now() - created_at).total_seconds())
    
    def _generate_light_hint(self, scenario: Dict[str, Any], discovered_evidence: List[str]) -> str:
        """軽いヒントを生成"""
        if len(discovered_evidence) < 3:
            return "まずはもっと証拠を集めることをおすすめします。"
        return "すべての容疑者のアリバイを慎重に検討してみてください。"
    
    def _generate_important_hint(self, scenario: Dict[str, Any], discovered_evidence: List[str]) -> str:
        """重要なヒントを生成"""
        suspects = scenario.get("suspects", [])
        if suspects:
            return f"容疑者は{len(suspects)}人います。そのうち1人だけが嘘をついています。"
        return "証拠の中に、犯人を特定する決定的なものがあります。"
    
    def _generate_critical_hint(self, scenario: Dict[str, Any]) -> str:
        """決定的ヒントを生成"""
        culprit = scenario.get("culprit", "不明")
        return f"犯人のイニシャルは「{culprit[0]}」です。動機は個人的な恨みに関係しています。"


# サービスインスタンス
deduction_service = DeductionService()