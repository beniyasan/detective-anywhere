"""
推理判定関連APIルーター
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.game_service import game_service
from shared.models.game import DeductionRequest, DeductionResult, GameScore
from shared.models.character import CharacterReaction
from ..errors import APIError, GameAPIError


router = APIRouter()


# レスポンスモデル
class DeductionSubmitResponse(BaseModel):
    """推理提出レスポンス"""
    correct: bool
    culprit: str
    reactions: List[CharacterReaction]
    game_completed: bool
    score: GameScore
    explanation: Optional[str]


class SuspectListResponse(BaseModel):
    """容疑者リストレスポンス"""
    game_id: str
    suspects: List[dict]
    victim: dict


@router.post("/submit", response_model=DeductionSubmitResponse)
async def submit_deduction(request: DeductionRequest) -> DeductionSubmitResponse:
    """
    推理回答を提出して判定
    
    - プレイヤーが推理した犯人名を判定
    - 正誤に応じたキャラクター反応を生成
    - ゲームを完了状態にして最終スコアを算出
    """
    
    try:
        # 推理判定処理
        result = await game_service.submit_deduction(request)
        
        return DeductionSubmitResponse(
            correct=result.correct,
            culprit=result.culprit,
            reactions=result.reactions,
            game_completed=result.game_completed,
            score=result.score,
            explanation=result.explanation
        )
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise APIError.internal_server_error(
            code="DEDUCTION_FAILED",
            message="推理判定処理に失敗しました",
            details=str(e)
        )

@router.post("/question")
async def ask_suspect_question(request: dict):
    """
    容疑者に質問を行う（フロントエンド互換性のため）
    
    - game_id: ゲームID
    - suspect_name: 質問対象の容疑者名
    - question_type: 質問タイプ
    """
    from ..errors import APIError
    
    try:
        game_id = request.get("game_id")
        suspect_name = request.get("suspect_name") 
        question_type = request.get("question_type")
        
        if not game_id or not suspect_name or not question_type:
            raise ValueError("game_id, suspect_name, question_type は必須です")
        
        # ゲーム情報を取得
        game_session = await game_service.get_game_session(game_id)
        if not game_session:
            raise ValueError("ゲームが見つかりません")
        
        # 容疑者情報を取得
        suspect = None
        for s in game_session.scenario.suspects:
            if s.name == suspect_name:
                suspect = s
                break
                
        if not suspect:
            raise ValueError("指定された容疑者が見つかりません")
        
        # 質問タイプに応じた回答を生成
        if question_type == "alibi":
            response_text = f"{suspect.alibi}について詳しくお話しします。"
        elif question_type == "relationship":
            response_text = f"被害者との関係は{suspect.relationship}でした。"
        elif question_type == "motive":
            response_text = f"動機については...まあ、それは言いたくありませんね。"
        else:
            response_text = f"{suspect.name}として、その質問には答えられません。"
        
        return {
            "suspect_name": suspect_name,
            "question_type": question_type,
            "response": response_text,
            "temperament": suspect.temperament.value
        }
        
    except ValueError as e:
        raise APIError.bad_request(message=str(e))
    except Exception as e:
        raise APIError.internal_server_error(message=f"質問処理に失敗: {str(e)}")


@router.get("/{game_id}/suspects", response_model=SuspectListResponse)
async def get_suspects_list(game_id: str) -> SuspectListResponse:
    """
    容疑者リストを取得
    
    - 推理パートで表示する容疑者一覧
    - 各容疑者の基本情報とアリバイ
    """
    
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    suspects_info = []
    for suspect in game_session.scenario.suspects:
        suspects_info.append({
            "name": suspect.name,
            "age": suspect.age,
            "occupation": suspect.occupation,
            "personality": suspect.personality,
            "relationship": suspect.relationship,
            "alibi": suspect.alibi,
            "temperament": suspect.temperament.value
        })
    
    victim_info = {
        "name": game_session.scenario.victim.name,
        "age": game_session.scenario.victim.age,
        "occupation": game_session.scenario.victim.occupation,
        "background": game_session.scenario.victim.background
    }
    
    return SuspectListResponse(
        game_id=game_id,
        suspects=suspects_info,
        victim=victim_info
    )


@router.get("/{game_id}/summary")
async def get_case_summary(game_id: str) -> Dict[str, Any]:
    """
    事件の要約情報を取得
    
    - 推理前に確認できる事件情報
    - 発見済み証拠の概要
    """
    
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    # 発見済み証拠の情報
    discovered_evidence = []
    for evidence_id in game_session.discovered_evidence:
        evidence = next(
            (ev for ev in game_session.evidence_list if ev.evidence_id == evidence_id),
            None
        )
        if evidence:
            discovered_evidence.append({
                "name": evidence.name,
                "description": evidence.description,
                "importance": evidence.importance.value,
                "poi_name": evidence.poi_name,
                "related_character": evidence.related_character
            })
    
    return {
        "game_id": game_id,
        "case_title": game_session.scenario.title,
        "case_description": game_session.scenario.description,
        "victim": {
            "name": game_session.scenario.victim.name,
            "occupation": game_session.scenario.victim.occupation
        },
        "discovered_evidence_count": len(discovered_evidence),
        "total_evidence_count": len(game_session.evidence_list),
        "discovered_evidence": discovered_evidence,
        "timeline": game_session.scenario.timeline,
        "game_progress": {
            "completion_rate": game_session.progress.completion_rate,
            "time_elapsed": game_session.progress.time_elapsed
        }
    }


@router.get("/{game_id}/analysis-help")
async def get_analysis_help(game_id: str) -> Dict[str, Any]:
    """
    推理分析のヒントを提供
    
    - 発見した証拠の関連性
    - 容疑者の矛盾点の示唆
    - ただし、直接的な答えは教えない
    """
    
    game_session = await game_service.get_game_session(game_id)
    
    if not game_session:
        raise GameAPIError.game_not_found(game_id)
    
    # 発見済み証拠から分析ヒントを生成
    discovered_evidence = []
    critical_evidence_found = False
    
    for evidence_id in game_session.discovered_evidence:
        evidence = next(
            (ev for ev in game_session.evidence_list if ev.evidence_id == evidence_id),
            None
        )
        if evidence:
            discovered_evidence.append(evidence)
            if evidence.is_critical:
                critical_evidence_found = True
    
    analysis_tips = []
    
    # 証拠発見状況に応じたヒント
    if len(discovered_evidence) < 2:
        analysis_tips.append("まずはもっと多くの証拠を集めましょう。")
    elif not critical_evidence_found:
        analysis_tips.append("決定的な証拠がまだ見つかっていないようです。")
    else:
        analysis_tips.append("重要な証拠が揃ってきました。各容疑者のアリバイと証拠を照らし合わせてみてください。")
    
    # 関連キャラクターの分析
    character_mentions = {}
    for evidence in discovered_evidence:
        if evidence.related_character:
            character_mentions[evidence.related_character] = character_mentions.get(evidence.related_character, 0) + 1
    
    if character_mentions:
        most_mentioned = max(character_mentions, key=character_mentions.get)
        analysis_tips.append(f"{most_mentioned}に関する証拠が多く見つかっています。")
    
    # ミスリード証拠の警告
    misleading_count = sum(1 for ev in discovered_evidence if ev.is_misleading)
    if misleading_count > 0:
        analysis_tips.append("一部の証拠は真実から目をそらすものかもしれません。慎重に判断してください。")
    
    return {
        "game_id": game_id,
        "analysis_tips": analysis_tips,
        "evidence_summary": {
            "total_found": len(discovered_evidence),
            "critical_found": sum(1 for ev in discovered_evidence if ev.is_critical),
            "important_found": sum(1 for ev in discovered_evidence if ev.importance.value == "important"),
            "misleading_found": misleading_count
        },
        "character_focus": character_mentions,
        "ready_for_deduction": len(discovered_evidence) >= 3 and critical_evidence_found
    }