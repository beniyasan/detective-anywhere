#!/usr/bin/env python3
"""
センター北駅用カスタムシナリオ生成テスト
実際の場所に基づいた適切なミステリーシナリオを作成
"""

import os
import json
import googlemaps
from dotenv import load_dotenv

load_dotenv()

def create_center_kita_scenario():
    """センター北駅周辺に適したミステリーシナリオを生成"""
    
    print("🎭 センター北駅カスタムシナリオ生成")
    print("=" * 50)
    
    # センター北駅周辺の実際のPOI調査
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ Google Maps APIキーが設定されていません")
        return None
    
    gmaps = googlemaps.Client(key=api_key)
    center_kita_location = (35.5949, 139.5651)
    
    # 周辺POI検索
    places_result = gmaps.places_nearby(
        location=center_kita_location,
        radius=800,
        type='point_of_interest'
    )
    
    pois = places_result.get('results', [])
    
    # 特徴的な施設を特定
    cafes = [p for p in pois if any('cafe' in t for t in p.get('types', []))]
    restaurants = [p for p in pois if any('restaurant' in t for t in p.get('types', []))]
    stores = [p for p in pois if any('store' in t for t in p.get('types', []))]
    
    print(f"📊 周辺施設調査結果:")
    print(f"   カフェ: {len(cafes)}件")
    print(f"   レストラン: {len(restaurants)}件") 
    print(f"   店舗: {len(stores)}件")
    
    # 実際に見つかったカフェを使用
    main_location = None
    if cafes:
        main_location = cafes[0]
        location_name = main_location.get('name', 'Hoshino Coffee')
    else:
        location_name = "センター北駅前カフェ"
    
    print(f"🎯 メイン事件現場: {location_name}")
    
    # センター北駅の特徴を活かしたシナリオ作成
    scenario = {
        "title": "ニュータウンの影",
        "description": f"午後2時、横浜市都筑区のセンター北駅近くにある{location_name}で、常連客の田村健一(52歳・不動産会社勤務)が突然倒れた。救急車で運ばれたが既に息を引き取っており、警察は事件性が高いと判断。ニュータウン開発に関わる複雑な人間関係が浮かび上がる中、あなたは現場に居合わせた探偵として、この謎の解明を任された。",
        "victim": {
            "name": "田村健一",
            "age": 52,
            "occupation": "不動産会社勤務",
            "personality": "野心的で商才があるが、時々強引な手法を取る",
            "temperament": "ambitious",
            "relationship": "被害者"
        },
        "suspects": [
            {
                "name": "佐々木恵子",
                "age": 38,
                "occupation": "カフェ店長",
                "personality": "地域密着型の経営で人情味があるが、最近は経営に悩んでいた",
                "temperament": "caring",
                "relationship": "店長として被害者とよく話していた",
                "alibi": "事件時は厨房で新メニューの試作をしていた",
                "motive": "田村に店舗立ち退きを迫られており、経営難に追い込まれていた"
            },
            {
                "name": "山下大輔", 
                "age": 29,
                "occupation": "地域開発コンサルタント",
                "personality": "理想主義者で地域コミュニティを大切にする反面、現実と理想のギャップに苦悩",
                "temperament": "idealistic",
                "relationship": "ニュータウン再開発プロジェクトで対立",
                "alibi": "近くのコワーキングスペースで資料作成していた",
                "motive": "田村の開発計画が地域コミュニティを破壊すると激しく対立していた"
            },
            {
                "name": "中村美智子",
                "age": 45,
                "occupation": "地域住民代表",
                "personality": "地域のことを誰よりも愛しているが、変化に対して保守的",
                "temperament": "protective",
                "relationship": "住民代表として田村と何度も交渉",
                "alibi": "近所の商店街で買い物をしていた", 
                "motive": "田村の再開発計画で長年住んでいた地域が変わってしまうことに強く反発していた"
            },
            {
                "name": "小林雅人",
                "age": 34,
                "occupation": "田村の不動産会社の部下",
                "personality": "真面目で忠実だが、最近上司との方針に疑問を抱いている",
                "temperament": "conflicted", 
                "relationship": "田村の直属の部下",
                "alibi": "会社でプレゼン資料の準備をしていた",
                "motive": "田村の強引な開発手法に反発し、内部告発を検討していた"
            }
        ],
        "culprit": "山下大輔"
    }
    
    # 証拠をセンター北駅周辺の実際のPOIに配置
    evidence_locations = []
    
    # 利用可能なPOIから証拠配置場所を選定
    suitable_pois = [p for p in pois if p.get('rating', 0) > 3.0][:5]
    
    evidence_templates = [
        {"name": "開発計画書の一部", "importance": "critical", "description": "田村の開発計画に関する重要な手がかり"},
        {"name": "住民の抗議文", "importance": "important", "description": "地域住民からの強い反発を示す証拠"},
        {"name": "内部告発メール", "importance": "critical", "description": "会社内部の不正を告発しようとしていた証拠"},
        {"name": "カフェのレシート", "importance": "misleading", "description": "事件当日の時系列を示すが、ミスリードの可能性"},
        {"name": "コンサルタント契約書", "importance": "important", "description": "山下と田村の間の契約関係を示す重要資料"}
    ]
    
    print(f"\n🔎 証拠配置計画:")
    
    for i, poi in enumerate(suitable_pois):
        if i < len(evidence_templates):
            evidence_template = evidence_templates[i]
            location = poi['geometry']['location']
            
            evidence = {
                "evidence_id": f"evidence_{i+1}",
                "name": evidence_template["name"], 
                "description": evidence_template["description"],
                "location": {"lat": location['lat'], "lng": location['lng']},
                "poi_name": poi.get('name', f'場所{i+1}'),
                "poi_type": poi.get('types', ['establishment'])[0],
                "importance": evidence_template["importance"]
            }
            
            evidence_locations.append(evidence)
            
            print(f"   {i+1}. {evidence['name']}")
            print(f"      配置場所: {evidence['poi_name']}")
            print(f"      重要度: {evidence['importance']}")
            print(f"      座標: {location['lat']:.6f}, {location['lng']:.6f}")
    
    # 完全なシナリオパッケージ
    game_scenario = {
        "scenario": scenario,
        "evidence": evidence_locations,
        "location_info": {
            "name": "センター北駅周辺",
            "prefecture": "神奈川県",
            "city": "横浜市都筑区",
            "characteristics": "ニュータウン、計画都市、住宅街とビジネス地区の融合"
        },
        "difficulty_adjustments": {
            "hard": {
                "additional_red_herrings": 2,
                "complex_alibis": True,
                "multiple_motives": True,
                "time_pressure": False
            }
        }
    }
    
    return game_scenario

