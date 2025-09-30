import os
import sys
import datetime
import traceback
import logging
import gspread
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.g_sheet_handler import get_sheet, get_all_videos_for_report, update_report_data, EXPECTED_HEADERS
from handlers.youtube_handler import get_authenticated_service, get_video_stats_bulk, get_video_comments
from handlers.analysis_ai import generate_insight_and_plan, generate_weekly_insights
from handlers.discord_handler import (
    send_discord_notification, 
    format_analysis_notification, 
    format_daily_report, 
    format_weekly_report, 
    format_error_notification
)
from utils.utils import get_unique_log_filename
from core.performance_analyzer import PerformanceAnalyzer
from core.unified_scoring_system import UnifiedScoringSystem

load_dotenv()

# ロギング設定
log_file_path = get_unique_log_filename("reporter")

# ファイルハンドラーを作成（バッファリング無効）
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# ストリームハンドラーを作成
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler],
    force=True
)

# ログの即座フラッシュ設定
logger = logging.getLogger()
for handler in logger.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.stream.reconfigure(line_buffering=True)
        
# ログ関数を再定義してフラッシュを強制
original_info = logger.info
def flush_info(msg, *args, **kwargs):
    original_info(msg, *args, **kwargs)
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
logger.info = flush_info

def create_daily_summary_report(videos_with_stats):
    """サマリーレポートを作成してDiscordに通知する"""
    logging.info("デイリーサマリーレポートを作成中...")
    
    total_views = sum(v['latest_stats']['views'] for v in videos_with_stats)
    total_likes = sum(v['latest_stats']['likes'] for v in videos_with_stats)
    total_comments = sum(v['latest_stats']['comments'] for v in videos_with_stats)
    
    # 各動画の再生数変化とスコアを計算
    scoring_system = UnifiedScoringSystem()
    for v in videos_with_stats:
        v['views_change'] = v['latest_stats']['views'] - v['previous_views']
        # 統一スコアを計算
        score_result = scoring_system.calculate_unified_score(v, videos_with_stats, channel_subscribers=50)
        v['score_info'] = {
            'score': score_result['unified_score'],
            'rank': score_result['rank']
        }

    top_5_growing = sorted([v for v in videos_with_stats if v['views_change'] > 0], 
                             key=lambda x: x['views_change'], 
                             reverse=True)[:5]

    message = format_daily_report(total_views, total_likes, total_comments, top_5_growing)
    if send_discord_notification(message, username="デイリーレポートBot"):
        logging.info("Discordにデイリーサマリーレポートを送信しました。")

