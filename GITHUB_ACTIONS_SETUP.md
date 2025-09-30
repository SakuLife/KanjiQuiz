# KanjiQuiz GitHub Actions セットアップガイド

このドキュメントは、KanjiQuizシステムをGitHub Actionsで自動実行するための設定手順を説明します。

## システム概要

- **自動実行**: 毎日 17:00 JST に実行（20:00予約投稿のため）
- **手動実行**: GitHub ActionsのWorkflow Dispatch
- **実行環境**: Ubuntu Latest (Python 3.11)
- **処理内容**: 漢字クイズ動画の自動生成・YouTube投稿・分析

## 必要な準備

### 1. Google Cloud Platform 設定

1. **Google Cloud Console** でプロジェクトを作成
2. 以下のAPIを有効化：
   - Google Sheets API
   - Google Drive API
   - YouTube Data API v3
   - Gemini AI API

3. **サービスアカウント** を作成:
   - JSON キーファイルをダウンロード
   - Google Sheets に編集権限を付与

4. **YouTube OAuth** を設定:
   - OAuth 2.0 クライアント ID を作成
   - `client_secret.json` をダウンロード
   - リフレッシュトークンを取得

### 2. GitHub Secrets 設定

GitHub リポジトリの Settings > Secrets and variables > Actions で以下を設定：

#### Google Cloud関連
```
GCP_SA_JSON             # サービスアカウントJSONの完全な内容
GEMINI_API_KEY          # Gemini API キー
```

#### Google Sheets
```
SPREADSHEET_ID          # Google Sheets のスプレッドシートID
```

#### YouTube OAuth
```
YT_CLIENT_ID            # YouTube OAuth クライアントID
YT_CLIENT_SECRET        # YouTube OAuth クライアントシークレット
YT_REFRESH_TOKEN        # YouTube リフレッシュトークン
YT_CLIENT_SECRET_JSON   # client_secret.jsonファイルの完全な内容
```

#### Discord通知
```
DISCORD_WEBHOOK_URL       # 通常通知用のWebhook URL
DISCORD_WEBHOOK_URL_ERROR # エラー通知用のWebhook URL
```

## ファイル構成

```
KanjiQuiz/
├── .github/workflows/
│   └── kanji-quiz-automation.yml    # メイン自動化ワークフロー
├── core/                            # コアアプリケーション
├── handlers/                        # 外部API連携
├── requirements.txt                 # Python依存関係
├── .env.clean                       # 環境変数テンプレート
└── run_quiz_bot.py                  # GitHub Actions対応ランナー
```

## ワークフロー詳細

### 実行スケジュール
- **自動実行**: 毎日 08:00 UTC (17:00 JST)
- **手動実行**: GitHub ActionsのWorkflow Dispatch

### 実行ステップ

#### Job 1: video-generation
1. 環境セットアップ (Python 3.11, システム依存関係)
2. 認証情報の配置
3. 動画生成・アップロードの実行
4. 成果物のアップロード

#### Job 2: metrics-collection
1. YouTube統計の収集
2. パフォーマンス分析
3. レポート生成

### システム依存関係
- **FFmpeg**: 音声・動画処理
- **Noto CJK フォント**: 日本語テキスト描画
- **Xvfb**: 仮想ディスプレイ (MoviePy用)

## 実行時の特徴

### GitHub Actions 専用機能
- Linux用フォントパスの自動設定
- VOICEVOX無効化 (音声生成スキップ)
- 仮想ディスプレイでの動画処理
- Discord通知による実行状況報告

### エラーハンドリング
- 部分的失敗時も処理継続
- 詳細ログのアーティファクト保存
- エラー専用Discord通知

## 監視・運用

### 実行状況確認
1. **GitHub Actions**: 実行履歴とログ
2. **Discord通知**: リアルタイム状況報告
3. **Google Sheets**: データ更新状況
4. **YouTube Studio**: 動画投稿状況

### トラブルシューティング

#### よくある問題
1. **認証エラー**: Secrets設定を確認
2. **API制限**: YouTube/Gemini APIクォータを確認
3. **フォントエラー**: システムフォントパスを確認

#### 対処法
1. **手動再実行**: Workflow Dispatchを使用
2. **ログ確認**: Artifactsからログダウンロード
3. **部分実行**: 個別スクリプトの直接実行

## セキュリティ考慮事項

- 全認証情報をGitHub Secretsで管理
- 本番環境変数は環境から直接取得
- API制限・レート制限への対応
- 最小権限でのサービスアカウント設定

## カスタマイズ

### スケジュール変更
`.github/workflows/kanji-quiz-automation.yml` の cron 設定を変更

### 通知設定
`handlers/discord_handler.py` で通知内容をカスタマイズ

### 処理内容変更
`core/app.py` でメインロジックを調整

---

**作成日**: 2025-09-29
**対象**: KanjiQuiz GitHub Actions 自動化システム