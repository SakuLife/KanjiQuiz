# GitHub Secrets 設定ガイド

このドキュメントでは、KanjiQuizプロジェクトをGitHub Actionsで動作させるために必要なSecretsの設定方法を説明します。

## 📁 ファイルの場所

### 1. Google Sheets認証情報
**ファイルパス**: `D:\AutoSystem\PythonSystem\KanjiQuiz\json\credentials.json`

このファイルは、Google Cloud Platformで作成したサービスアカウントのJSONキーファイルです。

### 2. YouTube OAuth認証情報
**ファイルパス**: `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json`

このファイルは、Google Cloud Platformで作成したYouTube OAuth 2.0クライアントIDのJSONファイルです。

### 3. YouTube認証トークン
**ファイルパス**: `D:\AutoSystem\PythonSystem\KanjiQuiz\token.pickle`

このファイルは、YouTube APIの認証後に自動生成されるトークンファイルです。

---

## 🔐 GitHub Secrets設定手順

### ステップ1: GitHubリポジトリにアクセス

1. `https://github.com/SakuLife/KanjiQuiz` にアクセス
2. **Settings** > **Secrets and variables** > **Actions** に移動
3. **New repository secret** をクリック

### ステップ2: 各Secretを設定

以下の順番で設定してください。

---

## 📋 Secret一覧と設定方法

### 1. GCP_SA_JSON (Google Cloud サービスアカウント)

**Secret名**: `GCP_SA_JSON`

**ファイル**: `json/credentials.json`

**設定方法**:
1. `D:\AutoSystem\PythonSystem\KanjiQuiz\json\credentials.json` を開く
2. **ファイル全体の内容をコピー**（改行を含む）
3. GitHub SecretsのValue欄に**そのまま貼り付け**

**例**:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

**重要**: JSON全体を1つの値として貼り付けてください。

---

### 2. GEMINI_API_KEY (Gemini AI API キー)

**Secret名**: `GEMINI_API_KEY`

