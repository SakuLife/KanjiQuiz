# GitHub接続トラブルシューティング

## エラー: `Could not resolve host: github.com`

このエラーが発生する場合の対処法：

### 1. ネットワーク接続の確認

```bash
# DNS解決の確認
nslookup github.com

# 接続テスト
ping github.com -n 4
```

### 2. Git設定の確認と修正

```bash
# HTTPバージョンを設定（IPv6問題の回避）
git config --global http.version HTTP/1.1

# SSL検証を有効化
git config --global http.sslVerify true

# プロキシ設定の確認（設定されている場合）
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 3. リポジトリの存在確認

**重要**: GitHub上にリポジトリがまだ作成されていない場合、このエラーが発生します。

1. GitHubにログイン
2. `https://github.com/SakuLife/KanjiQuiz` にアクセス
3. リポジトリが存在するか確認

### 4. SSH接続への切り替え（推奨）

HTTPS接続に問題がある場合、SSH接続に切り替えます：

#### SSH鍵の生成（まだ持っていない場合）

```bash
# SSH鍵を生成
ssh-keygen -t ed25519 -C "your_email@example.com"

# 公開鍵を表示
cat ~/.ssh/id_ed25519.pub
```

#### GitHubにSSH鍵を登録

1. 生成した公開鍵をコピー
2. GitHub > Settings > SSH and GPG keys > New SSH key
3. 公開鍵を貼り付けて保存

#### リモートURLをSSHに変更

```bash
cd D:\AutoSystem\PythonSystem\KanjiQuiz
git remote set-url origin git@github.com:SakuLife/KanjiQuiz.git
git remote -v  # 確認
```

#### SSH接続テスト

```bash
ssh -T git@github.com
```

### 5. 一時的な解決策

#### 方法A: リトライ

一時的なネットワーク問題の可能性があるため、数分待ってから再試行：

```bash
git push -u origin master
```

#### 方法B: 別のDNSサーバーを使用

```bash
# Google Public DNSを使用
ipconfig /flushdns
```

#### 方法C: VPN/プロキシの確認

企業ネットワークやVPNを使用している場合、プロキシ設定が必要な場合があります。

### 6. GitHub CLIを使用（代替方法）

GitHub CLIがインストールされている場合：

```bash
# GitHub CLIで認証
gh auth login

# リポジトリを作成してプッシュ
gh repo create SakuLife/KanjiQuiz --private --source=. --remote=origin --push
```

### 7. 手動でのリポジトリ作成とプッシュ

1. **GitHubでリポジトリを作成**（Webブラウザで）
   - https://github.com/new
   - リポジトリ名: `KanjiQuiz`
   - 組織: `SakuLife`
   - **重要**: README、.gitignore、ライセンスは追加しない

2. **リポジトリ作成後、GitHubが表示する手順に従う**:
   ```bash
   git remote add origin https://github.com/SakuLife/KanjiQuiz.git
   git branch -M main
   git push -u origin main
   ```

   または、既存のリモートがある場合：
   ```bash
   git push -u origin master
   ```

## よくある問題と解決法

### 問題1: 認証エラー

```
remote: Support for password authentication was removed on August 13, 2021.
```

**解決法**: Personal Access Token (PAT) を使用

1. GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)
2. "Generate new token" をクリック
3. スコープ: `repo` を選択
4. トークンを生成してコピー
5. プッシュ時にパスワードの代わりにトークンを使用

### 問題2: リポジトリが見つからない

```
remote: Repository not found.
```

**解決法**:
- リポジトリが存在するか確認
- アクセス権限があるか確認
- リポジトリ名が正確か確認（大文字小文字を含む）

### 問題3: 接続タイムアウト

```
fatal: unable to access 'https://github.com/...': Failed to connect to github.com port 443
```

**解決法**:
- ファイアウォール設定を確認
- プロキシ設定を確認
- VPN接続を確認

---

**作成日**: 2025-01-XX
**対象**: KanjiQuiz GitHub接続トラブルシューティング
