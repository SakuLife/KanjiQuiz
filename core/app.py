import os
import sys
import datetime
import json
import re
import traceback
import logging
import glob
import argparse
from dotenv import load_dotenv
from google.auth.exceptions import RefreshError

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- 各モジュールのインポート ---
from handlers.g_sheet_handler import get_sheet, fetch_past_data, append_new_video, get_all_videos_for_report
from handlers.gemini_handler import generate_next_plan_prompt, generate_quiz_script
from handlers.voicevox_handler import VoicevoxHandler
from core.video_generator import create_advanced_quiz_video
from core.video_generator_horizontal import create_horizontal_endurance_quiz
from handlers.youtube_handler import get_authenticated_service, upload_to_youtube
from handlers.discord_handler import send_discord_notification, format_script_notification, format_error_notification

from core.performance_analyzer import PerformanceAnalyzer
from utils.utils import get_unique_log_filename

load_dotenv()

# GitHub Actionsモードの確認
GITHUB_ACTIONS_MODE = os.environ.get('GITHUB_ACTIONS_MODE', 'false').lower() == 'true'
VOICEVOX_DISABLED = os.environ.get('VOICEVOX_DISABLED', 'false').lower() == 'true'

# VOICEVOXのパス設定
if VOICEVOX_DISABLED:
    VOICEVOX_ENGINE_PATH = None
elif GITHUB_ACTIONS_MODE:
    # GitHub Actionsでは環境変数から取得
    VOICEVOX_ENGINE_PATH = os.environ.get('VOICEVOX_ENGINE_PATH', '/tmp/linux-cpu-x64/run')
else:
    # ローカル実行時はWindowsパス
    VOICEVOX_ENGINE_PATH = r"D:\App\VOICEVOX\vv-engine\run.exe"

def cleanup_voice_files(base_filename):
    """
    動画生成完了後に使用済みvoiceファイルを削除する
    base_filename: YYYYMMDD_テーマ名 形式のファイル名
    """
    try:
        voice_pattern = f"voice/{base_filename}_*.wav"
        voice_files = glob.glob(voice_pattern)
        
        deleted_count = 0
        for voice_file in voice_files:
            try:
                os.remove(voice_file)
                deleted_count += 1
                logging.info(f"削除: {voice_file}")
            except Exception as e:
                logging.warning(f"ファイル削除失敗: {voice_file} - {e}")
        
        if deleted_count > 0:
            logging.info(f"voiceファイル削除完了: {deleted_count}個のファイルを削除")
        else:
            logging.warning(f"削除対象のvoiceファイルが見つかりませんでした: {voice_pattern}")
            
    except Exception as e:
        logging.error(f"voiceファイル削除中にエラー: {e}")

# ロギング設定
log_file_path = get_unique_log_filename("app")

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

# ログの即座フラッシュ設定（より確実な方法）
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

