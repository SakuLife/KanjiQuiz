# youtube_handler.py
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time
from datetime import datetime

# このファイルを実行する際に、ユーザー認証が必要です
# 絶対パスで指定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "..", "json", "client_secret.json")
TOKEN_PICKLE_FILE = os.path.join(BASE_DIR, "..", "token.pickle")

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
# 分析とアップロードに必要な権限
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload", 
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def get_authenticated_service():
    """
    OAuth 2.0認証を行い、認証済みのYouTubeサービスオブジェクトを返す
    GitHub Actions環境では環境変数から認証情報を取得して自動更新
    """
    import logging
    from google.oauth2.credentials import Credentials

    creds = None
    logging.info("YouTube API認証開始...")

    # GitHub Actions環境の確認（環境変数でリフレッシュトークンが提供されている場合）
    yt_client_id = os.environ.get('YT_CLIENT_ID')
    yt_client_secret = os.environ.get('YT_CLIENT_SECRET')
    yt_refresh_token = os.environ.get('YT_REFRESH_TOKEN')

    if yt_client_id and yt_client_secret and yt_refresh_token:
        # GitHub Actions環境: 環境変数から認証情報を構築
        logging.info("GitHub Actions環境を検出: 環境変数から認証情報を取得します")
        try:
            creds = Credentials(
                None,  # token (アクセストークン) は自動で取得
                refresh_token=yt_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=yt_client_id,
                client_secret=yt_client_secret,
                scopes=SCOPES
            )

            # トークンをリフレッシュして最新のアクセストークンを取得
            logging.info("リフレッシュトークンからアクセストークンを取得中...")
            creds.refresh(Request())
            logging.info("✅ GitHub Actions環境でのYouTube API認証に成功しました")

            service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
            logging.info("YouTube APIサービスの初期化に成功")
            return service

        except Exception as e:
            logging.error(f"GitHub Actions環境での認証に失敗: {e}")
            logging.error("リフレッシュトークンが無効か期限切れの可能性があります")
            logging.error("解決方法: YOUTUBE_TOKEN_FIX.md を参照してください")
            raise

    # ローカル環境: token.pickleを使用
    logging.info("ローカル環境を検出: token.pickleから認証情報を取得します")

    # token.pickleファイルが、ユーザーのアクセストークンとリフレッシュトークンを保存します。
    if os.path.exists(TOKEN_PICKLE_FILE):
        try:
            with open(TOKEN_PICKLE_FILE, "rb") as token:
                creds = pickle.load(token)
            logging.info("保存された認証情報を読み込みました")
        except Exception as e:
            logging.warning(f"認証情報の読み込みに失敗: {e}")
            creds = None

    # 有効な認証情報がない場合は、ユーザーにログインしてもらう
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logging.info("アクセストークンを更新中...")
                print("INFO: Refreshing access token...")
                creds.refresh(Request())
                logging.info("アクセストークンの更新に成功")
            except Exception as e:
                logging.error(f"トークンの更新に失敗: {e}")
                logging.error("リフレッシュトークンが無効か期限切れの可能性があります")
                # ネットワークエラーまたはリフレッシュトークン期限切れの場合
                if "invalid_grant" in str(e) or "NameResolutionError" in str(e) or "Max retries exceeded" in str(e):
                    logging.info("認証エラーのため、token.pickleを削除して再認証します")
                    logging.info("解決方法: YOUTUBE_TOKEN_FIX.md を参照してください")
                    try:
                        os.remove(TOKEN_PICKLE_FILE)
                        logging.info("token.pickleファイルを削除しました")
                    except FileNotFoundError:
                        pass
                creds = None

        if not creds:
            try:
                # 初回実行時、ブラウザが開いて認証を求められます
                logging.info("新しい認証を開始...")
                print("INFO: A browser window will open for authentication.")
                if not os.path.exists(CLIENT_SECRETS_FILE):
                    raise FileNotFoundError(f"クライアント秘密ファイルが見つかりません: {CLIENT_SECRETS_FILE}")

                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                logging.info("新しい認証に成功")
            except Exception as e:
                logging.error(f"認証プロセスに失敗: {e}")
                raise

        # 次回実行のために認証情報を保存
        try:
            with open(TOKEN_PICKLE_FILE, "wb") as token:
                pickle.dump(creds, token)
            logging.info("認証情報を保存しました")
        except Exception as e:
            logging.warning(f"認証情報の保存に失敗: {e}")

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        logging.info("YouTube APIサービスの初期化に成功")
        return service
    except Exception as e:
        logging.error(f"YouTube APIサービスの初期化に失敗: {e}")
        raise