def display_custom_scenario(scenario_data):
    """カスタムシナリオの詳細表示"""
    
    if not scenario_data:
        print("❌ シナリオデータがありません")
        return
    
    scenario = scenario_data["scenario"]
    evidence = scenario_data["evidence"] 
    location_info = scenario_data["location_info"]
    
    print(f"\n🎬 【カスタムシナリオ詳細】")
    print("=" * 60)
    
    print(f"📍 場所: {location_info['city']}{location_info['name']}")
    print(f"🏙️  地域特性: {location_info['characteristics']}")
    
    print(f"\n📖 タイトル: {scenario['title']}")
    print(f"📝 あらすじ:")
    print(f"   {scenario['description']}")
    
    print(f"\n💀 被害者: {scenario['victim']['name']} ({scenario['victim']['age']}歳)")
    print(f"   職業: {scenario['victim']['occupation']}")
    print(f"   性格: {scenario['victim']['personality']}")
    
    print(f"\n🕵️ 容疑者一覧 ({len(scenario['suspects'])}名):")
    for i, suspect in enumerate(scenario['suspects']):
        print(f"   {i+1}. {suspect['name']} ({suspect['age']}歳)")
        print(f"      職業: {suspect['occupation']}")
        print(f"      性格: {suspect['personality']}")
        print(f"      関係: {suspect['relationship']}")
        print(f"      アリバイ: {suspect['alibi']}")
        print(f"      動機: {suspect['motive']}")
        print()
    
    print(f"🎯 真犯人: {scenario['culprit']}")
    
    print(f"\n🔍 証拠配置 ({len(evidence)}件):")
    for i, ev in enumerate(evidence):
        print(f"   {i+1}. {ev['name']} (重要度: {ev['importance']})")
        print(f"      場所: {ev['poi_name']}")
        print(f"      説明: {ev['description']}")
        print(f"      座標: {ev['location']['lat']:.6f}, {ev['location']['lng']:.6f}")
        print()
    
    print(f"📊 地域の特徴を活かした設定:")
    print(f"   - ニュータウン開発の背景を活用")
    print(f"   - 地域コミュニティの結束と変化への不安")
    print(f"   - 不動産開発に関わる複雑な利害関係") 
    print(f"   - 横浜市都筑区という実際の地域性")

if __name__ == "__main__":
    print("🎭 センター北駅カスタムシナリオジェネレーター")
    print("=" * 60)
    
    # カスタムシナリオ生成
    scenario_data = create_center_kita_scenario()
    
    if scenario_data:
        # 詳細表示
        display_custom_scenario(scenario_data)
        
        # JSONで保存（オプション）
        with open('center_kita_custom_scenario.json', 'w', encoding='utf-8') as f:
            json.dump(scenario_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 シナリオを center_kita_custom_scenario.json に保存しました")
        print(f"✅ センター北駅の地域性を活かしたミステリーシナリオ生成完了！")
    else:
        print("❌ シナリオ生成に失敗しました")