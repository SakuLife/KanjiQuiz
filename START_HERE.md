# 漢字クイズBot 実行ガイド

## メイン実行ファイル

### 🚀 **run_quiz_bot.bat** ← これを使え！
**毎日の自動実行用のメインファイル**
- 動画生成 + YouTube投稿 + 分析レポート を一括実行
- エラー処理とログ記録が充実
- タスクスケジューラからの自動実行に最適

### 📝 **run_quiz_bot.py** 
Pythonランナー（上記batファイルの代替）
- より詳細なエラーハンドリング
- タイムアウト機能付き
- バッチファイルが動かない場合の代替

## 実行方法

### 手動実行
```bash
# メイン実行（推奨）
run_quiz_bot.bat

# Python版（代替）
python run_quiz_bot.py
```

### タスクスケジューラ設定
- **実行ファイル**: `D:\Python\KanjiQuiz\run_quiz_bot.bat`
- **開始ディレクトリ**: `D:\Python\KanjiQuiz`
- **実行時刻**: 毎日 7:00 AM

## フォルダ構成

```
📦 KanjiQuiz/
├── 🔥 run_quiz_bot.bat          # メイン実行ファイル
├── 🐍 run_quiz_bot.py           # Python代替実行ファイル
├── 📁 core/                     # メインプログラム
│   ├── app.py                   # 動画生成・投稿
│   └── reporter.py              # 分析・レポート
├── 📁 handlers/                 # API処理
├── 📁 logs/                     # ログファイル
├── 📁 archive/                  # 古いファイル保管
│   ├── test_files/              # テストファイル
│   ├── deprecated/              # 非推奨ファイル
│   └── old_batch_files/         # 古いバッチファイル
└── 📁 new_venv/                 # Python仮想環境
```

## ログファイルの場所
- メインログ: `logs/quiz_bot_YYYYMMDD_HHMM.log`
- 最終実行ログ: `logs/last_run.log`

## トラブルシューティング

1. **Virtual environment not found エラー**
   - `new_venv/Scripts/python.exe` が存在するか確認

2. **タスクスケジューラでエラー267009**
   - batファイルのパスが正しく設定されているか確認
   - 開始ディレクトリが `D:\Python\KanjiQuiz` になっているか確認

3. **文字化けする場合**
   - コマンドプロンプトで `chcp 65001` を実行してからbatファイルを実行

## 重要な注意点
- ⚠️ **run_quiz_bot.bat のみ使用すること**
- ⚠️ アーカイブフォルダのファイルは実行しない
- ⚠️ 手動実行時は作業ディレクトリを `D:\Python\KanjiQuiz` に設定