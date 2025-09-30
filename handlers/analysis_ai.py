# analysis_ai.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils.utils import extract_block

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_insight_and_plan(title, script, previous_plan, stats_data, comments_data=None):
    """
    動画の実行内容と統計結果を基に、深いインサイト分析と具体的な次回計画を生成する
    """
    print("INFO: AIアナリストが動画の分析を開始...")
    
    views = stats_data.get("views", "N/A")
    likes = stats_data.get("likes", "N/A")
    comments = stats_data.get("comments", "N/A")
    
    # 台本データを解析
    script_analysis = ""
    try:
        import json
        script_data = json.loads(script) if script else {}
        theme = script_data.get("theme", "不明")
        quiz_data = script_data.get("quiz_data", [])
        
        # 解説の長さ分析
        explanation_lengths = [len(q.get("kaisetsu", "")) for q in quiz_data]
        avg_explanation_length = sum(explanation_lengths) / len(explanation_lengths) if explanation_lengths else 0
        
        # 漢字の難易度分析
        kanji_list = [q.get("kanji", "") for q in quiz_data]
        
        script_analysis = f"""
        ### 台本分析
        - テーマ: {theme}
        - 問題数: {len(quiz_data)}問
        - 平均解説文字数: {avg_explanation_length:.1f}文字
        - 漢字例: {', '.join(kanji_list[:3]) if kanji_list else 'なし'}
        - 解説文字数範囲: {min(explanation_lengths) if explanation_lengths else 0}-{max(explanation_lengths) if explanation_lengths else 0}文字
        """
    except Exception as e:
        script_analysis = f"### 台本分析\n（台本解析エラー: {e}）"
    
    # コメント分析の追加
    comments_summary = ""
    if comments_data and len(comments_data) > 0:
        comments_summary = "### コメント分析\n"
        for comment in comments_data[:10]:  # 上位10件のコメントを分析
            comments_summary += f"- {comment['text'][:100]}...\n"
    else:
        comments_summary = "### コメント分析\n（コメントデータなし）"

    # 漢字クイズ動画に特化したプロンプト
    prompt = f"""
    あなたは漢字クイズYouTube動画の専門アナリストです。
    この動画は**音声のみの漢字クイズ動画**（映像なし、VoiceVox生成音声）です。
    以下の台本とパフォーマンスデータを分析し、具体的な改善提案を行ってください。

    # 分析の観点
    ## 1. 漢字選定とテーマ
    - 選定した漢字の難易度は適切か？（難しすぎ/簡単すぎ）
    - テーマ（{script_data.get('theme', '不明') if script else '不明'}）は視聴者の興味を引いたか？
    - 漢字の組み合わせにメリハリがあったか？

    ## 2. 解説内容と時間
    - 解説の文字数（平均{avg_explanation_length:.1f}文字）は適切か？
    - 解説内容は興味深く、記憶に残りやすいか？
    - 豆知識や語源説明の効果は？

    ## 3. テンポと構成
    - 問題→回答→解説のテンポは適切か？
    - 10問という問題数は視聴者の集中力に適していたか？
    - 冒頭の掴みや締めの言葉は効果的だったか？

    ## 4. エンゲージメント要因
    - 高評価率（{likes}/{views} = {likes/views*100 if views and likes else 0:.1f}%）から何が読み取れるか？
    - コメント数（{comments}件）が示す視聴者の反応は？
    - 知的好奇心を刺激する要素はあったか？

    # 次回の具体的改善計画
    上記分析に基づき、次回動画の具体的改善案を3つ提案してください：
    - 漢字テーマの選び方
    - 解説内容・文字数の調整
    - タイトルや構成の改善
    ※抽象的表現禁止。実行可能な具体策のみ。

    ---
    ### 実行した内容
    **前回の計画**: {previous_plan if previous_plan else "特になし"}
    **タイトル**: {title}
    {script_analysis}

    ### パフォーマンス結果
    - 再生数: {views}
    - 高評価数: {likes}
    - コメント数: {comments}
    - 高評価率: {likes/views*100 if views and likes else 0:.1f}%
    
    {comments_summary}
    ---

    # あなたの分析と計画
    ### 分析：
    （ここに分析を記述）
    ### 計画：
    （ここに計画を記述）
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        content = response.text
        usage = model.count_tokens(prompt).total_tokens

        return {
            "analysis": extract_block("分析", content),
            "plan": extract_block("計画", content),
            "tokens": usage 
        }
    except Exception as e:
        print(f"Gemini APIでの分析中にエラーが発生: {e}")
        return {"analysis": "エラー発生", "plan": "エラー発生", "tokens": 0}

def generate_weekly_insights(videos_data, relative_analysis=None):
    """
    週次レポート用に、動画の傾向を分析し、プロンプト改善のためのインサイトを生成する
    相対評価分析結果も活用する
    """
    print("INFO: AIが週次分析とプロンプト改善のインサイトを生成中...")

    # Prepare data for the AI
    video_summaries = []
    for video in videos_data:
        video_summaries.append(f"""
        - タイトル: {video.get('title', 'N/A')}
          テーマ: {video.get('theme', 'N/A')}
          再生数: {video.get('latest_stats', {}).get('views', 'N/A')}
          高評価: {video.get('latest_stats', {}).get('likes', 'N/A')}
          コメント: {video.get('latest_stats', {}).get('comments', 'N/A')}
          台本抜粋: {video.get('script', 'N/A')[:100]}...
          分析: {video.get('previous_analysis', 'N/A')}
          計画: {video.get('previous_plan', 'N/A')}
        """)

    formatted_video_summaries = "\n".join(video_summaries)
    
    # 相対評価分析データの整理
    relative_analysis_summary = ""
    if relative_analysis and "error" not in relative_analysis:
        theme_perf = relative_analysis.get("theme_analysis", {}).get("theme_performance", {})
        top_themes = list(theme_perf.keys())[:3]
        
        relative_analysis_summary = f"""
        
        ### チャンネル全体の相対評価分析
        - 分析対象動画数: {relative_analysis.get('analyzed_videos_count', 0)}本
        - 最も人気のテーマ: {relative_analysis.get('theme_analysis', {}).get('most_popular_theme', '不明')}
        - トップパフォーマンステーマ: {', '.join(top_themes) if top_themes else 'なし'}
        - 改善提案: {', '.join(relative_analysis.get('improvement_suggestions', [])) if relative_analysis.get('improvement_suggestions') else 'なし'}
        """

    prompt = f"""
    あなたは非常に優秀なYouTubeコンテンツ戦略家です。
    以下の動画データ（最近伸びている動画や総再生数の多い動画）と、チャンネル全体の相対評価分析を参考にして、
    今後の漢字クイズ動画のプロンプト改善に役立つインサイトと具体的な提案をしてください。

    # 分析の観点
    - **漢字のテーマ**: どのような漢字テーマが視聴者に響いているか？チャンネル全体のデータと比較してどうか？
    - **相対的なパフォーマンス**: チャンネル内で高パフォーマンスな動画の共通要素は何か？
    - **解説方法**: どのような解説が効果的か？（例：豆知識、語源、類義語との比較など）
    - **締めの言葉**: 視聴者の行動を促す効果的な締めの言葉の傾向は？
    - **エンゲージメント戦略**: 高評価率やコメント率が高い動画の特徴は？
    - **その他**: 統計データから読み取れる、動画の改善点や成功要因。

    # 提案
    上記の分析に基づき、次回の動画生成プロンプトに含めるべき具体的な改善提案を、以下の形式で記述してください。
    - 箇条書きで3つ以上。
    - 抽象的な表現は避け、AIが理解しやすい具体的な言葉で。
    - 例：「動画テーマは『季節の難読漢字』に焦点を当て、視聴者の共感を呼ぶように指示する。」
    - チャンネル全体の相対評価を考慮した戦略的な提案を含める。

    ---
    ### 分析対象動画データ:
    {formatted_video_summaries}
    {relative_analysis_summary}
    ---

    # あなたのインサイトと提案
    ### インサイト：
    （ここに分析結果のインサイトを記述）
    ### 提案：
    （ここにプロンプト改善の具体的な提案を記述）
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        content = response.text
        usage = model.count_tokens(prompt).total_tokens

        return {
            "insights": extract_block("インサイト", content),
            "suggestions": extract_block("提案", content),
            "tokens": usage
        }
    except Exception as e:
        print(f"❌ Gemini APIでの週次分析中にエラーが発生: {e}")
        return {"insights": "エラー発生", "suggestions": "エラー発生", "tokens": 0}