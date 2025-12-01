# KanjiQuiz GitHub Actions クイックスタート

## ✅ セットアップ完了後の確認

### 1. GitHub Actionsの動作確認

1. **GitHubリポジトリにアクセス**:
   - `https://github.com/SakuLife/KanjiQuiz` にアクセス

2. **Actionsタブを確認**:
   - **Actions** タブに移動
   - **KanjiQuiz Automation** ワークフローが表示されているか確認

3. **手動実行でテスト**:
   - **KanjiQuiz Automation** をクリック
   - **Run workflow** ボタンをクリック
   - `force_run` を `true` に設定
   - **Run workflow** ボタンをクリック

4. **実行結果を確認**:
   - 実行が開始されたら、ログを確認
   - 以下のステップが成功しているか確認:
     - ✅ Setup Google Service Account
     - ✅ Setup YouTube OAuth
     - ✅ Setup YouTube Token Pickle
     - ✅ Run KanjiQuiz automation

### 2. 自動実行スケジュール

- **実行時刻**: 毎日 **08:00 UTC (17:00 JST)**
- **実行内容**: 漢字クイズ動画の自動生成・YouTube投稿・分析

### 3. 実行履歴の確認

- **Actions** タブで実行履歴を確認できます
- 各実行のログを確認して、エラーがないかチェック
- 成功した場合は、生成された動画がArtifactsにアップロードされます

### 4. Discord通知の確認

- 実行開始時にDiscord通知が送信されます
- 実行完了時にも通知が送信されます
- エラーが発生した場合も通知されます

---

## 🚨 エラーが発生した場合

### よくあるエラー

1. **Secretsの設定エラー**:
   - `TROUBLESHOOTING_SECRETS.md` を参照

2. **認証エラー**:
   - Google Cloud Platformの設定を確認
   - YouTube APIの認証情報を確認

3. **API制限エラー**:
   - YouTube APIのクォータを確認
   - Gemini APIのクォータを確認

### ログの確認方法

1. **Actions** タブで実行を選択
2. 失敗したジョブをクリック
3. エラーが発生したステップを確認
4. ログをダウンロードして詳細を確認

---

## 📚 参考ドキュメント

- **`GITHUB_SECRETS_SETUP.md`** - Secrets設定ガイド
- **`TROUBLESHOOTING_SECRETS.md`** - トラブルシューティング
- **`GITHUB_SETUP.md`** - リポジトリセットアップガイド
- **`GITHUB_ACTIONS_SETUP.md`** - GitHub Actions詳細ガイド

---

## 🎉 次のステップ

1. ✅ GitHubリポジトリの作成
2. ✅ GitHub Secretsの設定
3. ✅ GitHub Actionsの動作確認
4. ⏭️ 自動実行の監視
5. ⏭️ 生成された動画の確認

---

**作成日**: 2025-01-XX
**対象**: KanjiQuiz GitHub Actions クイックスタート

