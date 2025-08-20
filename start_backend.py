#!/usr/bin/env python3
"""
シンプルなバックエンドサーバー起動スクリプト
Gemini API統合デモ用
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# パスを設定
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

app = FastAPI(
    title="AIミステリー散歩 API",
    description="GPS連動のAI生成ミステリーゲームAPI",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "message": "AIミステリー散歩 API",
        "version": "1.0.0",
        "status": "running",
        "gemini_api": "integrated",
        "features": [
            "real_gemini_api",
            "google_maps_integration", 
            "scenario_generation",
            "evidence_placement",
            "mystery_solving"
        ]
    }

@app.get("/health")
async def health_check():
    """詳細ヘルスチェック"""
    from backend.src.config.secrets import get_api_key, validate_required_secrets
    
    # APIキー検証
    secrets_validation = validate_required_secrets()
    
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "gemini": "available" if secrets_validation.get('GEMINI_API_KEY', False) else "unavailable",
            "google_maps": "available" if secrets_validation.get('GOOGLE_MAPS_API_KEY', False) else "unavailable",
            "firestore": "mocked",
            "environment": os.getenv('ENV', 'development')
        }
    }

@app.post("/api/v1/game/start")
async def start_game_demo(request: Request):
    """デモ用ゲーム開始エンドポイント - 直接Gemini API使用"""
    import google.generativeai as genai
    import json
    from fastapi import Request
    from backend.src.config.secrets import get_api_key
    
    try:
        # リクエストデータを取得
        body = await request.body()
        request_data = json.loads(body.decode()) if body else {}
        
        # 場所とプロンプト情報を決定
        location = request_data.get('location', {})
        difficulty = request_data.get('difficulty', 'normal')
        
        # 場所に応じたプロンプトを生成
        location_prompts = {
            'shin-yokohama': {
                'name': '新横浜駅',
                'context': '新横浜駅周辺の商業・オフィス地区。新幹線駅として多くの人が行き交う繁華街',
                'features': '新幹線、駅ビル、ホテル、アリーナなど'
            },
            'shibuya': {
                'name': '渋谷駅',
                'context': '渋谷駅周辺の繁華街。若者文化の発信地として賑やかな商業エリア',
                'features': 'スクランブル交差点、センター街、ハチ公前、109など'
            },
            'tokyo': {
                'name': '東京駅',
                'context': '東京駅周辺の丸の内オフィス街。皇居に近い格式高いビジネス地区',
                'features': '丸の内ビル群、皇居、東京駅、高級ホテルなど'
            }
        }
        
        # カスタム場所対応
        if location.get('name') and location.get('context'):
            # カスタム場所が設定されている場合
            location_info = {
                'name': location.get('name'),
                'context': location.get('context'),
                'features': f'{location.get("name")}の特色と周辺環境'
            }
            location_key = 'custom'
            print(f"DEBUG: カスタム場所を使用 - {location_info['name']}")
        else:
            # 座標による場所判定
            location_key = 'shin-yokohama'
            if location.get('lat') == 35.6580:  # 渋谷
                location_key = 'shibuya'
            elif location.get('lat') == 35.6762:  # 東京
                location_key = 'tokyo'
            elif location.get('lat') == 35.5070:  # 新横浜
                location_key = 'shin-yokohama'
            
            location_info = location_prompts[location_key]
        
        print(f"DEBUG: 選択された場所 = {location_info['name']}, 難易度 = {difficulty}")
        
        # Gemini API設定
        api_key = get_api_key('gemini')
        if not api_key:
            raise Exception("Gemini APIキーが設定されていません")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # 動的シナリオ生成プロンプト
        prompt = f"""
あなたは優秀な推理小説作家です。{location_info['name']}周辺を舞台にしたミステリーシナリオを作成してください。

## 条件設定
- 場所: {location_info['context']}
- 難易度: {difficulty}
- 容疑者数: 4名
- {location_info['name']}の特徴（{location_info['features']}）を活かす

