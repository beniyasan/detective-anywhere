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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
    allow_origins=[
        "https://detective-anywhere-hosting.web.app",
        "https://detective-anywhere-hosting.firebaseapp.com", 
        "http://localhost:8000",
        "http://localhost:5000",  # Firebase serve
        "http://127.0.0.1:8000",
        "*"  # 開発用（本番では削除推奨）
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 静的ファイルディレクトリのマウント
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

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

@app.get("/web-demo.html")
async def serve_web_demo():
    """Web Demo HTMLファイル提供"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "web-demo.html")
    return FileResponse(file_path, media_type="text/html")

@app.get("/mobile-app.html")
async def serve_mobile_app():
    """Mobile App HTMLファイル提供"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "mobile-app.html")
    return FileResponse(file_path, media_type="text/html")

@app.get("/manifest.json")
async def serve_manifest():
    """PWA Manifestファイル提供"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "manifest.json")
    return FileResponse(file_path, media_type="application/json")

@app.get("/service-worker.js")
async def serve_service_worker():
    """Service Workerファイル提供"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "service-worker.js")
    return FileResponse(file_path, media_type="application/javascript")

@app.get("/favicon.ico")
async def serve_favicon():
    """Faviconファイル提供"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "favicon.ico")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/x-icon")
    return {"message": "No favicon"}

@app.post("/api/v1/game/start")
async def start_game_demo(request: Request):
    """デモ用ゲーム開始エンドポイント - 直接Gemini API使用"""
    import google.generativeai as genai
    import json
    from fastapi import Request
    import sys
    import os
    
    # POIサービスのインポートパスを追加（Cloud Run対応）
    backend_src_path = os.path.join(os.path.dirname(__file__), 'backend', 'src')
    if backend_src_path not in sys.path:
        sys.path.append(backend_src_path)
    from services.poi_service import POIService
    from config.secrets import get_api_key
    
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
            # 座標による場所判定（近接判定に変更）
            user_lat = location.get('lat', 35.5070)
            user_lng = location.get('lng', 139.6176)
            
            # 各地点との距離を計算
            def calculate_distance(lat1, lon1, lat2, lon2):
                import math
                R = 6371e3  # 地球の半径（メートル）
                φ1 = lat1 * math.pi / 180
                φ2 = lat2 * math.pi / 180
                Δφ = (lat2 - lat1) * math.pi / 180
                Δλ = (lon2 - lon1) * math.pi / 180
                a = math.sin(Δφ/2) * math.sin(Δφ/2) + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2) * math.sin(Δλ/2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
            
            # 各地点の中心座標
            locations_centers = {
                'shibuya': (35.6580, 139.7016),
                'tokyo': (35.6762, 139.6503),
                'shin-yokohama': (35.5070, 139.6176)
            }
            
            # 最も近い場所を判定（10km以内）
            min_distance = float('inf')
            location_key = 'shin-yokohama'  # デフォルト
            
            for loc_key, (lat, lng) in locations_centers.items():
                distance = calculate_distance(user_lat, user_lng, lat, lng)
                if distance < min_distance and distance < 10000:  # 10km以内
                    min_distance = distance
                    location_key = loc_key
            
            print(f"DEBUG: ユーザー位置 ({user_lat:.4f}, {user_lng:.4f}) から最も近い場所: {location_key} (距離: {min_distance:.0f}m)")
            
            # 距離が5km以上離れている場合は、ユーザーの現在地ベースのカスタムシナリオを生成
            if min_distance > 5000:
                location_info = {
                    'name': '現在地周辺',
                    'context': 'あなたの現在地周辺の街。身近な場所で起きた事件',
                    'features': '地域のランドマーク、商店街、公園などが点在する日常的な風景'
                }
                print(f"DEBUG: 既定の場所が遠いため、現在地周辺のシナリオを生成")
            else:
                location_info = location_prompts[location_key]
        
        print(f"DEBUG: 選択された場所 = {location_info['name']}, 難易度 = {difficulty}")
        
        # Gemini API設定
        api_key = get_api_key('gemini')
        if not api_key:
            raise Exception("Gemini APIキーが設定されていません")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        # 動的シナリオ生成プロンプト（推理要素を強化）
        prompt = f"""
あなたは本格推理小説の巨匠です。論理的に解決可能な緻密なミステリーシナリオを作成してください。

## 条件設定
- 場所: {location_info['context']}
- 難易度: {difficulty}
- 容疑者数: 4名
- {location_info['name']}の特徴（{location_info['features']}）を活かす

## 出力形式（必ずJSON形式で出力）
{{
  "title": "事件のタイトル",
  "description": "事件の導入部分（500-800字程度、ドラマチックで詳細）。事件発生の背景、現場の状況、発見時の様子、初期の調査状況などを含む魅力的な物語として描写",
  "incident_time": "事件発生時刻（例: 22:30）",
  "discovery_time": "発見時刻（例: 23:45）",
  "victim": {{
    "name": "被害者名",
    "age": 年齢,
    "occupation": "職業",
    "personality": "性格・特徴",
    "last_seen": "最後に目撃された時刻と場所（例: 21:30 レストランで食事）"
  }},
  "suspects": [
    {{
      "name": "容疑者名",
      "age": 年齢,
      "occupation": "職業",
      "personality": "性格・特徴",
      "relationship": "被害者との関係",
      "alibi": "具体的な時刻を含むアリバイ（例: 21:00-23:00 バーで友人と飲酒、レシート有）",
      "motive": "動機",
      "contradiction": "アリバイや証言の矛盾点（真犯人のみ）",
      "suspicious_point": "不審な点や行動"
    }}
  ],
  "culprit": "真犯人の名前",
  "true_motive": "真の犯行動機（表面的な動機とは異なる深い理由）",
  "method": "詳細な犯行手口と使用された凶器",
  "trick": "犯人が使ったトリックや偽装工作（アリバイ工作など）",
  "timeline": [
    "20:00 - 被害者が現場付近に到着",
    "21:00 - 容疑者Aと被害者が口論（目撃者あり）",
    "22:00 - 容疑者Bが被害者と電話（通話記録あり）",
    "22:30 - 推定犯行時刻",
    "23:45 - 遺体発見"
  ],
  "key_evidence": [
    "決定的な物的証拠とその意味",
    "重要な証言の矛盾",
    "見落としやすい状況証拠"
  ],
  "resolution_logic": "犯人を論理的に特定する推理の道筋（プレイヤーへのヒント）"
}}

## 重要な要件
1. **導入文（description）**:
   - 500-800字で詳細に描写
   - 事件現場の雰囲気（天気、時間帯、環境音など）
   - 発見者の心境と現場の第一印象
   - 警察到着時の状況
   - 読者を物語に引き込む文学的な表現を使用
   
2. **推理要素**:
   - アリバイには必ず具体的な時刻（21:00-23:00など）を含める
   - 真犯人のアリバイには巧妙だが見破れる矛盾を仕込む
   - 他の容疑者にも動機を持たせてミスリードを誘う
   - タイムラインは詳細で、事件の流れが明確に分かるようにする
   - 証拠と証言から論理的に真犯人を特定できるようにする
   - トリックは現実的で、実行可能なものにする

{location_info['name']}の特徴を活かした本格推理シナリオを生成してください。
導入文は推理小説の冒頭のように、読者を事件の世界に没入させる魅力的な文章にしてください。
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
        
        # シナリオに関連した証拠を動的に生成
        # 基本的な証拠テンプレート（シナリオの内容に応じて詳細が変わる）
        evidence_templates_by_location = {
            'shin-yokohama': [
                {
                    "name": "血痕の付いたハンカチ",
                    "description": f"高級ブランドのハンカチに血痕が付着。イニシャルの刺繍があり、{scenario_data.get('culprit', '誰か')}と関連がありそう。",
                    "hint": "イニシャルと容疑者の名前を照合してみよう。真犯人は偽装している可能性もある。",
                    "importance": "critical",
                    "related_to": "犯人の所持品または偽装工作"
                },
                {
                    "name": "破れた名刺",
                    "description": f"半分に破れた名刺。時刻「{scenario_data.get('incident_time', '22:30')}」と誰かの電話番号が書かれている。",
                    "hint": "この時刻は事件発生時刻と一致する。誰との約束だったのか？",
                    "importance": "important",
                    "related_to": "アリバイの矛盾を示す証拠"
                },
                {
                    "name": "レシートまたは切符",
                    "description": f"事件当夜のレシート。時刻は{scenario_data.get('incident_time', '22:30')}の30分前。購入品から誰かの行動が推測できる。",
                    "hint": "購入時刻と場所から、誰かのアリバイが崩れるかもしれない。",
                    "importance": "important",
                    "related_to": "アリバイ検証の証拠"
                }
            ],
            'shibuya': [
                {
                    "name": "割れたスマートフォン",
                    "description": "画面が割れたスマートフォン。最後の通話履歴が残っている。",
                    "hint": "通話履歴から被害者の最後の行動が分かるかもしれない。",
                    "importance": "critical"
                },
                {
                    "name": "血痕のある領収書",
                    "description": "カフェの領収書に血痕が付着。時刻は事件発生の30分前。",
                    "hint": "誰かと一緒にいた証拠かもしれない。",
                    "importance": "important"
                },
                {
                    "name": "怪しいメモ",
                    "description": "急いで書かれたようなメモ。「23:00 裏口」と読める。",
                    "hint": "密会の約束だったのだろうか。",
                    "importance": "important"
                }
            ],
            'tokyo': [
                {
                    "name": "高級万年筆",
                    "description": "限定品の万年筆。インクが最近補充されたばかり。",
                    "hint": "この万年筆で何か重要な書類にサインされた可能性がある。",
                    "importance": "critical"
                },
                {
                    "name": "機密書類の一部",
                    "description": "シュレッダーを免れた書類の一部。金額と日付が見える。",
                    "hint": "巨額の取引に関する証拠かもしれない。",
                    "importance": "important"
                },
                {
                    "name": "謎の会員証",
                    "description": "高級クラブの会員証。偽名で登録されている。",
                    "hint": "被害者の隠された一面を示している。",
                    "importance": "important"
                }
            ],
            'custom': [
                {
                    "name": "謎の手がかり",
                    "description": "事件現場に残された不可解な物品。一見すると無関係に見える。",
                    "hint": "この手がかりの真の意味を理解することが事件解決の鍵となる。",
                    "importance": "critical"
                },
                {
                    "name": "重要な証拠品",
                    "description": "被害者が最後に触れたと思われる物品。指紋が残っている可能性がある。",
                    "hint": "誰の指紋が検出されるかが重要だ。",
                    "importance": "important"
                },
                {
                    "name": "決定的証拠",
                    "description": "犯人を特定できる可能性がある証拠。慎重な分析が必要。",
                    "hint": "この証拠が示す真実は予想外のものかもしれない。",
                    "importance": "important"
                }
            ]
        }
        
        import random
        evidence_templates = evidence_templates_by_location.get(location_key, evidence_templates_by_location['custom'])
        
        # ユーザーの位置を取得
        base_lat = location.get('lat', 35.5070)
        base_lng = location.get('lng', 139.6176)
        
        # POIサービスを使用して実際の場所を取得
        poi_service = POIService()
        
        # Google Maps APIキーの確認（環境変数から）
        maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if maps_api_key:
            print(f"DEBUG: Google Maps API使用 - 実際のPOIを取得")
        else:
            print(f"DEBUG: Google Maps APIキーなし - フォールバックPOI使用")
        
        # 非同期でPOI情報を取得
        import asyncio
        evidence_locations = await poi_service.get_evidence_locations(
            base_lat,
            base_lng,
            evidence_count=len(evidence_templates),
            min_distance=100,  # 100m以上
            max_distance=500   # 500m以内に変更
        )
        
        # 証拠を配置
        evidence = []
        for i, (template, location_info) in enumerate(zip(evidence_templates, evidence_locations), 1):
            evidence.append({
                "evidence_id": f"evidence_{i}",
                "name": template["name"],
                "description": template["description"],
                "hint": template["hint"],
                "importance": template["importance"],
                "poi_name": location_info['poi_name'],
                "location": {"lat": location_info['lat'], "lng": location_info['lng']}
            })
            print(f"DEBUG: 証拠配置 - {template['name']} at {location_info['poi_name']} ({location_info['lat']:.4f}, {location_info['lng']:.4f})")
        
        print(f"DEBUG: 証拠を配置 - ベース位置 ({base_lat:.4f}, {base_lng:.4f}) 周辺の実際のPOI使用")
        
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