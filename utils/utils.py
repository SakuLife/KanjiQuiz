# utils.py
import json
import re
import os
import datetime

def extract_json(text: str) -> dict:
    """
    AIが生成したテキストからJSONオブジェクトを抽出してパースする関数。
    まずテキスト全体をJSONとしてパースを試み、失敗した場合はコードブロックからの抽出を試みる。
    """
    if not isinstance(text, str):
        return {}

    # 1. テキスト全体をJSONとしてパースを試みる
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass  # 失敗した場合は次のステップへ

    # 2. マークダウンのコードブロックからJSONを抽出してパースを試みる
    # ```json ... ``` または ``` ... ``` の形式に対応
    match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"ERROR: コードブロック内のJSON解析に失敗しました。")
            print(f"--- 抽出されたJSON文字列 ---\n{json_str}\n--------------------")

    print(f"ERROR: JSONの解析に失敗しました。AIの出力が不正な形式です。")
    print(f"--- AIの生出力 ---\n{text}\n--------------------")
    return {} # 最終的に失敗した場合は空の辞書を返す

def extract_block(block_name: str, text: str) -> str:
    """
    指定されたブロック名（例：「分析」）の内容をテキストから抽出する関数
    """
    # ### ブロック名： で始まるパターンを探す
    pattern = f"### {block_name}：(.*?)(?=\n### |$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    else:
        return "" # 見つからなければ空文字を返す

def print_token_cost(tokens: int):
    """
    トークン数と概算コストを表示する関数
    """
    # このレートはOpenAI/Geminiで異なるため、あくまで目安です
    rate = 0.23  # Gemini 1.5 Proの概算レート (1000トークンあたり)
    cost = tokens * rate / 1000
    print(f"--- (参考) 消費トークン: {tokens} / 概算コスト: ¥{cost:.2f} ---")

def get_unique_log_filename(base_name):
    """同じ日に複数回実行された場合、連番を付けてユニークなログファイル名を生成"""
    # プロジェクトルートからlogsディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    base_filename = f"{base_name}_{date_str}"
    
    # 最初は連番なしで試す
    log_file_path = os.path.join(log_dir, f"{base_filename}.log")
    if not os.path.exists(log_file_path):
        return log_file_path
    
    # ファイルが存在する場合は連番を付ける
    counter = 2
    while True:
        log_file_path = os.path.join(log_dir, f"{base_filename}_{counter}.log")
        if not os.path.exists(log_file_path):
            return log_file_path
        counter += 1