def upload_to_youtube(service, video_path, title, description, tags, category_id="27", publish_at=None, thumbnail_path=None):
    """
    動画をYouTubeにアップロードし、指定された日時に予約投稿する
    """
    import logging
    import traceback
    
    logging.info(f"YouTubeアップロード開始: '{title}'")
    logging.info(f"動画ファイル: {video_path}")
    
    try:
        # 動画ファイルの存在確認
        if not os.path.exists(video_path):
            error_msg = f"動画ファイルが見つかりません: {video_path}"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return None, None
            
        file_size = os.path.getsize(video_path)
        if file_size == 0:
            error_msg = f"動画ファイルが空です: {video_path}"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return None, None
            
        logging.info(f"動画ファイルサイズ: {file_size:,} bytes")
        try:
            print(f"INFO: Uploading video to YouTube: '{title}' ({file_size:,} bytes)")
        except UnicodeEncodeError:
            print(f"INFO: Uploading video to YouTube: (title with special characters) ({file_size:,} bytes)")

        # リクエストボディの準備
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "selfDeclaredMadeForKids": False 
            }
        }

        # 予約投稿のロジック
        if publish_at:
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = publish_at.isoformat()
            publish_time_str = publish_at.astimezone().strftime('%Y年%m月%d日 %H:%M (JST)')
            logging.info(f"予約投稿設定: {publish_time_str}")
            print(f"INFO: この動画は {publish_time_str} に予約投稿されます。")
        else:
            body["status"]["privacyStatus"] = "public"
            logging.info("即座に公開設定")
        
        # アップロード実行
        logging.info("YouTubeアップロード実行中...")
        print("INFO: アップロード中...")
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = service.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        
        # アップロード進行状況の監視
        response = None
        while response is None:
            try:
                print(".", end="", flush=True)
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"\rアップロード進行状況: {progress}%", end="", flush=True)
            except Exception as chunk_error:
                logging.warning(f"アップロード中の一時的なエラー: {chunk_error}")
                print(f"\n一時的なエラー: {chunk_error}")
                # 少し待ってリトライ
                time.sleep(5)
                continue
        
        print("\n", end="")  # 改行
        
        if response:
            video_id = response.get("id")
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                status_message = "予約投稿" if publish_at else "公開"
                success_msg = f"YouTubeへのアップロードと{status_message}設定が完了しました！"
                logging.info(success_msg)
                logging.info(f"Video ID: {video_id}")
                logging.info(f"URL: {video_url}")
                print(success_msg)
                print(f"   Video ID: {video_id}")
                print(f"   URL: {video_url}")

                # カスタムサムネイルのアップロード
                if thumbnail_path and os.path.exists(thumbnail_path):
                    upload_thumbnail(service, video_id, thumbnail_path)

                return video_id, video_url
            else:
                error_msg = "レスポンスにVideo IDが含まれていません"
                logging.error(error_msg)
                print(f"ERROR: {error_msg}")
                return None, None
        else:
            error_msg = "YouTubeからのレスポンスが空です"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return None, None

    except Exception as e:
        error_msg = f"YouTubeへのアップロード中にエラーが発生しました: {str(e)}"
        logging.error(error_msg)
        logging.error(f"トレースバック: {traceback.format_exc()}")
        print(f"ERROR: {error_msg}")
        print(f"詳細: {traceback.format_exc()}")
        return None, None

def get_video_stats_bulk(service, video_ids):
    """
    複数の動画IDの統計情報を一括で取得する
    """
    print(f"INFO: {len(video_ids)}件の動画の統計情報を一括取得中...")
    stats_dict = {}
    # APIは一度に50件までIDを処理できる
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        try:
            request = service.videos().list(
                part="statistics",
                id=",".join(chunk)
            )
            response = request.execute()
            
            for item in response.get("items", []):
                video_id = item["id"]
                stats = item["statistics"]
                stats_dict[video_id] = {
                    "views": int(stats.get("viewCount", "0")),
                    "likes": int(stats.get("likeCount", "0")),
                    "comments": int(stats.get("commentCount", "0"))
                }
        except Exception as e:
            print(f"❌ YouTube統計情報の一括取得中にエラー (Chunk {i//50 + 1}): {e}")
            # エラーが発生しても、取得できた分だけで処理を続ける
            continue
    
    print(f"{len(stats_dict)}件の動画統計情報を取得しました。")
    return stats_dict

def get_video_comments(service, video_id, max_results=50):
    """
    指定された動画のコメントを取得する
    """
    print(f"INFO: 動画 {video_id} のコメントを取得中...")
    try:
        request = service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            order="relevance"  # 関連性の高い順で取得
        )
        response = request.execute()
        
        comments = []
        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "text": comment["textDisplay"],
                "author": comment["authorDisplayName"],
                "likes": comment["likeCount"],
                "published": comment["publishedAt"]
            })
        
        print(f"INFO: {len(comments)}件のコメントを取得しました。")
        return comments
    except Exception as e:
        print(f"WARNING: コメント取得中にエラー: {e}")
        print("INFO: コメント機能をスキップして処理を継続します。")
        return []

def upload_thumbnail(service, video_id, thumbnail_path):
    """
    カスタムサムネイルをYouTubeにアップロードする
    """
    import logging
    import traceback

    logging.info(f"サムネイルアップロード開始: {thumbnail_path}")
    print(f"INFO: サムネイルをアップロード中...")

    try:
        # サムネイルファイルの存在確認
        if not os.path.exists(thumbnail_path):
            error_msg = f"サムネイルファイルが見つかりません: {thumbnail_path}"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return False

        file_size = os.path.getsize(thumbnail_path)
        if file_size == 0:
            error_msg = f"サムネイルファイルが空です: {thumbnail_path}"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return False

        logging.info(f"サムネイルファイルサイズ: {file_size:,} bytes")
        print(f"INFO: サムネイルサイズ: {file_size:,} bytes")

        # メディアアップロードの準備
        media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")

        # サムネイルアップロード実行
        request = service.thumbnails().set(
            videoId=video_id,
            media_body=media
        )
        response = request.execute()

        if response:
            success_msg = "サムネイルアップロードが完了しました！"
            logging.info(success_msg)
            print(success_msg)
            return True
        else:
            error_msg = "サムネイルアップロードのレスポンスが空です"
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return False

    except Exception as e:
        error_msg = f"サムネイルアップロード中にエラーが発生しました: {str(e)}"
        logging.error(error_msg)
        logging.error(f"トレースバック: {traceback.format_exc()}")
        print(f"ERROR: {error_msg}")
        print(f"詳細: {traceback.format_exc()}")
        return False