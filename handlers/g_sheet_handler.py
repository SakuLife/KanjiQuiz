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
    row_num = data['row_num']
    print(f"INFO: {row_num}行目のレポートデータを更新中...")
    try:
        # 統計情報の上書き
        stats_range = f"{gspread.utils.rowcol_to_a1(row_num, col_map['再生数'])}:{gspread.utils.rowcol_to_a1(row_num, col_map['コメント'])}"
        sheet.update(stats_range, [[data['stats']['views'], data['stats']['likes'], data['stats']['comments']]], value_input_option='USER_ENTERED')

        # 分析と計画の更新 (あれば)
        if 'insight' in data:
            analysis_cell = gspread.utils.rowcol_to_a1(row_num, col_map['分析【1d】'])
            plan_cell = gspread.utils.rowcol_to_a1(row_num, col_map['計画【1d】'])
            sheet.update(analysis_cell, [[data['insight']['analysis']]])
            sheet.update(plan_cell, [[data['insight']['plan']]])
            
            # トークン数と料金を更新
            tokens_col_name, cost_col_name = "トークン数", "料金"
            tokens_cell_a1 = gspread.utils.rowcol_to_a1(row_num, col_map[tokens_col_name])
            cost_cell_a1 = gspread.utils.rowcol_to_a1(row_num, col_map[cost_col_name])
            
            prev_tokens = int(sheet.acell(tokens_cell_a1).value or "0")
            prev_cost_str = sheet.acell(cost_cell_a1).value or "¥0"
            prev_cost = float(prev_cost_str.replace("¥", "").replace(",", ""))

            new_tokens = prev_tokens + data['insight'].get('tokens', 0)
            new_cost = prev_cost + (data['insight'].get('tokens', 0) * 0.23 / 1000)
            
            sheet.update(f"{tokens_cell_a1}:{cost_cell_a1}", [[new_tokens, f"¥{new_cost:,.2f}"]], value_input_option='USER_ENTERED')

        return True
    except Exception as e:
        print(f"ERROR: {row_num}行目の更新中にエラー: {e}")
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
