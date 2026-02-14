# discord_handler.py
import os
import requests
import datetime
from dotenv import load_dotenv

load_dotenv(override=True)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_WEBHOOK_URL_ERROR = os.getenv("DISCORD_WEBHOOK_URL_ERROR")

DISCORD_MESSAGE_LIMIT = 1900  # Discordの上限2000文字に安全マージンを確保

def _split_message(message: str, limit: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
    """メッセージをDiscordの文字数制限に合わせて分割する"""
    if len(message) <= limit:
        return [message]

    chunks: list[str] = []
    while message:
        if len(message) <= limit:
            chunks.append(message)
            break
        # 改行で区切れる位置を探す
        split_pos = message.rfind("\n", 0, limit)
        if split_pos <= 0:
            split_pos = limit
        chunks.append(message[:split_pos])
        message = message[split_pos:].lstrip("\n")
    # 空文字チャンクを除外
    return [c for c in chunks if c.strip()]

def send_discord_notification(message: str, username: str = "動画生成Bot", is_error: bool = False) -> bool:
    """
    DiscordのWebhookを使って、指定されたメッセージを送信する
    2000文字を超える場合は自動で分割して送信する
    :param is_error: エラー通知の場合はTrue
    :return: 成功した場合はTrue、失敗した場合はFalse
    """
    webhook_url = DISCORD_WEBHOOK_URL_ERROR if is_error else DISCORD_WEBHOOK_URL
    if not webhook_url:
        print(f"WARNING: .envファイルに適切なWebhook URLが設定されていません。(is_error={is_error})")
        return False

    chunks = _split_message(message)
    try:
        for chunk in chunks:
            payload = {"username": username, "content": chunk}
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        # レスポンスボディからDiscordのエラー詳細を取得
        detail = ""
        if hasattr(e, 'response') and e.response is not None:
            try:
                detail = f" | 詳細: {e.response.text[:300]}"
            except Exception:
                pass
        print(f"ERROR: Discord通知の送信に失敗しました: {e}{detail}")
        return False

def format_script_notification(theme, title, description):
    """台本概要の通知メッセージをフォーマットする"""
    return (
        f"**AIが新しい動画の台本を生成しました！**\n\n"
        f"- **テーマ:** {theme}\n"
        f"- **タイトル:** {title}\n"
        f"- **概要:** {description}"
    )

def format_error_notification(script_name, error_message, traceback_str):
    """エラー通知メッセージをフォーマットする"""
    return (
        f":warning: **エラーが発生しました** :warning:\n\n"
        f"**スクリプト:** `{script_name}`\n"
        f"**エラー内容:**\n```\n{error_message}\n```\n\n"
        f"**スタックトレース:**\n```python\n{traceback_str}\n```"
    )

def format_analysis_notification(video, stats, insight, analysis_type, score_result=None):
    """分析結果をDiscord通知用にフォーマットする"""
    # スコア情報を最初に表示するかどうか
    score_header = ""
    if score_result:
        score = score_result['unified_score']
        rank = score_result['rank']
        rank_emoji = {"S": "🏆", "A": "🥇", "B": "🥈", "C": "🥉", "D": "📈"}.get(rank, "📊")
        score_header = f" {rank_emoji} **{score:.1f}点 (ランク{rank})**"

    message = (
        f"📈 **{analysis_type}分析レポート**{score_header} 📈\n\n"
        f"**動画タイトル:** {video['title']}\n"
        f"https://www.youtube.com/watch?v={video['video_id']}\n\n"
        f"**【統計情報】**\n"
        f"- 再生数: {stats['views']:,} 回\n"
        f"- 高評価: {stats['likes']:,} 件\n"
        f"- コメント: {stats['comments']:,} 件\n\n"
        f"**【AIによる分析】**\n>>> {insight['analysis']}\n\n"
        f"**【次回の計画案】**\n>>> {insight['plan']}"
    )
    
    # 統一スコア情報を追加
    if score_result:
        score_section = (
            f"\n\n**【統一スコア評価】**\n"
            f"- 総合スコア: **{score_result['unified_score']}点**/100 (ランク: {score_result['rank']})\n"
            f"- 内訳: 再生数 {score_result['score_breakdown']['views']}点 | "
            f"コメント {score_result['score_breakdown']['comments_count']}点 | "
            f"内容評価 {score_result['score_breakdown']['comments_quality']}点\n"
        )
        
        # テーマボーナス
        if score_result.get('theme_bonus', 1.0) > 1.0:
            score_section += f"- テーマボーナス: x{score_result['theme_bonus']} (専門性評価)\n"
        
        # 改善提案
        recommendations = score_result.get('recommendations', [])
        if recommendations:
            score_section += f"- 改善提案: {recommendations[0]}"
        
        message += score_section
    
    return message

def format_daily_report(total_views, total_likes, total_comments, top_5_growing):
    """デイリーレポートをDiscord通知用にフォーマットする"""
    top_5_list = ""
    for i, v in enumerate(top_5_growing):
        # スコア情報を含めた表示
        score_info = ""
        if 'score_info' in v:
            score = v['score_info']['score']
            rank = v['score_info']['rank']
            score_info = f" [{score:.1f}点・{rank}]"
        
        top_5_list += f"{i+1}. **+{v['views_change']:,}**{score_info} - {v['title']}\n"
    if not top_5_list:
        top_5_list = "(直近24時間で再生数が伸びた動画はありませんでした)"

    message = (
        f"📊 **チャンネルデイリーレポート** 📊\n\n"
        f"**【総合統計 (前日比)】**\n"
        f"- 総再生数: {total_views:,} 回\n"
        f"- 総高評価数: {total_likes:,} 件\n"
        f"- 総コメント数: {total_comments:,} 件\n\n"
        f"**【再生数増加 Top 5 (直近24h)】**\n{top_5_list}"
    )
    return message

def format_github_actions_notification(status, execution_time, video_info=None, error_info=None):
    """
    GitHub Actions実行結果の通知をフォーマットする
    """
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    timestamp = now.strftime('%Y-%m-%d %H:%M JST')

    if status == 'success':
        emoji = '✅'
        color_indicator = '🟢'  # 緑円
        message = (
            f"{emoji} **KanjiQuiz自動生成成功** {color_indicator}\n\n"
            f"📅 **実行時刻:** {timestamp}\n"
            f"⏱️ **処理時間:** {execution_time}\n"
            f"📍 **実行環境:** GitHub Actions\n\n"
        )

        if video_info:
            message += (
                f"🎥 **生成された動画:**\n"
                f"- タイトル: {video_info.get('title', 'N/A')}\n"
                f"- ファイルサイズ: {video_info.get('size_mb', 0):.1f}MB\n"
                f"- YouTube URL: {video_info.get('url', 'N/A')}\n\n"
            )

        message += f"🚀 **次回実行予定:** 明日 20:00 JST"

    elif status == 'failure':
        emoji = '❌'
        color_indicator = '🔴'  # 赤円
        message = (
            f"{emoji} **KanjiQuiz自動生成失敗** {color_indicator}\n\n"
            f"📅 **実行時刻:** {timestamp}\n"
            f"⏱️ **処理時間:** {execution_time}\n"
            f"📍 **実行環境:** GitHub Actions\n\n"
        )

        if error_info:
            message += (
                f"⚠️ **エラー情報:**\n"
                f"```\n{error_info.get('message', 'Unknown error')}\n```\n\n"
            )

        message += (
            f"🔧 **対応方法:**\n"
            f"1. GitHub Actionsのログを確認\n"
            f"2. 手動でワークフローを再実行\n"
            f"3. 環境変数の設定を確認"
        )

    return message

def format_weekly_report(total_views_week, total_likes_week, total_comments_week, new_videos_week, top_3_growing_week, weekly_insights, unified_analysis=None):
    """週次レポートをDiscord通知用にフォーマットする"""
    new_videos_list = ""
    for i, v in enumerate(new_videos_week):
        new_videos_list += f"  - {v['title']}\n"
    if not new_videos_list:
        new_videos_list = "(今週公開された新しい動画はありませんでした)"

    top_3_list = ""
    for i, v in enumerate(top_3_growing_week):
        # スコア情報を含めた表示
        score_info = ""
        if 'score_info' in v:
            score = v['score_info']['score']
            rank = v['score_info']['rank']
            score_info = f" [{score:.1f}点・{rank}]"
        
        top_3_list += f"  {i+1}. **+{v['views_change']:,}**{score_info} - {v['title']}\n"
    if not top_3_list:
        top_3_list = "(今週再生数が大きく伸びた動画はありませんでした)"

    message = (
        f"📈 **チャンネル週次レポート** 📈\n\n"
        f"**【今週の総合統計】**\n"
        f"- 総再生数: {total_views_week:,} 回\n"
        f"- 総高評価数: {total_likes_week:,} 件\n"
        f"- 総コメント数: {total_comments_week:,} 件\n\n"
        f"**【今週公開された動画】**\n{new_videos_list}\n"
        f"**【今週再生数増加 Top 3】**\n{top_3_list}\n\n"
        f"**【AIによる週次インサイト】**\n>>> インサイト: {weekly_insights.get('insights', 'N/A') if isinstance(weekly_insights, dict) else str(weekly_insights)}\n>>> 提案: {weekly_insights.get('suggestions', 'N/A') if isinstance(weekly_insights, dict) else 'AI分析完了'}"
    )
    
    # 統一スコアリング結果を追加
    if unified_analysis and not unified_analysis.get('error'):
        avg_score = unified_analysis.get('average_score', 0)
        rank_dist = unified_analysis.get('rank_distribution', {})
        top_performer = unified_analysis.get('top_performers', [{}])[0]
        
        score_section = (
            f"\n\n**【統一スコア分析】**\n"
            f"- チャンネル平均: **{avg_score}点**/100\n"
            f"- ランク分布: S:{rank_dist.get('S', 0)} A:{rank_dist.get('A', 0)} B:{rank_dist.get('B', 0)} C:{rank_dist.get('C', 0)} D:{rank_dist.get('D', 0)}\n"
        )
        
        if top_performer.get('title'):
            score_section += f"- 最高スコア: **{top_performer.get('score', 0)}点** ({top_performer.get('title', '')[:30]}...)\n"
        
        # チャンネル改善提案
        channel_recs = unified_analysis.get('channel_recommendations', [])
        if channel_recs:
            score_section += f"- 改善提案: {channel_recs[0]}"
        
        message += score_section
    
    return message