def create_weekly_summary_report(videos_with_stats, sheet, col_map):
    """週次サマリーレポートを作成してDiscordに通知する"""
    logging.info("週次サマリーレポートを作成中...")

    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    
    # 今週公開された動画
    new_videos_week = [v for v in videos_with_stats if (today - datetime.datetime.strptime(v['upload_date'], "%Y/%m/%d").date()).days < 7]

    # 今週再生数が伸びた動画 (過去7日間の再生数変化でソート)
    scoring_system = UnifiedScoringSystem()
    for v in videos_with_stats:
        v['views_change'] = v['latest_stats']['views'] - v['previous_views']
        # 週次レポートでもスコア情報を追加
        if 'score_info' not in v:  # デイリーレポートで既に計算済みの場合はスキップ
            score_result = scoring_system.calculate_unified_score(v, videos_with_stats, channel_subscribers=50)
            v['score_info'] = {
                'score': score_result['unified_score'],
                'rank': score_result['rank']
            }
    top_3_growing_week = sorted([v for v in videos_with_stats if v['views_change'] > 0], 
                                  key=lambda x: x['views_change'], 
                                  reverse=True)[:3]

    # 総再生数が多い動画 (上位5件)
    top_5_total_views = sorted(videos_with_stats, key=lambda x: x['latest_stats']['views'], reverse=True)[:5]

    # 相対評価分析を実行
    analyzer = PerformanceAnalyzer()
    relative_analysis = analyzer.analyze_relative_performance(videos_with_stats)
    logging.info(f"相対評価分析完了: {relative_analysis.get('analyzed_videos_count', 0)}本の動画を分析")
    
    # 統一スコアリング分析を実行（既に作成済みのインスタンスを使用）
    unified_analysis = scoring_system.analyze_channel_performance(videos_with_stats, channel_subscribers=50)
    logging.info(f"統一スコアリング分析完了: 平均スコア {unified_analysis.get('average_score', 0)}点")

    # AIによる週次インサイト生成（相対評価結果を含む）
    # 分析対象動画を結合 (伸びている動画 + 総再生数が多い動画)
    unique_video_ids = set()
    analysis_target_videos = []
    for v in top_3_growing_week + top_5_total_views:
        if v['video_id'] not in unique_video_ids:
            unique_video_ids.add(v['video_id'])
            analysis_target_videos.append(v)
    weekly_insights_result = generate_weekly_insights(analysis_target_videos, relative_analysis)
    weekly_insights = weekly_insights_result  # 辞書全体を保持
    weekly_tokens = weekly_insights_result['tokens']

    # 週次レポートのトークン数と料金を、その週の最新の動画に加算
    if new_videos_week:
        # 最新の動画を特定（複数ある場合は最初のもの）
        latest_video_in_week = sorted(new_videos_week, key=lambda x: datetime.datetime.strptime(x['upload_date'], "%Y/%m/%d"), reverse=True)[0]
        
        row_num = latest_video_in_week['row_num']
        tokens_col_name, cost_col_name = "トークン数", "料金"
        tokens_cell_a1 = gspread.utils.rowcol_to_a1(row_num, col_map[tokens_col_name])
        cost_cell_a1 = gspread.utils.rowcol_to_a1(row_num, col_map[cost_col_name])
        
        prev_tokens = int(sheet.acell(tokens_cell_a1).value or "0")
        prev_cost_str = sheet.acell(cost_cell_a1).value or "¥0"
        prev_cost = float(prev_cost_str.replace("¥", "").replace(",", ""))

        new_tokens = prev_tokens + weekly_tokens
        new_cost = prev_cost + (weekly_tokens * 0.23 / 1000) # 0.23円/1000トークン
        
        sheet.update(f"{tokens_cell_a1}:{cost_cell_a1}", [[new_tokens, f"¥{new_cost:,.2f}"]], value_input_option='USER_ENTERED')
        logging.info(f"週次レポートのトークン数({weekly_tokens})と料金(¥{weekly_tokens * 0.23 / 1000:.2f})を動画「{latest_video_in_week['title']}」に加算しました。")

    message = format_weekly_report(
        total_views_week=sum(v['latest_stats']['views'] for v in videos_with_stats), # 全動画の最新再生数合計
        total_likes_week=sum(v['latest_stats']['likes'] for v in videos_with_stats), # 全動画の最新いいね数合計
        total_comments_week=sum(v['latest_stats']['comments'] for v in videos_with_stats), # 全動画の最新コメント数合計
        new_videos_week=new_videos_week,
        top_3_growing_week=top_3_growing_week,
        weekly_insights=weekly_insights, # AIのインサイトを追加
        unified_analysis=unified_analysis # 統一スコア分析結果を追加
    )
    if send_discord_notification(message, username="週次レポートBot"):
        logging.info("Discordに週次サマリーレポートを送信しました。")

