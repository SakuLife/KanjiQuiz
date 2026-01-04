# g_sheet_handler.py
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import json

load_dotenv()
SHEET_ID = os.getenv("SPREADSHEET_ID")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "..", "json", "credentials.json")

EXPECTED_HEADERS = ['投稿日時', '動画URL', 'Video ID', 'タイトル', '台本', '実行した計画', '再生数', 'いいね', 'コメント', '分析【1d】', '計画【1d】', 'トークン数', '料金']

COLORS = {
    "info":       {"red": 218/255, "green": 227/255, "blue": 243/255},
    "stats":      {"red": 255/255, "green": 229/255, "blue": 204/255},
    "plan":       {"red": 255/255, "green": 242/255, "blue": 204/255},
    "analysis":   {"red": 217/255, "green": 234/255, "blue": 211/255},
    "cost":       {"red": 239/255, "green": 239/255, "blue": 239/255}
}

def get_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        gc = gspread.authorize(credentials)
        return gc.open_by_key(SHEET_ID).sheet1
    except Exception as e:
        print(f"ERROR: Googleスプレッドシートへの接続に失敗: {e}")
        return None

def _format_row_compatible(sheet, row_index):
    """指定された行に書式を適用する"""
    print(f"INFO: Formatting row {row_index}...")
    try:
        
        col_map = {name: gspread.utils.rowcol_to_a1(1, i + 1)[:-1] for i, name in enumerate(EXPECTED_HEADERS)}

        format_map = {
            "info":     ['投稿日時', '動画URL', 'Video ID', 'タイトル', '台本', '実行した計画'],
            "stats":    ['再生数', 'いいね', 'コメント'],
            "analysis": ['分析【1d】'],
            "plan":     ['計画【1d】'],
            "cost":     ['トークン数', '料金']
        }

        for key, columns in format_map.items():
            for col_name in columns:
                if col_name in col_map:
                    cell_a1 = f"{col_map[col_name]}{row_index}"
                    sheet.format(cell_a1, {"backgroundColor": COLORS[key]})
                    
    except Exception as e:
        print(f"⚠️ 警告: 行のフォーマット中にエラーが発生しました: {e}")

def append_new_video(sheet, row_data):
    try:
        col_map = {name: i + 1 for i, name in enumerate(EXPECTED_HEADERS)}
        
        # デバッグ情報を追加
        print(f"DEBUG: 書き込み予定データ: {row_data[:3]}...")
        
        # append_rowを実行
        sheet.append_row(row_data, value_input_option='USER_ENTERED')
        
        # 書き込み確認
        all_values = sheet.get_all_values()
        new_row_index = len(all_values)
        if all_values and len(all_values[-1]) > 2 and all_values[-1][2]:
            print(f"DEBUG: 書き込み成功確認 - Video ID: {all_values[-1][2]}")
        else:
            print("WARNING: 書き込みデータが空の可能性があります")
            # 代替方法: 直接セル範囲を指定して書き込み
            range_name = f"A{new_row_index}:M{new_row_index}"
            sheet.update(range_name, [row_data], value_input_option='USER_ENTERED')
            print(f"DEBUG: 代替方法で書き込み実行: {range_name}")
        
        _format_row_compatible(sheet, new_row_index)
        print("INFO: スプレッドシートに新しい動画情報を記録し、書式を適用しました。")
    except Exception as e:
        print(f"ERROR: スプレッドシートへの書き込み中にエラー: {e}")
        import traceback
        traceback.print_exc()

def get_all_videos_for_report(sheet):
    """レポート対象となるすべての動画情報をスプレッドシートから取得する"""
    print("INFO: スプレッドシートから全動画のレポート用データを取得中...")
    try:
        expected_headers = ['投稿日時', '動画URL', 'Video ID', 'タイトル', '台本', '実行した計画', '再生数', 'いいね', 'コメント', '分析【1d】', '計画【1d】', 'トークン数', '料金']
        records = sheet.get_all_records(expected_headers=expected_headers)
        videos = []
        for i, row in enumerate(records):
            if row.get("Video ID"):
                videos.append({
                    "row_num": i + 2,
                    "video_id": row["Video ID"],
                    "upload_date": row["投稿日時"],
                    "title": row["タイトル"],
                    "script": row.get("台本"),
                    "previous_plan": row.get("実行した計画"),
                    "previous_analysis": row.get("分析【1d】"),
                    "previous_views": int(str(row.get("再生数", "0")).replace(",", "") or "0"),
                    "previous_likes": int(str(row.get("いいね", "0")).replace(",", "") or "0"),
                    "previous_comments": int(str(row.get("コメント", "0")).replace(",", "") or "0"),
                })
        print(f"INFO: {len(videos)}件の動画データを取得しました。")
        return videos
    except Exception as e:
        print(f"ERROR: 全動画データの取得中にエラー: {e}")
        return []