def run_creation_flow(vv_handler, youtube_service):
    """新しい動画を生成し、YouTubeにアップロード、スプレッドシートに記録するフロー"""
    logging.info("--- 漢字クイズ動画 生成フロー開始 ---")
    sheet = get_sheet()
    if not sheet: return

    past_data = fetch_past_data(sheet)
    
    # 相対評価分析を実行
    all_videos_data = get_all_videos_for_report(sheet)
    relative_analysis = None
    if len(all_videos_data) >= 2:
        analyzer = PerformanceAnalyzer()
        relative_analysis = analyzer.analyze_relative_performance(all_videos_data)
        logging.info(f"相対評価分析完了: {relative_analysis.get('analyzed_videos_count', 0)}本の動画を分析")
    
    plan_prompt, plan_tokens = generate_next_plan_prompt(past_data, relative_analysis)
    logging.info(f"AIプロデューサーによる改善方針:\n{plan_prompt}")
    
    # 通常版と耐久版の両方を生成
    quiz_data_normal, script_tokens_normal = generate_quiz_script(plan_prompt, past_data, num_questions=10)
    if not quiz_data_normal or not quiz_data_normal.get("quiz_data"): 
        logging.error("❌ 通常クイズデータの生成に失敗しました。")
        return
    
    # 耐久版クイズデータを生成（横型長尺動画）
    quiz_data_endurance = None
    script_tokens_endurance = 0
    if True:  # 耐久版を有効化
        endurance_plan = f"{plan_prompt}\n\n【耐久版用】10-20分の集中力を維持できる、テンポの良い連続クイズにしてください。視聴者が飽きないよう、バラエティに富んだ問題構成にしてください。"
        logging.info("耐久版（横型長尺動画）のクイズデータ生成を開始...")
        quiz_data_endurance, script_tokens_endurance = generate_quiz_script(endurance_plan, past_data, num_questions=30)
    # 耐久版が無効化されている場合はスキップ
    if quiz_data_endurance and quiz_data_endurance.get("quiz_data"):
        logging.info(f"✅ 耐久版クイズデータ生成成功: {len(quiz_data_endurance.get('quiz_data', []))}問")
    
    # 通常版の処理
    quiz_data = quiz_data_normal
    script_tokens = script_tokens_normal
        
    title = quiz_data.get("title", "難読漢字クイズ")
    theme = quiz_data.get("theme", "KanjiQuiz")
    logging.info(f"AIによる台本生成完了 (テーマ: {theme})")
    
    discord_message = format_script_notification(theme, title, quiz_data.get("description", ""))
    if send_discord_notification(discord_message, username="台本生成Bot"):
        logging.info("Discordに台本概要を通知しました。")
    
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    memo = re.sub(r'[\\|/|:|*|?|"|<|>|\\|]', '', theme)
    base_filename = f"{today_str}_{memo}"
    logging.info("ナレーションのパート別生成を開始します...")
    
    # 通常版音声生成
    voice_start_message = f"🎤 **音声生成開始**\nテーマ: {theme}\n通常版: {len(quiz_data['quiz_data'])}問"
    if quiz_data_endurance:
        voice_start_message += f"\n耐久版: {len(quiz_data_endurance['quiz_data'])}問"
    send_discord_notification(voice_start_message, username="音声生成Bot")
    
    # 通常版音声
    for i, quiz in enumerate(quiz_data["quiz_data"]):
        path_before = f"voice/{base_filename}_q{i+1}_before.wav"
        if not vv_handler.generate_voice(quiz.get("narration_before", ""), path_before, speaker=13): return
        path_after = f"voice/{base_filename}_q{i+1}_after.wav"
        narration_after_full = f"{quiz.get('narration_after', '')} {quiz.get('kaisetsu', '')}"
        if not vv_handler.generate_voice(narration_after_full, path_after, speaker=13): return
    path_outro = f"voice/{base_filename}_outro.wav"
    if not vv_handler.generate_voice(quiz_data.get("outro_narration", ""), path_outro, speaker=13): return
    
    # 耐久版音声生成 (必要に応じて)
    endurance_filename = f"{base_filename}_endurance"
    if quiz_data_endurance:
        logging.info("耐久版音声生成開始...")
        for i, quiz in enumerate(quiz_data_endurance["quiz_data"]):
            path_before = f"voice/{endurance_filename}_q{i+1}_before.wav"
            if not vv_handler.generate_voice(quiz.get("narration_before", ""), path_before, speaker=13): return
            path_after = f"voice/{endurance_filename}_q{i+1}_after.wav"
            narration_after_full = f"{quiz.get('narration_after', '')} {quiz.get('kaisetsu', '')}"
            if not vv_handler.generate_voice(narration_after_full, path_after, speaker=13): return
        path_outro_endurance = f"voice/{endurance_filename}_outro.wav"
        if not vv_handler.generate_voice(quiz_data_endurance.get("outro_narration", ""), path_outro_endurance, speaker=13): return
    
    logging.info("全ナレーションパートの生成完了。")
    
    # Discord通知: 音声生成完了
    voice_end_message = f"✅ **音声生成完了**\nテーマ: {theme}\n生成ファイル数: {len(quiz_data['quiz_data']) * 2 + 1}個"
    send_discord_notification(voice_end_message, username="音声生成Bot")

    # 通常版動画生成
    video_path = f"video/{base_filename}.mp4"
    video_start_message = f"🎬 **動画生成開始**\nテーマ: {theme}\n通常版: {base_filename}.mp4"
    if quiz_data_endurance:
        video_start_message += f"\n耐久版: {endurance_filename}.mp4"
    send_discord_notification(video_start_message, username="動画生成Bot")
    
    thumbnail_path = create_advanced_quiz_video(quiz_data, base_filename, output_path=video_path)
    
    # 耐久版動画生成 (必要に応じて)
    video_path_endurance = None
    if quiz_data_endurance:
        video_path_endurance = f"video/{endurance_filename}.mp4"
        logging.info("耐久版動画生成開始...")
        # 耐久版タイトルを調整
        endurance_title = quiz_data_endurance.get("title", "").replace("クイズ", "耐久クイズ")
        if "耐久" not in endurance_title:
            endurance_title = f"【{len(quiz_data_endurance['quiz_data'])}問連続耐久】{endurance_title}"
        quiz_data_endurance["title"] = endurance_title
        try:
            create_horizontal_endurance_quiz(quiz_data_endurance, endurance_filename, output_path=video_path_endurance)
        except Exception as e:
            logging.error(f"耐久版動画生成中にエラー発生: {e}")
            import traceback
            traceback.print_exc()
            send_discord_notification(f"❌ **耐久版動画生成失敗**\nエラー: {str(e)[:200]}", is_error=True)
    
    # 動画生成完了チェック
    if not os.path.exists(video_path):
        error_msg = f"❌ 通常動画生成に失敗しました。出力ファイルが見つかりません: {video_path}"
        logging.error(error_msg)
        send_discord_notification(f"❌ **通常動画生成失敗**\nテーマ: {theme}", username="動画生成Bot")
        return
    
    # Discord通知: 動画生成完了
    video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    video_end_message = f"✅ **動画生成完了**\nテーマ: {theme}\n通常版: {video_size_mb:.1f}MB"
    
    if video_path_endurance and os.path.exists(video_path_endurance):
        endurance_size_mb = os.path.getsize(video_path_endurance) / (1024 * 1024)
        video_end_message += f"\n耐久版: {endurance_size_mb:.1f}MB"
        logging.info(f"耐久版動画ファイル生成確認: {video_path_endurance} ({endurance_size_mb:.1f}MB)")
    
    logging.info(f"通常版動画ファイル生成確認: {video_path} ({video_size_mb:.1f}MB)")
    send_discord_notification(video_end_message, username="動画生成Bot")

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) # JST
    publish_time_jst = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if now > publish_time_jst:
        publish_time_jst += datetime.timedelta(days=1)
    publish_time_utc = publish_time_jst.astimezone(datetime.timezone.utc)
    
    logging.info("[7/8] YouTubeアップロード開始...")
    
    # 通常版のアップロード
    upload_start_message = f"📺 **YouTubeアップロード開始**\nテーマ: {theme}\n通常版公開予定: {publish_time_jst.strftime('%Y-%m-%d %H:%M')}"
    send_discord_notification(upload_start_message, username="YouTubeアップロードBot")
    video_id, video_url = upload_to_youtube(
        service=youtube_service, video_path=video_path, title=title,
        description=quiz_data.get("description", ""),
        tags=quiz_data.get("tags", []),
        publish_at=publish_time_utc,
        thumbnail_path=thumbnail_path
    )
    
    # 耐久版のアップロード (必要に応じて)
    video_id_endurance = None
    video_url_endurance = None
    if video_path_endurance and os.path.exists(video_path_endurance):
        # 耐久版は30分遅らせて公開
        endurance_publish_time_jst = publish_time_jst + datetime.timedelta(minutes=30)
        endurance_publish_time_utc = endurance_publish_time_jst.astimezone(datetime.timezone.utc)
        
        endurance_title = quiz_data_endurance.get("title", "")
        endurance_description = quiz_data_endurance.get("description", "").replace("10問", f"{len(quiz_data_endurance['quiz_data'])}問")
        endurance_tags = quiz_data_endurance.get("tags", []) + ["耐久クイズ", "10分動画", "横型"]
        
        logging.info("耐久版YouTubeアップロード開始...")
        video_id_endurance, video_url_endurance = upload_to_youtube(
            service=youtube_service, video_path=video_path_endurance, title=endurance_title,
            description=endurance_description,
            tags=endurance_tags,
            publish_at=endurance_publish_time_utc
        )
    
    # Discord通知: YouTubeアップロード結果
    upload_result_message = ""
    if video_id:
        upload_result_message += f"✅ **通常版アップロード成功**\n動画URL: {video_url}\n公開予定: {publish_time_jst.strftime('%Y-%m-%d %H:%M')}"
    else:
        upload_result_message += f"❌ **通常版アップロード失敗**\n動画ファイル: {video_path}"
    
    if video_id_endurance:
        endurance_publish_time_jst = publish_time_jst + datetime.timedelta(minutes=30)
        upload_result_message += f"\n\n✅ **耐久版アップロード成功**\n動画URL: {video_url_endurance}\n公開予定: {endurance_publish_time_jst.strftime('%Y-%m-%d %H:%M')}"
    elif video_path_endurance:
        upload_result_message += f"\n\n❌ **耐久版アップロード失敗**\n動画ファイル: {video_path_endurance}"
    
    send_discord_notification(upload_result_message, username="YouTubeアップロードBot")
    
    if not video_id:
        error_msg = f"通常版YouTubeアップロードに失敗しました。動画ファイルは {video_path} に保存されています。"
        logging.error(error_msg)
        print(f"ERROR: {error_msg}")
        
        # Discord通知（アップロード失敗）
        try:
            upload_error_notification = f"⚠️ **通常版アップロード失敗**\n\n" \
                f"**タイトル:** {title}\n" \
                f"**動画ファイル:** {video_path}\n" \
                f"**ファイルサイズ:** {os.path.getsize(video_path):,} bytes\n\n" \
                f"動画は正常に生成されましたが、YouTubeへのアップロードに失敗しました。手動でアップロードしてください。"
            send_discord_notification(upload_error_notification)
        except Exception as discord_error:
            logging.warning(f"Discord通知の送信に失敗: {discord_error}")
        return

    logging.info("[8/8] スプレッドシート更新中...")
    total_tokens = plan_tokens + script_tokens_normal
    if quiz_data_endurance:
        total_tokens += script_tokens_endurance
    yen = total_tokens * 0.23 / 1000
    script_json_string = json.dumps(quiz_data, ensure_ascii=False)
    
    # 通常版をスプレッドシートに記録
    row_data = [
        datetime.datetime.now().strftime("%Y/%m/%d"), video_url, video_id, title,
        script_json_string, plan_prompt,
        "", "", "", "", "", # 再生数, いいね, コメント, 分析【1d】, 計画【1d】 (初期値は空)
        total_tokens, f"¥{yen:.2f}"
    ]
    
    try:
        append_new_video(sheet, row_data)
        logging.info("通常版スプレッドシート更新完了")
        
        # 耐久版もスプレッドシートに記録 (成功した場合のみ)
        if video_id_endurance and quiz_data_endurance:
            endurance_script_json = json.dumps(quiz_data_endurance, ensure_ascii=False)
            endurance_row_data = [
                datetime.datetime.now().strftime("%Y/%m/%d"), video_url_endurance, video_id_endurance, 
                quiz_data_endurance.get("title", ""),
                endurance_script_json, plan_prompt,
                "", "", "", "", "", # 初期値は空
                script_tokens_endurance, f"¥{script_tokens_endurance * 0.23 / 1000:.2f}"
            ]
            append_new_video(sheet, endurance_row_data)
            logging.info("耐久版スプレッドシート更新完了")
        
        logging.info("[8/8] 全スプレッドシート更新完了")
    except Exception as e:
        logging.error(f"スプレッドシート更新エラー: {str(e)}")
    
    # 全処理完了後に使用済みvoiceファイルを削除
    logging.info("使用済みvoiceファイルを削除中...")
    cleanup_voice_files(base_filename)
    if quiz_data_endurance:
        cleanup_voice_files(endurance_filename)
    
    end_time = datetime.datetime.now()
    total_duration = (end_time - app_start_time).total_seconds()
    logging.info(f"✅ 全処理完了! 総所要時間: {total_duration:.1f}秒 ({total_duration/60:.1f}分)")
    logging.info(f"トークン数: {total_tokens} (¥{yen:.2f})")
    logging.info("--- 漢字クイズ動画 生成フロー完了 ---")

    # NOTE: 分析フローは run_quiz_bot.bat で別途実行されます