## 出力形式（必ずJSON形式で出力）
{{
  "title": "事件のタイトル",
  "description": "導入文（300字程度、ドラマチック）",
  "victim": {{
    "name": "被害者名",
    "age": 年齢,
    "occupation": "職業",
    "personality": "性格・特徴"
  }},
  "suspects": [
    {{
      "name": "容疑者名",
      "age": 年齢,
      "occupation": "職業",
      "personality": "性格・特徴",
      "relationship": "被害者との関係",
      "alibi": "アリバイ",
      "motive": "動機"
    }}
  ],
  "culprit": "真犯人の名前",
  "motive": "真の犯行動機",
  "method": "犯行手口",
  "timeline": ["時系列1", "時系列2", "時系列3"]
}}

{location_info['name']}の特徴を活かしたリアルなシナリオを生成してください。
"""
        
        # Gemini APIでシナリオ生成
        print(f"DEBUG: Gemini APIにプロンプト送信中...")
        print(f"DEBUG: プロンプト抜粋 - 場所: {location_info['name']}, 難易度: {difficulty}")
        
        response = model.generate_content(prompt)
        
        if not response.text:
            raise Exception("Gemini APIからレスポンスがありませんでした")
        
        print(f"DEBUG: Gemini API レスポンス長: {len(response.text)} 文字")
        print(f"DEBUG: レスポンス最初の200文字: {response.text[:200]}...")
        
        # レスポンステキストから JSON を抽出
        response_text = response.text.strip()
        
        # JSONブロックを探す（```json ブロックの場合）
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            if json_end != -1:
                response_text = response_text[json_start:json_end].strip()
                print(f"DEBUG: JSONブロック抽出成功")
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            if json_end != -1:
                response_text = response_text[json_start:json_end].strip()
                print(f"DEBUG: コードブロック抽出成功")
        else:
            print(f"DEBUG: コードブロックなし、レスポンス全体をJSON解析")
        
        print(f"DEBUG: 解析対象JSON長: {len(response_text)} 文字")
        
        try:
            scenario_data = json.loads(response_text)
            print(f"DEBUG: JSON解析成功 - タイトル: {scenario_data.get('title', 'N/A')}")
            print(f"DEBUG: 容疑者数: {len(scenario_data.get('suspects', []))}名")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON解析失敗 - {str(e)}")
            print(f"DEBUG: フォールバックシナリオを使用（場所: {location_key}）")
            # JSON形式でない場合のフォールバック（場所に応じて動的生成）
            fallback_scenarios = {
                'shin-yokohama': {
                    "title": "新横浜発最終便の謎",
                    "description": "新横浜駅で起きた不可解な事件。新幹線の発車を前に真相を解明せよ。"
                },
                'shibuya': {
                    "title": "渋谷スクランブル交差点の秘密",
                    "description": "渋谷の喧騒の中で起きた謎めいた事件。ハチ公前広場に隠された真実とは。"
                },
                'tokyo': {
                    "title": "東京駅丸の内の陰謀", 
                    "description": "格式高い丸の内ビジネス地区で発生した事件。皇居を望む高層ビルに潜む暗闇。"
                },
                'custom': {
                    "title": f"{location_info['name']}の謎",
                    "description": f"{location_info['name']}で起きた不可解な事件。この土地に隠された秘密とは。"
                }
            }
            
            fallback = fallback_scenarios.get(location_key, fallback_scenarios['shin-yokohama'])
            
            scenario_data = {
                "title": fallback["title"],
                "description": fallback["description"],
                "victim": {
                    "name": "田中太郎",
                    "age": 45,
                    "occupation": "会社員",
                    "personality": "真面目で几帳面"
                },
                "suspects": [
                    {"name": "佐藤花子", "age": 35, "occupation": "同僚", "personality": "野心的", "relationship": "同僚", "alibi": "会議中", "motive": "昇進への嫉妬"},
                    {"name": "鈴木一郎", "age": 50, "occupation": "上司", "personality": "厳格", "relationship": "上司", "alibi": "出張中", "motive": "隠し事の発覚を恐れて"},
                    {"name": "高橋美咲", "age": 28, "occupation": "秘書", "personality": "内向的", "relationship": "秘書", "alibi": "書類整理", "motive": "パワハラへの恨み"},
                    {"name": "山田健二", "age": 42, "occupation": "取引先", "personality": "短気", "relationship": "取引先", "alibi": "別の会議", "motive": "契約トラブル"}
                ],
                "culprit": "佐藤花子",
                "motive": "昇進を阻まれたことへの恨み",
                "method": "毒物を使った犯行",
                "timeline": ["午前9時: 被害者出社", "午前10時: 容疑者たちとの会議", "午前11時: 事件発生"]
            }
        
        # 証拠データ（場所に応じて動的生成）
        evidence_templates = {
            'shin-yokohama': [
                {"name": "血痕の付いたハンカチ", "poi_name": "新横浜駅構内カフェ", "lat": 35.5070, "lng": 139.6176},
                {"name": "破れた名刺", "poi_name": "新横浜プリンスホテル", "lat": 35.5080, "lng": 139.6186},
                {"name": "謎の鍵", "poi_name": "新横浜アリーナ", "lat": 35.5090, "lng": 139.6196}
            ],
            'shibuya': [
                {"name": "割れたスマートフォン", "poi_name": "渋谷スクランブル交差点", "lat": 35.6580, "lng": 139.7016},
                {"name": "血痕のある領収書", "poi_name": "渋谷109", "lat": 35.6590, "lng": 139.7026},
                {"name": "怪しいメモ", "poi_name": "ハチ公前広場", "lat": 35.6600, "lng": 139.7036}
            ],
            'tokyo': [
                {"name": "高級万年筆", "poi_name": "東京駅丸の内口", "lat": 35.6762, "lng": 139.6503},
                {"name": "機密書類の一部", "poi_name": "丸の内ビルディング", "lat": 35.6772, "lng": 139.6513},
                {"name": "謎の会員証", "poi_name": "皇居東御苑", "lat": 35.6851, "lng": 139.7544}
            ],
            'custom': [
                {"name": "謎の手がかり", "poi_name": f"{location_info['name']}中央部", "lat": location.get('lat', 35.0), "lng": location.get('lng', 135.0)},
                {"name": "重要な証拠品", "poi_name": f"{location_info['name']}周辺施設", "lat": location.get('lat', 35.0) + 0.001, "lng": location.get('lng', 135.0) + 0.001},
                {"name": "決定的証拠", "poi_name": f"{location_info['name']}近郊", "lat": location.get('lat', 35.0) + 0.002, "lng": location.get('lng', 135.0) + 0.002}
            ]
        }
        
        evidence_list = evidence_templates.get(location_key, evidence_templates['shin-yokohama'])
        evidence = []
        for i, ev in enumerate(evidence_list, 1):
            evidence.append({
                "evidence_id": f"evidence_{i}",
                "name": ev["name"],
                "importance": "critical" if i == 1 else "important",
                "poi_name": ev["poi_name"],
                "location": {"lat": ev["lat"], "lng": ev["lng"]}
            })
        
        return {
            "game_id": "demo-game-12345",
            "scenario": scenario_data,
            "evidence": evidence,
            "game_rules": {
                "discovery_radius": 50.0,
                "time_limit": 3600,
                "max_evidence": len(evidence)
            }
        }
        
    except Exception as e:
        from fastapi import HTTPException
        import traceback
        error_detail = f"シナリオ生成エラー: {str(e)}"
        print(f"ERROR: {error_detail}")
        print(f"Traceback: {traceback.format_exc()}")
        
        raise HTTPException(status_code=500, detail={
            "error": {
                "code": "SCENARIO_GENERATION_FAILED",
                "message": error_detail
            }
        })

if __name__ == "__main__":
    print("🚀 AIミステリー散歩 バックエンドサーバー起動中...")
    print("📍 アクセス: http://localhost:8080")
    print("📊 API docs: http://localhost:8080/docs") 
    print("🔍 ヘルスチェック: http://localhost:8080/health")
    print("🎮 Web Demo: file:///mnt/c/docker/detective-anywhere/web-demo.html")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")