def update_report_data(sheet, col_map, data):
    """動画の統計情報と分析結果をスプレッドシートに上書き更新する"""
    import time
    row_num = data['row_num']
    print(f"INFO: {row_num}行目のレポートデータを更新中...")
    try:
        # バッチ更新用のデータを準備
        batch_data = []

        # 統計情報の更新範囲を追加
        stats_range = f"{gspread.utils.rowcol_to_a1(row_num, col_map['再生数'])}:{gspread.utils.rowcol_to_a1(row_num, col_map['コメント'])}"
        batch_data.append({
            'range': stats_range,
            'values': [[data['stats']['views'], data['stats']['likes'], data['stats']['comments']]]
        })

        # 分析と計画の更新 (あれば)
        if 'insight' in data:
            analysis_cell = gspread.utils.rowcol_to_a1(row_num, col_map['分析【1d】'])
            plan_cell = gspread.utils.rowcol_to_a1(row_num, col_map['計画【1d】'])

            # 事前にトークン数と料金を読み取り (バッチ更新前に1回だけ)
            tokens_col_name, cost_col_name = "トークン数", "料金"
            tokens_cell_a1 = gspread.utils.rowcol_to_a1(row_num, col_map[tokens_col_name])
            cost_cell_a1 = gspread.utils.rowcol_to_a1(row_num, col_map[cost_col_name])

            # 読み取りを1回のbatch_getで実行
            cell_values = sheet.batch_get([tokens_cell_a1, cost_cell_a1])
            prev_tokens = int(cell_values[0][0][0] if cell_values[0] and cell_values[0][0] else "0")
            prev_cost_str = cell_values[1][0][0] if cell_values[1] and cell_values[1][0] else "¥0"
            prev_cost = float(prev_cost_str.replace("¥", "").replace(",", ""))

            new_tokens = prev_tokens + data['insight'].get('tokens', 0)
            new_cost = prev_cost + (data['insight'].get('tokens', 0) * 0.23 / 1000)

            # 分析、計画、トークン、料金を一括更新データに追加
            analysis_plan_range = f"{analysis_cell}:{plan_cell}"
            batch_data.append({
                'range': analysis_plan_range,
                'values': [[data['insight']['analysis'], data['insight']['plan']]]
            })

            tokens_cost_range = f"{tokens_cell_a1}:{cost_cell_a1}"
            batch_data.append({
                'range': tokens_cost_range,
                'values': [[new_tokens, f"¥{new_cost:,.2f}"]]
            })

        # バッチ更新を1回で実行 (APIコールを大幅に削減)
        sheet.batch_update(batch_data, value_input_option='USER_ENTERED')

        # レート制限対策: 0.1秒待機
        time.sleep(0.1)

        return True
    except Exception as e:
        print(f"ERROR: {row_num}行目の更新中にエラー: {e}")
        # レート制限エラーの場合、待機してリトライ
        if "429" in str(e) or "Quota exceeded" in str(e):
            print(f"WARNING: レート制限エラー検出。10秒待機してリトライします...")
            time.sleep(10)
            try:
                # リトライ
                sheet.batch_update(batch_data, value_input_option='USER_ENTERED')
                return True
            except Exception as retry_error:
                print(f"ERROR: リトライも失敗: {retry_error}")
                return False
        return False

def fetch_past_data(sheet):
    """動画作成の参考にするため、過去のデータを取得する"""
    print("INFO: スプレッドシートから過去の分析データを取得中...")
    try:
        expected_headers = ['投稿日時', '動画URL', 'Video ID', 'タイトル', '台本', '実行した計画', '再生数', 'いいね', 'コメント', '分析【1d】', '計画【1d】', 'トークン数', '料金']
        records = sheet.get_all_records(expected_headers=expected_headers)
        past_data = []
        for row in records:
            views = int(str(row.get("再生数", "0")).replace(",", "") or "0")
            theme = "不明"
            try:
                script_json = row.get("台本", '{}')
                if script_json and script_json.strip():
                    script_data = json.loads(script_json)
                    theme = script_data.get("theme", "不明")
            except (json.JSONDecodeError, AttributeError):
                pass
            
            past_data.append({
                "theme": theme, "views": views,
                "analysis": row.get("分析【1d】"),
                "plan": row.get("計画【1d】"),
            })
        print(f"INFO: {len(past_data)}件の過去データを取得しました。")
        return past_data
    except Exception as e:
        print(f"ERROR: 過去データの取得中にエラー: {e}")
        return []