**取得方法**:
1. Google AI Studio (https://makersuite.google.com/app/apikey) にアクセス
2. APIキーを生成または既存のキーをコピー

**設定方法**:
- Value欄にAPIキーをそのまま貼り付け（例: `AIzaSy...`）

---

### 3. SPREADSHEET_ID (Google Sheets スプレッドシートID)

**Secret名**: `SPREADSHEET_ID`

**取得方法**:
1. Google SheetsのURLを開く
2. URLからIDを抽出:
   ```
   https://docs.google.com/spreadsheets/d/【ここがID】/edit
   ```

**設定方法**:
- Value欄にスプレッドシートIDをそのまま貼り付け

**例**: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t`

---

### 4. YT_CLIENT_ID (YouTube OAuth クライアントID)

**Secret名**: `YT_CLIENT_ID`

**ファイル**: `json/client_secret.json` の中の `client_id` フィールド

**設定方法**:
1. `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json` を開く
2. `"client_id"` の値をコピー

**例**: `262523400856-ai98t7n4f7fjbgisbpp9ctcffp0srifs.apps.googleusercontent.com`

---

### 5. YT_CLIENT_SECRET (YouTube OAuth クライアントシークレット)

**Secret名**: `YT_CLIENT_SECRET`

**ファイル**: `json/client_secret.json` の中の `client_secret` フィールド

**設定方法**:
1. `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json` を開く
2. `"client_secret"` の値をコピー

**例**: `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`

---

### 6. YT_REFRESH_TOKEN (YouTube OAuth リフレッシュトークン)

**Secret名**: `YT_REFRESH_TOKEN`

**取得方法**:
1. `token.pickle` ファイルから取得するか、OAuth認証フローで取得
2. または、YouTube API認証時に取得したリフレッシュトークンを使用

**注意**: このトークンは `token.pickle` ファイルに含まれていますが、直接抽出するのは困難です。
既に認証済みの場合は、`token.pickle` をbase64エンコードして `YOUTUBE_TOKEN_PICKLE` として設定する方法を推奨します。

---

### 7. YT_CLIENT_SECRET_JSON (YouTube OAuth クライアントシークレットJSON)

**Secret名**: `YT_CLIENT_SECRET_JSON`

**ファイル**: `json/client_secret.json`

**設定方法**:
1. `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json` を開く
2. **ファイル全体の内容をコピー**（改行を含む）
3. GitHub SecretsのValue欄に**そのまま貼り付け**

**例**:
```json
{
  "installed": {
    "client_id": "262523400856-ai98t7n4f7fjbgisbpp9ctcffp0srifs.apps.googleusercontent.com",
    "project_id": "kanjiquiz-462614",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "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",
    "redirect_uris": ["http://localhost"]
  }
}
```

**重要**: JSON全体を1つの値として貼り付けてください。

---

### 8. YOUTUBE_TOKEN_PICKLE (YouTube認証トークン - Base64エンコード)

**Secret名**: `YOUTUBE_TOKEN_PICKLE`

**ファイル**: `token.pickle`

**設定方法**:

#### Windows (PowerShell) でエンコード:

```powershell
# PowerShellを開く
cd D:\AutoSystem\PythonSystem\KanjiQuiz
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.pickle"))
```

出力された長い文字列をコピーして、GitHub SecretsのValue欄に貼り付けます。

#### Windows (コマンドプロンプト) でエンコード:

```cmd
cd D:\AutoSystem\PythonSystem\KanjiQuiz
certutil -encode token.pickle token_base64.txt
type token_base64.txt
```

出力から `-----BEGIN CERTIFICATE-----` と `-----END CERTIFICATE-----` の行を除いた内容をコピーします。

#### Pythonでエンコード:

```python
import base64

with open("D:\\AutoSystem\\PythonSystem\\KanjiQuiz\\token.pickle", "rb") as f:
    encoded = base64.b64encode(f.read()).decode('utf-8')
    print(encoded)
```

出力された文字列をコピーして、GitHub SecretsのValue欄に貼り付けます。

**重要**: 
- 改行を含まない1つの長い文字列になります
- 完全にコピーしてください（途中で切れないように）

---

### 9. DISCORD_WEBHOOK_URL (Discord通知用Webhook URL)

**Secret名**: `DISCORD_WEBHOOK_URL`

**取得方法**:
1. Discordサーバーで、**サーバー設定** > **連携サービス** > **ウェブフック** に移動
2. **新しいウェブフック** を作成
3. ウェブフックURLをコピー

**設定方法**:
- Value欄にWebhook URLをそのまま貼り付け

**例**: `https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz`

---

### 10. DISCORD_WEBHOOK_URL_ERROR (Discordエラー通知用Webhook URL)

**Secret名**: `DISCORD_WEBHOOK_URL_ERROR`

**取得方法**:
- エラー専用のWebhookを作成（通常の通知とは別に）

**設定方法**:
- Value欄にWebhook URLをそのまま貼り付け

**注意**: 通常の通知と同じWebhook URLを使用しても問題ありません。

---

## ✅ 設定確認チェックリスト

以下のSecretsがすべて設定されているか確認してください：

- [ ] `GCP_SA_JSON` - Google Sheets認証情報（JSON全体）
- [ ] `GEMINI_API_KEY` - Gemini API キー
- [ ] `SPREADSHEET_ID` - Google Sheets スプレッドシートID
- [ ] `YT_CLIENT_ID` - YouTube OAuth クライアントID
- [ ] `YT_CLIENT_SECRET` - YouTube OAuth クライアントシークレット
- [ ] `YT_REFRESH_TOKEN` - YouTube リフレッシュトークン（または `YOUTUBE_TOKEN_PICKLE` を使用）
- [ ] `YT_CLIENT_SECRET_JSON` - YouTube OAuth JSON（JSON全体）
- [ ] `YOUTUBE_TOKEN_PICKLE` - YouTube認証トークン（Base64エンコード）
- [ ] `DISCORD_WEBHOOK_URL` - Discord通知用Webhook URL
- [ ] `DISCORD_WEBHOOK_URL_ERROR` - Discordエラー通知用Webhook URL（オプション）

---

## 🔍 ファイルの場所まとめ

| Secret名 | ファイルパス | 取得方法 |
|---------|------------|---------|
| `GCP_SA_JSON` | `D:\AutoSystem\PythonSystem\KanjiQuiz\json\credentials.json` | ファイル全体をコピー |
| `YT_CLIENT_ID` | `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json` | `client_id` フィールドをコピー |
| `YT_CLIENT_SECRET` | `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json` | `client_secret` フィールドをコピー |
| `YT_CLIENT_SECRET_JSON` | `D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json` | ファイル全体をコピー |
| `YOUTUBE_TOKEN_PICKLE` | `D:\AutoSystem\PythonSystem\KanjiQuiz\token.pickle` | Base64エンコードしてコピー |

---

## 🚨 よくある間違い

### ❌ 間違い1: JSONファイルの一部だけをコピー
- ✅ 正しい: ファイル全体をコピー（`{` から `}` まで）

### ❌ 間違い2: token.pickleをそのまま貼り付け
- ✅ 正しい: Base64エンコードしてから貼り付け

### ❌ 間違い3: 改行を削除してしまう
- ✅ 正しい: JSONファイルは改行を含めてそのまま貼り付け

### ❌ 間違い4: クォートを追加してしまう
- ✅ 正しい: GitHub SecretsのValue欄には、値そのものを貼り付ける（クォート不要）

---

## 📝 設定後の確認

1. **GitHub Actions** タブに移動
2. **KanjiQuiz Automation** ワークフローを選択
3. **Run workflow** をクリック
4. `force_run` を `true` に設定
5. **Run workflow** ボタンをクリック

実行が成功すれば、Secretsの設定は正しく行われています。

---

**作成日**: 2025-01-XX
**対象**: KanjiQuiz GitHub Secrets設定

