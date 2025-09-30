# 動画分析システム仕様書

## 概要
この仕様書は、YouTubeチャンネル向けの包括的な動画分析システムを他のシステムでも活用できるように汎用化したものです。

## アーキテクチャ

### 1. 分析エンジン（Performance Analyzer）

#### 1.1 相対評価分析
**目的**: チャンネル内での動画の相対的なパフォーマンスを評価

**機能**:
- パフォーマンス指標の統計計算（平均、中央値、標準偏差）
- 動画のランキング化（再生数、エンゲージメント率、高評価率）
- テーマ別パフォーマンス分析
- パフォーマンス分布分析（四分位数）
- 改善提案の自動生成

**出力データ構造**:
```json
{
    "analyzed_videos_count": "int",
    "analysis_timestamp": "ISO datetime",
    "performance_metrics": {
        "views": {"avg": "float", "median": "float", "max": "int", "min": "int", "std": "float"},
        "likes": {"avg": "float", "median": "float", "max": "int", "min": "int"},
        "comments": {"avg": "float", "median": "float", "max": "int", "min": "int"},
        "engagement_rate": {"avg": "float", "median": "float", "max": "float", "min": "float"},
        "like_rate": {"avg": "float", "median": "float", "max": "float", "min": "float"}
    },
    "rankings": {
        "views_top10": "List[Dict]",
        "engagement_top10": "List[Dict]",
        "like_rate_top10": "List[Dict]",
        "comments_top10": "List[Dict]",
        "views_bottom5": "List[Dict]",
        "engagement_bottom5": "List[Dict]"
    },
    "theme_analysis": {
        "theme_performance": "Dict[str, Dict]",
        "total_themes": "int",
        "most_popular_theme": "str",
        "theme_diversity_score": "float"
    },
    "improvement_suggestions": "List[str]"
}
```

#### 1.2 トレンド分析
**目的**: 再生数変化に基づく動画の成長トレンドを分析

**機能**:
- 再生数変化の計算と成長率算出
- テーマ別成長分析
- コンテンツ特性と成長率の相関分析

### 2. AIアナリスト（Analysis AI）

#### 2.1 個別動画分析
**目的**: AIを使用した深いコンテンツ分析と改善提案

**入力データ**:
- 動画タイトル
- コンテンツスクリプト/台本
- 統計データ（再生数、高評価数、コメント数）
- 視聴者コメント
- 過去の計画・分析結果

**分析観点**:
- コンテンツの質と適切性
- エンゲージメント要因の特定
- 構成とテンポの評価
- 視聴者反応の解釈

**出力**:
```json
{
    "analysis": "分析結果テキスト",
    "plan": "改善計画テキスト", 
    "tokens": "使用トークン数"
}
```

#### 2.2 週次インサイト分析
**目的**: チャンネル全体の傾向分析と戦略提案

**機能**:
- 複数動画の横断分析
- 成功パターンの抽出
- 戦略的改善提案の生成
- 相対評価結果との統合分析

### 3. レポーティングシステム

#### 3.1 日次レポート
**内容**:
- 総再生数、高評価数、コメント数
- 成長上位5動画
- 統一スコア情報

#### 3.2 週次レポート  
**内容**:
- 週次統計サマリー
- 新規公開動画の分析
- 成長動画トップ3
- 総再生数上位5動画
- AIインサイト
- 相対評価分析結果

### 4. 統一スコアリングシステム

#### 4.1 スコア算出方法
多次元評価による統一スコア:
- 再生数スコア
- エンゲージメントスコア  
- 成長率スコア
- 相対評価スコア

#### 4.2 チャンネル分析
- 平均スコアの計算
- スコア分布の分析
- パフォーマンス傾向の把握

## データフロー

```
1. データ収集 → 2. 基礎分析 → 3. AI分析 → 4. レポート生成 → 5. 改善提案
    ↓              ↓             ↓          ↓              ↓
外部API統計    相対評価分析    個別分析    日次/週次      次回計画
YouTube API   トレンド分析    週次分析    レポート       戦略提案
コメント取得  スコア算出      インサイト   通知送信       改善実行
```

## 必要な外部サービス

