# gemini_handler.py
import os
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from utils.utils import extract_json
from utils.season_utils import get_seasonal_context

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "prompts.json")
    with open(config_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)
except FileNotFoundError:
    print("❌エラー: prompts.json が見つかりません。")
    exit()

def generate_next_plan_prompt(past_data, relative_analysis=None):
    """過去の分析から、次の動画の改善方針プロンプトを生成する（相対評価分析も活用）"""
    print("INFO: AIが次回の改善方針を生成中...")
    insights_for_prompt = []
    if past_data:
        for data in sorted(past_data, key=lambda x: x.get('views', 0), reverse=True)[:3]:
            if data.get('analysis'):
                 insights_for_prompt.append(f"テーマ「{data['theme']}」\n分析: {data['analysis']}\n計画: {data['plan']}\n")
    
    formatted_insights = "\n---\n".join(insights_for_prompt) if insights_for_prompt else "（今回が初めての分析です）"
    
    # 相対評価分析データを追加
    relative_insights = ""
    if relative_analysis and "error" not in relative_analysis:
        theme_analysis = relative_analysis.get("theme_analysis", {})
        performance_metrics = relative_analysis.get("performance_metrics", {})
        
        # 動的な統計情報を取得
        views_stats = performance_metrics.get("views", {})
        avg_views = int(views_stats.get("avg", 0))
        median_views = int(views_stats.get("median", 0))
        max_views = int(views_stats.get("max", 0))
        min_views = int(views_stats.get("min", 0))
        
        if theme_analysis:
            most_popular = theme_analysis.get("most_popular_theme", "")
            suggestions = relative_analysis.get("improvement_suggestions", [])
            relative_insights = f"""
            
            ### チャンネル全体のパフォーマンス分析
            - 分析対象動画数: {relative_analysis.get('analyzed_videos_count', 0)}本
            - 再生数統計: 平均{avg_views:,}回、中央値{median_views:,}回、最高{max_views:,}回、最低{min_views:,}回
            - 最も人気のテーマ: {most_popular}
            - 改善提案: {'; '.join(suggestions[:3]) if suggestions else 'なし'}
            
            ### 相対評価基準
            - 平均的なパフォーマンス: {median_views:,}回程度
            - 高パフォーマンス: {int(median_views * 1.5):,}回以上
            - 低パフォーマンス: {int(median_views * 0.7):,}回未満
            """

    prompt_config = prompts["next_plan_prompt"]
    current_datetime = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    seasonal_context = get_seasonal_context()
    system_prompt = f"{prompt_config['system_instruction']}\n\n{seasonal_context}\n\n{prompt_config['task_template'].format(current_datetime=current_datetime, formatted_insights=formatted_insights)}{relative_insights}"
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(system_prompt)
    usage = model.count_tokens(system_prompt).total_tokens
    
    return response.text, usage

def generate_quiz_script(plan_prompt, past_data, num_questions=10):
    """AIに戦略的に漢字クイズの台本をJSON形式で生成させる"""
    print("INFO: AIが戦略的に漢字クイズのテーマと台本を生成中...")

    past_themes = [data['theme'] for data in past_data if data['theme'] != "不明"]
    top_theme = "なし"
    if past_data:
        top_video = max(past_data, key=lambda x: x.get('views', 0))
        top_theme = top_video['theme'] if top_video.get('views', 0) > 0 else "なし"
    
    past_themes_str = ", ".join(set(past_themes)) if past_themes else "なし"

    prompt_config = prompts["quiz_script_prompt"]
    current_datetime = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    seasonal_context = get_seasonal_context()
    system_prompt = (
        f"{prompt_config['system_instruction']}\n\n"
        f"{seasonal_context}\n\n"
        f"{prompt_config['task_template'].format(current_datetime=current_datetime, past_themes_str=past_themes_str, top_theme=top_theme, plan_prompt=plan_prompt, num_questions=num_questions)}\n\n"
        f"{prompt_config['verification_instruction']}\n\n"
        f"{prompt_config['json_format_instruction'].format(question_number=1)}"
    )
    
    generation_config = {"response_mime_type": "application/json"}
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config=generation_config)
    
    response = model.generate_content(system_prompt)
    json_data = extract_json(response.text)
    
    # 問題数の厳格な検証を実行
    json_data = validate_and_fix_quiz_questions(json_data, num_questions)
    
    usage = model.count_tokens(system_prompt).total_tokens
                
    return json_data, usage

def validate_and_fix_quiz_questions(quiz_data, expected_questions=10):
    """
    クイズデータの問題数を厳格に検証し、不足している場合は補完を試みる

    Args:
        quiz_data: クイズデータのJSON
        expected_questions: 期待する問題数（デフォルト: 10）

    Returns:
        dict: 検証済みのクイズデータ
    """
    if not quiz_data or not isinstance(quiz_data, dict):
        print(f"❌ ERROR: 無効なクイズデータです。期待する問題数: {expected_questions}問")
        return None

    quiz_questions = quiz_data.get("quiz_data", [])
    actual_count = len(quiz_questions)

    print(f"INFO: 問題数検証 - 生成された問題数: {actual_count}問, 期待する問題数: {expected_questions}問")

    if actual_count == expected_questions:
        print(f"OK: 問題数が正確に{expected_questions}問です。")
        return quiz_data

    elif actual_count < expected_questions:
        print(f"WARNING: 問題数が不足しています ({actual_count}問 < {expected_questions}問)")

        # 耐久版の場合は、ある程度の問題数があれば許可する（最低30問）
        if expected_questions > 30 and actual_count >= 30:
            print(f"INFO: 耐久版として{actual_count}問で続行します（最低限の問題数を満たしています）")
            return quiz_data
        # 通常版の場合は10問必須
        elif expected_questions <= 10 and actual_count < 5:
            print("ERROR: 問題数不足により、動画生成を中止します。")
            print("漢字クイズとして成り立たない問題の生成を防ぐため、最低5問は必要です。")
            return None
        else:
            print(f"INFO: {actual_count}問で動画生成を続行します")
            return quiz_data

    elif actual_count > expected_questions:
        print(f"WARNING: 問題数が多すぎます ({actual_count}問 > {expected_questions}問)")
        print(f"最初の{expected_questions}問のみを使用します。")
        quiz_data["quiz_data"] = quiz_questions[:expected_questions]
        return quiz_data

    return quiz_data
