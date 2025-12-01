# KanjiQuiz GitHub リポジトリセットアップガイド

## 現在の状況

- ローカルリポジトリは既に `SakuLife/KanjiQuiz` をリモートとして設定済み
- GitHub Actionsのワークフローは設定済み
- リポジトリがGitHub上に存在しない可能性があります

## GitHubリポジトリの作成手順

### 1. GitHubでリポジトリを作成

1. **GitHubにログイン**して、`SakuLife` 組織（またはアカウント）にアクセス
2. **新しいリポジトリを作成**:
   - リポジトリ名: `KanjiQuiz`
   - 説明: `漢字クイズ動画自動生成システム - YouTube向けの漢字クイズ動画を自動生成し、アップロード、分析まで行う統合システム`
   - 公開設定: プライベート（推奨）またはパブリック
   - **重要**: README、.gitignore、ライセンスは追加しない（既にローカルに存在するため）

### 2. リモートリポジトリの設定確認

リポジトリ作成後、以下のコマンドでリモートURLを確認・設定：

```bash
# 現在のリモート設定を確認
git remote -v

# もし異なる場合は、正しいURLに設定
git remote set-url origin https://github.com/SakuLife/KanjiQuiz.git

# またはSSHを使用する場合
git remote set-url origin git@github.com:SakuLife/KanjiQuiz.git
```

### 3. 初回プッシュ

```bash
# 現在のブランチを確認
git branch

# masterブランチをmainに変更する場合（GitHubのデフォルト）
git branch -M main

# 初回プッシュ
git push -u origin main
# または masterブランチのままの場合
git push -u origin master
```

### 4. GitHub Actionsの有効化

1. GitHubリポジトリの **Settings** > **Actions** > **General** に移動
2. **Actions permissions** で以下を確認:
   - ✅ "Allow all actions and reusable workflows" を選択
   - ✅ "Allow actions to create and approve pull requests" を有効化（必要に応じて）

### 5. GitHub Secretsの設定

リポジトリの **Settings** > **Secrets and variables** > **Actions** で以下を設定：

#### 必須Secrets

```
GCP_SA_JSON              # Google Cloud サービスアカウントJSON（完全な内容）
GEMINI_API_KEY           # Gemini API キー
SPREADSHEET_ID           # Google Sheets スプレッドシートID
YT_CLIENT_ID             # YouTube OAuth クライアントID
YT_CLIENT_SECRET         # YouTube OAuth クライアントシークレット
YT_REFRESH_TOKEN         # YouTube リフレッシュトークン
YT_CLIENT_SECRET_JSON    # client_secret.jsonファイルの完全な内容
YOUTUBE_TOKEN_PICKLE     # token.pickleファイルをbase64エンコードしたもの
DISCORD_WEBHOOK_URL      # Discord通知用Webhook URL
DISCORD_WEBHOOK_URL_ERROR # Discordエラー通知用Webhook URL
```

#### token.pickleのbase64エンコード方法

```bash
# Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pickle"))

# Linux/Mac
base64 -i token.pickle
```

### 6. GitHub Actionsの動作確認

1. **Actions** タブに移動
2. ワークフローが表示されているか確認
3. **手動実行**:
   - "KanjiQuiz Automation" ワークフローを選択
   - "Run workflow" ボタンをクリック
   - `force_run` を `true` に設定して実行

### 7. スケジュール実行の確認

- ワークフローは毎日 **08:00 UTC (17:00 JST)** に自動実行されます
- 実行履歴は **Actions** タブで確認できます
- 実行結果はDiscord通知でも確認できます

## トラブルシューティング

### リポジトリが見つからないエラー

```
remote: Repository not found.
fatal: repository 'https://github.com/SakuLife/KanjiQuiz.git/' not found
```

**解決方法**:
1. GitHubでリポジトリが作成されているか確認
2. リポジトリ名が正確か確認（大文字小文字を含む）
3. アクセス権限があるか確認
4. 認証情報を確認（Personal Access Tokenが必要な場合）

### GitHub Actionsが実行されない

1. **Actionsタブ**でワークフローが有効になっているか確認
2. **Settings** > **Actions** > **General** でActionsが有効になっているか確認
3. Secretsが正しく設定されているか確認
4. ワークフローファイルの構文エラーがないか確認

### 認証エラー

1. すべてのSecretsが正しく設定されているか確認
2. JSONファイルの内容が完全にコピーされているか確認（改行を含む）
3. base64エンコードが正しく行われているか確認

## 次のステップ

1. ✅ GitHubリポジトリを作成
2. ✅ コードをプッシュ
3. ✅ GitHub Actionsを有効化
4. ✅ Secretsを設定
5. ✅ 手動実行でテスト
6. ✅ スケジュール実行を確認

---

**作成日**: 2025-01-XX
**対象**: KanjiQuiz GitHub リポジトリセットアップ

