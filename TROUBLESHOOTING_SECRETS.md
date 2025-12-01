# GitHub Secrets トラブルシューティング

## よくあるエラーと解決法

### エラー1: `base64: invalid input`

**エラーメッセージ**:
```
📝 YouTube認証トークンをデコード中...
base64: invalid input
Error: Process completed with exit code 1.
```

**原因**:
- `YOUTUBE_TOKEN_PICKLE` の値に改行や空白が含まれている
- Base64文字列が不完全（途中で切れている）
- コピー&ペースト時に余分な文字が入った

**解決法**:

1. **encode_token.pyを再実行**:
   ```bash
   cd D:\AutoSystem\PythonSystem\KanjiQuiz
   python encode_token.py
   ```

2. **出力された文字列を完全にコピー**:
   - 文字列の最初から最後まで、すべてを選択
   - 改行が入らないように注意
   - 余分な空白や改行を入れない

3. **GitHub Secretsに貼り付け**:
   - Value欄に、コピーした文字列をそのまま貼り付け
   - 前後に空白や改行を入れない

4. **確認**:
   - 貼り付けた後、文字列の前後に余分な文字がないか確認
   - 文字列は1行で、改行がないことを確認

---

### エラー2: `echo '***' > json/client_secret.json`

**エラーメッセージ**:
```
Run echo '***' > json/client_secret.json
```

**原因**:
- `YT_CLIENT_SECRET_JSON` が正しく設定されていない
- Secretsの値が空または `***` というプレースホルダーのまま

**解決法**:

1. **client_secret.jsonファイルを開く**:
   ```
   D:\AutoSystem\PythonSystem\KanjiQuiz\json\client_secret.json
   ```

2. **ファイル全体をコピー**:
   - エディタでファイルを開く
   - すべて選択（Ctrl+A）
   - コピー（Ctrl+C）

3. **GitHub Secretsに貼り付け**:
   - GitHub > Settings > Secrets and variables > Actions
   - `YT_CLIENT_SECRET_JSON` を編集
   - Value欄に、コピーしたJSONをそのまま貼り付け
   - **ダブルクォート（`"`）を含めて、そのまま貼り付ける**

4. **確認**:
   - JSONの形式が正しいか確認（`{` で始まり `}` で終わる）
   - ダブルクォートが正しく含まれているか確認

---

### エラー3: `credentials.jsonが無効なJSON形式です`

**エラーメッセージ**:
```
❌ credentials.jsonが無効なJSON形式です
```

**原因**:
- `GCP_SA_JSON` の値が不完全
- JSONの一部だけがコピーされた
- ダブルクォートが削除された

**解決法**:

1. **credentials.jsonファイルを開く**:
   ```
   D:\AutoSystem\PythonSystem\KanjiQuiz\json\credentials.json
   ```

2. **ファイル全体をコピー**:
   - エディタでファイルを開く
   - すべて選択（Ctrl+A）
   - コピー（Ctrl+C）

3. **GitHub Secretsに貼り付け**:
   - `GCP_SA_JSON` を編集
   - Value欄に、コピーしたJSONをそのまま貼り付け
   - **JSON全体を貼り付ける**（最初の `{` から最後の `}` まで）

4. **JSON形式の確認**:
   - 貼り付けた後、JSONが正しい形式か確認
   - オンラインJSONバリデーター（https://jsonlint.com/）で確認することを推奨

---

### エラー4: Secretsが設定されていない

**エラーメッセージ**:
```
❌ YT_CLIENT_SECRET_JSON が設定されていません
```

**原因**:
- Secretsがまだ設定されていない
- Secret名が間違っている

**解決法**:

1. **必要なSecretsをすべて設定**:
   - `GITHUB_SECRETS_SETUP.md` を参照
   - チェックリストに従って、すべてのSecretsを設定

2. **Secret名の確認**:
   - Secret名は大文字小文字を区別します
   - 正確に `YT_CLIENT_SECRET_JSON` と入力してください（アンダースコアを含む）

3. **設定確認**:
   - Settings > Secrets and variables > Actions で、すべてのSecretsが表示されているか確認

---

## 設定のベストプラクティス

### ✅ 正しい設定方法

1. **ファイルをエディタで開く**
2. **すべて選択（Ctrl+A）**
3. **コピー（Ctrl+C）**
4. **GitHub SecretsのValue欄に貼り付け（Ctrl+V）**
5. **保存前に内容を確認**

### ❌ 避けるべきこと

1. **手動で入力しない** - タイプミスの原因になります
2. **一部だけをコピーしない** - JSON全体をコピーしてください
3. **ダブルクォートを削除しない** - JSONの一部です
4. **改行を削除しない** - JSONファイルの改行は保持してください（ただし、Base64文字列には改行を入れない）
5. **余分な文字を追加しない** - コピーした内容をそのまま貼り付けてください

---

## 設定後の確認方法

### 1. GitHub Actionsで手動実行

1. **Actions** タブに移動
2. **KanjiQuiz Automation** ワークフローを選択
3. **Run workflow** をクリック
4. `force_run` を `true` に設定
5. **Run workflow** ボタンをクリック

### 2. ログを確認

実行後、以下のステップが成功しているか確認：

- ✅ Setup Google Service Account
- ✅ Setup YouTube OAuth
- ✅ Setup YouTube Token Pickle

これらのステップでエラーが出ない場合、Secretsの設定は正しく行われています。

---

## よくある質問

### Q: JSONファイルをコピーする際、改行は必要ですか？

**A**: 
- **credentials.json と client_secret.json**: 改行を含めてそのままコピーしてください
- **YOUTUBE_TOKEN_PICKLE (Base64文字列)**: 改行を含めないでください（1行の長い文字列）

### Q: ダブルクォート（`"`）は削除しますか？

**A**: いいえ、削除しないでください。JSONの一部なので、そのまま含めてください。

### Q: Secretsの値が長すぎて貼り付けられない

**A**: 
- GitHub Secretsには長さ制限がありますが、通常のJSONファイルやBase64文字列は問題ありません
- もし問題がある場合は、値が正しくコピーされているか確認してください

### Q: エンコード後のBase64文字列に改行が含まれている

**A**: 
- `encode_token.py` の出力は改行を含まない1行の文字列です
- もし改行が含まれている場合は、手動で削除してください
- または、出力をファイルに保存してからコピーする方法もあります：
  ```bash
  python encode_token.py > token_base64.txt
  ```
  その後、`token_base64.txt` の内容をコピーしてください

---

**作成日**: 2025-01-XX
**対象**: KanjiQuiz GitHub Secrets トラブルシューティング