### データソース
- **YouTube Data API v3**: 動画統計、コメント取得
- **Google Sheets API**: データ永続化
- **AI サービス**: コンテンツ分析（Gemini Pro等）

### 通知システム  
- **Discord Webhook**: レポート通知
- **メール通知**: 重要なアラート

## 設定項目

### 環境変数
```env
# データソース
YOUTUBE_API_KEY="your_youtube_api_key"
SPREADSHEET_ID="your_spreadsheet_id" 
AI_API_KEY="your_ai_api_key"

# 通知
DISCORD_WEBHOOK_URL="your_discord_webhook"
DISCORD_WEBHOOK_URL_ERROR="your_error_webhook"

# 分析設定
CHANNEL_SUBSCRIBERS="チャンネル登録者数"
ANALYSIS_FREQUENCY="分析実行頻度"
```

### 分析パラメータ
```json
{
    "performance_thresholds": {
        "high_performance_percentile": 75,
        "low_performance_percentile": 25
    },
    "trend_analysis": {
        "minimum_growth_threshold": 10,
        "trending_days_lookback": 7
    },
    "ai_analysis": {
        "max_comments_to_analyze": 10,
        "analysis_prompt_template": "custom_prompt.txt"
    }
}
```

## 実装ガイド

### 1. データモデル
動画データの標準化された構造を定義:
```python
video_data = {
    "video_id": "str",
    "title": "str", 
    "upload_date": "YYYY/MM/DD",
    "script": "json_str",  # コンテンツ固有
    "previous_views": "int",
    "previous_likes": "int", 
    "previous_comments": "int",
    "latest_stats": {"views": "int", "likes": "int", "comments": "int"},
    "previous_analysis": "str",
    "previous_plan": "str",
    "row_num": "int"  # データソース位置
}
```

### 2. 分析クラスの実装
```python
class PerformanceAnalyzer:
    def analyze_relative_performance(self, videos_data: List[Dict]) -> Dict
    def _calculate_performance_metrics(self, videos_data: List[Dict]) -> Dict  
    def _calculate_rankings(self, videos_data: List[Dict]) -> Dict
    def _analyze_by_theme(self, videos_data: List[Dict]) -> Dict
    def get_relative_performance_score(self, video_data: Dict, all_videos: List[Dict]) -> Dict
```

### 3. AIアナリストの実装
```python
def generate_insight_and_plan(title, script, previous_plan, stats_data, comments_data=None):
def generate_weekly_insights(videos_data, relative_analysis=None):
```

### 4. レポート生成
```python
def create_daily_summary_report(videos_with_stats):
def create_weekly_summary_report(videos_with_stats, sheet, col_map):
```

## カスタマイズポイント

### 1. コンテンツ固有の分析
- テーマ抽出ロジック
- コンテンツ品質評価指標
- 成功要因の定義

### 2. AI分析プロンプト
- 業界特化型のプロンプト設計
- 分析観点のカスタマイズ
- 改善提案の業界適応

### 3. 通知・レポート形式
- 通知チャンネルの選択
- レポートフォーマットの調整
- ダッシュボード統合

## 拡張機能

### 1. 競合分析
- 他チャンネルとの比較分析
- 業界ベンチマークとの照合
- トレンド予測機能

### 2. 自動化機能  
- スケジュール実行
- 閾値ベースのアラート
- 自動改善提案の実行

### 3. 高度な分析
- 機械学習による予測モデル
- センチメント分析
- A/Bテスト結果の統合

## 導入手順

1. **環境準備**: 必要なAPI認証情報の取得
2. **データソース設定**: スプレッドシート構造の作成
3. **分析エンジン配置**: コア分析モジュールのデプロイ
4. **AI設定**: 分析プロンプトのカスタマイズ
5. **通知設定**: レポート送信先の設定
6. **自動化設定**: スケジュール実行の配置
7. **テスト実行**: サンプルデータでの動作確認

## 運用・保守

### ログ管理
- 分析処理のログ出力
- エラー監視とアラート
- パフォーマンス監視

### データ品質管理
- データ整合性チェック
- 異常値検出とクリーニング
- バックアップとリカバリ

### 継続改善
- 分析精度の定期評価
- プロンプト効果測定
- 新機能の段階的導入