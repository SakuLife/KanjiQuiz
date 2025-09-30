# 漢字クイズ動画自動生成システム

YouTube向けの漢字クイズ動画を自動生成し、アップロード、分析まで行う統合システムです。

## 🚀 主な機能

### 1. 動画生成 (`core/app.py`)
- **AI台本生成**: Gemini APIを使用した漢字クイズの台本自動生成
- **音声合成**: VOICEVOX APIによる自然な日本語音声生成
- **動画編集**: MoviePyを使用した高品質な動画自動生成
- **YouTube自動アップロード**: YouTube Data API v3での自動投稿

### 2. データ管理 (`handlers/g_sheet_handler.py`)
- **Google Sheets連携**: 動画データの一元管理
- **統計情報記録**: 再生数、いいね数、コメント数の自動更新
- **書式設定**: セルの色分けによる視覚的なデータ管理

### 3. 分析・レポート (`core/reporter.py`)
- **動画パフォーマンス分析**: AIによる詳細な動画分析
- **改善計画生成**: 次回動画への具体的なアクションプラン
- **日次・週次レポート**: Discord通知による定期的な成果報告

## 📁 プロジェクト構造

```
KanjiQuizProject/
├── core/                    # メインロジック
│   ├── app.py              # 動画生成メインフロー
│   ├── reporter.py         # 分析・レポート機能
│   └── video_generator.py  # 動画生成エンジン
├── handlers/               # 外部API連携
│   ├── gemini_handler.py   # Gemini AI連携
│   ├── voicevox_handler.py # VOICEVOX音声合成
│   ├── youtube_handler.py  # YouTube API連携
│   ├── g_sheet_handler.py  # Google Sheets連携
│   ├── discord_handler.py  # Discord通知
│   └── analysis_ai.py      # 分析AI機能
├── config/                 # 設定ファイル
│   └── prompts.json       # AIプロンプト設定
├── json/                   # 認証情報
│   ├── credentials.json    # Google Sheets認証
│   └── client_secret.json  # YouTube API認証
├── bgm/                    # BGMファイル
├── se/                     # 効果音ファイル
├── image/                  # 画像素材
├── voice/                  # 生成音声ファイル
├── video/                  # 生成動画ファイル
├── logs/                   # ログファイル
└── utils/                  # ユーティリティ
    └── utils.py           # 共通関数
```

## 🛠️ セットアップ

### 1. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定 (`.env`ファイルを作成)
```env
# Google Sheets
SPREADSHEET_ID="your_spreadsheet_id"

# Gemini AI
GEMINI_API_KEY="your_gemini_api_key"

# Discord Webhook
DISCORD_WEBHOOK_URL="your_discord_webhook_url"
DISCORD_WEBHOOK_URL_ERROR="your_error_webhook_url"
```

### 3. 認証ファイルの配置
- `json/credentials.json`: Google Sheets API認証情報
- `json/client_secret.json`: YouTube API認証情報

### 4. VOICEVOX Engineの設定
- VOICEVOX Engineをインストール
- `core/app.py`内のパスを環境に合わせて調整

## 🎯 使用方法

### 動画生成・アップロード
```bash
python core/app.py
```

### 分析・レポート実行
```bash
python core/reporter.py
```

### バッチ実行
```bash
./run_quiz_bot.bat
```

## 📊 Google Spreadsheet構造

| 列名 | 内容 |
|------|------|
| 投稿日時 | 動画投稿日 |
| 動画URL | YouTube URL |
| Video ID | YouTube動画ID |
| タイトル | 動画タイトル |
| 台本 | JSON形式の台本データ |
| 実行した計画 | 前回の改善計画 |
| 再生数 | 最新の再生数 |
| いいね | 最新のいいね数 |
| コメント | 最新のコメント数 |
| 分析【1d】 | AI分析結果 |
| 計画【1d】 | 次回への改善計画 |
| トークン数 | API使用トークン数 |
| 料金 | API使用料金 |

## 🤖 AI機能

### 台本生成
- 過去の成功パターン分析
- トレンドに基づいたテーマ選定
- エンゲージメント向上のための構成最適化

### パフォーマンス分析
- 動画パフォーマンスの多角的分析
- 視聴者コメントの感情分析
- 具体的な改善アクションプランの生成

## 📈 自動化機能

- **日次分析**: 動画公開1日後の自動分析
- **週次レポート**: 毎週日曜日の総合レポート
- **Discord通知**: リアルタイムの進捗通知
- **エラー監視**: 自動エラー検出・通知

## 🔧 カスタマイズ

### プロンプト設定
`config/prompts.json`でAIプロンプトをカスタマイズ可能

### 動画テンプレート
`core/video_generator.py`で動画レイアウト・効果を調整

### 分析ロジック
`handlers/analysis_ai.py`で分析ロジックを調整

## 📝 ログ・監視

- 詳細なログ記録 (`logs/`ディレクトリ)
- Discord通知による状況報告
- エラー自動検出・通知システム

## 🚨 注意事項

- YouTube API制限を考慮した使用
- 認証情報の適切な管理
- 定期的なログファイルのクリーンアップ推奨

## 📞 サポート

問題が発生した場合は、ログファイルを確認するか、Discord通知を参照してください。