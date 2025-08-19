"""
AIミステリー散歩 - メインモジュール
GPS連動のAI生成ミステリーゲーム
"""

from typing import Dict, Any


class DetectiveAnywhere:
    """AIミステリー散歩メインクラス"""
    
    def __init__(self):
        self.name = "AIミステリー散歩"
        self.version = "1.0.0"
    
    def get_project_info(self) -> Dict[str, Any]:
        """プロジェクト情報を取得"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "GPS連動のAI生成ミステリーゲーム",
            "features": [
                "AI生成シナリオ",
                "GPS連動証拠発見",
                "リアルタイム推理",
                "キャラクター反応"
            ],
            "tech_stack": [
                "FastAPI",
                "Gemini AI",
                "Google Cloud",
                "Flutter"
            ]
        }