if __name__ == "__main__":
    app_start_time = datetime.datetime.now()
    logging.info("=== 漢字クイズBot 起動 ===")
    logging.info(f"実行開始時刻: {app_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Discord通知: 処理開始
    start_message = f"🚀 **漢字クイズBot 処理開始**\n開始時刻: {app_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    send_discord_notification(start_message, username="処理開始Bot")
    
    youtube_service = None
    vv_handler = VoicevoxHandler(engine_path=VOICEVOX_ENGINE_PATH)
    
    try:
        logging.info("🔐 YouTube APIの認証を開始します...")
        youtube_service = get_authenticated_service()
        if not youtube_service:
            raise Exception("YouTube APIの認証に失敗しました。get_authenticated_serviceがNoneを返しました。")
        logging.info("✅ YouTube APIの認証に成功しました。")

        logging.info("🎤 Voicevoxエンジンの起動を開始します...")
        if not vv_handler.start_engine(): 
            raise Exception("Voicevoxエンジンの起動に失敗しました。")
        logging.info("✅ Voicevoxエンジンの起動に成功しました。")
        
        run_creation_flow(vv_handler, youtube_service)

        # 分析レポートはmetrics-collection jobで実行されるためスキップ
        logging.info("--- 分析レポートはmetrics-collection jobに委譲 ---")

    except RefreshError as e:
        error_message = "YouTube APIの認証トークンの有効期限が切れました。"
        tb_str = traceback.format_exc()
        logging.error(f"{error_message}\n{tb_str}")
        error_notification = format_error_notification("app.py", error_message, tb_str)
        error_notification += "\n\n**対処法:** `token.pickle`ファイルを削除し、手動でスクリプトを再実行して再認証してください。"
        send_discord_notification(error_notification, username="エラー通知Bot", is_error=True)

    except Exception as e:
        error_message = f"app.pyの実行中に予期せぬエラーが発生しました。"
        tb_str = traceback.format_exc()
        logging.error(f"{error_message}\n{tb_str}")
        send_discord_notification(
            format_error_notification("app.py", error_message, tb_str),
            username="エラー通知Bot",
            is_error=True
        )

    finally:
        logging.info("🧹 処理が完了したため、クリーンアップします。")
        vv_handler.stop_engine()
        
        app_end_time = datetime.datetime.now()
        app_total_duration = (app_end_time - app_start_time).total_seconds()
        logging.info(f"🎉 全ての処理が完了しました。総実行時間: {app_total_duration:.1f}秒 ({app_total_duration/60:.1f}分)")
        logging.info(f"終了時刻: {app_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("=== 漢字クイズBot 終了 ===")
        
        # Discord通知: 全処理完了
        complete_message = f"🎉 **全処理完了**\n実行時間: {app_total_duration/60:.1f}分\n終了時刻: {app_end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        send_discord_notification(complete_message, username="完了通知Bot")