def run_report_flow(youtube_service):
    """動画の分析とレポートを行うフロー"""
    logging.info("--- 分析＆レポート フロー開始 ---")
    
    # Discord通知: 分析処理開始
    analysis_start_message = f"📊 **分析処理開始**\n開始時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_discord_notification(analysis_start_message, username="分析処理Bot")
    sheet = get_sheet()
    if not sheet: return

    # 1. スプレッドシートから現在の動画リストと統計情報を取得
    videos_in_sheet = get_all_videos_for_report(sheet)
    if not videos_in_sheet:
        logging.info("レポート対象の動画はありませんでした。")
        return

    video_ids = [v['video_id'] for v in videos_in_sheet]

    # 2. YouTubeから最新の統計情報を一括取得
    latest_stats_map = get_video_stats_bulk(youtube_service, video_ids)
    if not latest_stats_map:
        logging.error("YouTubeから統計情報を取得できませんでした。")
        return

    # 3. 各動画の情報を更新・分析
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    videos_for_summary = []

    col_map = {name: i + 1 for i, name in enumerate(EXPECTED_HEADERS)}
    

    for video in videos_in_sheet:
        latest_stats = latest_stats_map.get(video['video_id'])
        if not latest_stats:
            continue

        update_data = {"row_num": video['row_num'], "stats": latest_stats}

        # --- 日次・週次分析の判定と実行 ---
        upload_date = datetime.datetime.strptime(video['upload_date'], "%Y/%m/%d").date()
        days_since_upload = (today - upload_date).days

        # 分析がまだ行われていない動画のみ、分析と計画を実行する
        # 動画公開から1日以上経過していること（再生数0でも初回分析は実行）
        if days_since_upload >= 1 and not video['previous_analysis']:
            logging.info(f"動画「{video['title']}」の分析を実行します。")
            
            # 統一スコア算出
            scoring_system = UnifiedScoringSystem()
            score_result = scoring_system.calculate_unified_score(video, videos_in_sheet, channel_subscribers=50)
            
            # コメント取得
            comments_data = get_video_comments(youtube_service, video['video_id'])
            
            insight = generate_insight_and_plan(
                title=video['title'],
                script=video['script'],
                previous_plan=video['previous_plan'],
                stats_data=latest_stats,
                comments_data=comments_data
            )
            update_data['insight'] = insight
            
            analysis_type = "週次" if days_since_upload >= 7 else "日次"
            message = format_analysis_notification(video, latest_stats, insight, analysis_type, score_result)
            if send_discord_notification(message, username="分析レポートBot"):
                logging.info(f"✅ Discordに{analysis_type}分析結果を通知しました。")

        # 4. スプレッドシートを更新
        if update_report_data(sheet, col_map, update_data):
            logging.info(f"動画「{video['title']}」の情報を更新しました。")

        # サマリーレポート用にデータを格納
        video['latest_stats'] = latest_stats
        videos_for_summary.append(video)

    # 5. デイリーサマリーレポートを作成して通知
    if videos_for_summary:
        create_daily_summary_report(videos_for_summary)

    # 6. 週次サマリーレポートを作成して通知 (毎週日曜日)
    today_weekday = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).weekday()
    if today_weekday == 6: # 日曜日 (0=月曜日, 6=日曜日)
        create_weekly_summary_report(videos_for_summary, sheet, col_map)

    logging.info("--- 分析＆レポート フロー完了 ---")
    
    # Discord通知: 分析処理完了
    analysis_end_message = f"✅ **分析処理完了**\n終了時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_discord_notification(analysis_end_message, username="分析処理Bot")

if __name__ == "__main__":
    try:
        logging.info("YouTube APIの認証を開始します...")
        youtube_service = get_authenticated_service()
        if not youtube_service:
            logging.error("YouTube APIの認証に失敗しました。")
            exit()
        logging.info("YouTube APIの認証に成功しました。")
        run_report_flow(youtube_service)
    except Exception as e:
        error_message = f"reporter.pyの実行中に予期せぬエラーが発生しました。"
        tb_str = traceback.format_exc()
        logging.error(f"{error_message}\n{tb_str}")
        send_discord_notification(format_error_notification("reporter.py", error_message, tb_str), username="エラー通知Bot")
    finally:
        logging.info("全ての処理が完了しました。")