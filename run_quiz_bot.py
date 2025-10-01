#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kanji Quiz Bot Python Runner
Windows Batch Fileの代替として、Pythonで同様の機能を提供
"""
import subprocess
import sys
import os
import datetime
import logging
from pathlib import Path

def setup_logging():
    """ログファイルをセットアップ"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"quiz_bot_{timestamp}.log"
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file

def check_virtual_env():
    """仮想環境の存在確認"""
    # GitHub Actionsの場合はスキップ
    if '--github-actions' in sys.argv:
        logging.info("Skipping virtual environment check for GitHub Actions")
        return True

    python_exe = Path("new_venv/Scripts/python.exe")
    if not python_exe.exists():
        logging.error("Virtual environment not found at %s", python_exe)
        return False
    return True

def load_env_file():
    """簡単な.envファイル読み込み"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        logging.info("Environment variables loaded from .env")

def setup_github_actions_env():
    """GitHub Actions環境用の設定"""
    logging.info("Setting up GitHub Actions environment...")

    # VOICEVOXはGitHub Actionsでは使用しない
    os.environ['VOICEVOX_DISABLED'] = 'true'

    # フォントパスをLinux用に設定
    os.environ['FONT_PATH_BOLD'] = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
    os.environ['FONT_PATH_REGULAR'] = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

    # GitHub Actionsモードフラグ
    os.environ['GITHUB_ACTIONS_MODE'] = 'true'

    logging.info("GitHub Actions environment setup completed")

def run_python_script(script_name, description):
    """Pythonスクリプトを実行"""
    logging.info("[%s] %s", script_name, description)

    # GitHub Actionsの場合はシステムPythonを使用
    if '--github-actions' in sys.argv:
        python_exe = "python"  # システムPython
    else:
        python_exe = Path("new_venv/Scripts/python.exe")

    script_path = Path("core") / script_name
    
    try:
        result = subprocess.run(
            [str(python_exe), str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Unicode エラーを置換文字で処理
            timeout=300  # 5分タイムアウト
        )
        
        if result.stdout:
            logging.info("STDOUT:\n%s", result.stdout)
        if result.stderr:
            logging.warning("STDERR:\n%s", result.stderr)
            
        if result.returncode == 0:
            logging.info("%s completed successfully", description)
            return True
        else:
            logging.warning("%s failed with exit code %d", description, result.returncode)
            return False
            
    except subprocess.TimeoutExpired:
        timeout_min = 10 if github_actions else 5
        logging.error("%s timed out after %d minutes", description, timeout_min)
        return False
    except Exception as e:
        logging.error("Error running %s: %s", description, str(e))
        return False

def main():
    """メイン実行関数"""
    print("Starting Kanji Quiz Bot...")
    
    # ロギングセットアップ
    log_file = setup_logging()
    logging.info("=" * 50)
    logging.info("Kanji Quiz Bot - Python Runner")
    logging.info("Log file: %s", log_file)
    logging.info("=" * 50)
    
    # GitHub Actions環境チェック
    if '--github-actions' in sys.argv:
        setup_github_actions_env()
    else:
        # 環境変数読み込み
        load_env_file()

    # 仮想環境チェック
    if not check_virtual_env():
        logging.error("Cannot continue without virtual environment")
        return 1
    
    # 結果追跡
    app_success = False
    reporter_success = False
    
    # Step 1: 動画生成
    logging.info("Step 1/2: Running video creation...")
    app_success = run_python_script("app.py", "Video creation")
    
    # Step 2: 分析とレポート（app.pyが失敗しても実行）
    logging.info("Step 2/2: Running analysis and reporting...")
    reporter_success = run_python_script("reporter.py", "Analysis and reporting")
    
    # 最終結果
    logging.info("=" * 50)
    if app_success and reporter_success:
        logging.info("STATUS: All tasks completed successfully")
        final_exit = 0
    elif reporter_success:
        logging.info("STATUS: Analysis completed, but video creation had issues")
        final_exit = 1
    elif app_success:
        logging.info("STATUS: Video creation completed, but analysis had issues") 
        final_exit = 1
    else:
        logging.info("STATUS: Both tasks had issues - check logs for details")
        final_exit = 2
    
    logging.info("Log file saved: %s", log_file)
    logging.info("=" * 50)
    
    print(f"\nExecution completed. Check log file: {log_file}")
    return final_exit

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)