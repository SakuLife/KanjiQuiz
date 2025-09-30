# analytics_planner.py
"""
チャンネル分析と戦略計画を立案するモジュール
相対評価を基に改善計画を提案する
"""
import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from core.performance_analyzer import PerformanceAnalyzer

class AnalyticsPlanner:
    """チャンネル分析と戦略計画立案クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = PerformanceAnalyzer()
        
    def create_comprehensive_analysis_report(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """
        包括的な分析レポートを作成
        
        Args:
            videos_data: 動画データのリスト
            
        Returns:
            Dict: 包括的分析レポート
        """
        self.logger.info("包括的分析レポートを作成中...")
        
        # 基本相対評価分析
        relative_analysis = self.analyzer.analyze_relative_performance(videos_data)
        
        # 追加分析
        trend_analysis = self._analyze_performance_trends(videos_data)
        competitive_analysis = self._analyze_competitive_positioning(videos_data)
        content_strategy_analysis = self._analyze_content_strategy(videos_data, relative_analysis)
        
        # 改善計画の生成
        improvement_plans = self._generate_improvement_plans(
            relative_analysis, trend_analysis, competitive_analysis, content_strategy_analysis
        )
        
        comprehensive_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "channel_summary": self._create_channel_summary(videos_data),
            "relative_performance": relative_analysis,
            "trend_analysis": trend_analysis,
            "competitive_positioning": competitive_analysis,
            "content_strategy": content_strategy_analysis,
            "improvement_plans": improvement_plans,
            "next_video_recommendations": self._generate_next_video_recommendations(
                relative_analysis, content_strategy_analysis
            )
        }
        
        self.logger.info("包括的分析レポート作成完了")
        return comprehensive_report
        
    def _create_channel_summary(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """チャンネル全体のサマリーを作成"""
        if not videos_data:
            return {}
            
        total_videos = len(videos_data)
        total_views = sum(v['previous_views'] for v in videos_data)
        total_likes = sum(v['previous_likes'] for v in videos_data)
        total_comments = sum(v['previous_comments'] for v in videos_data)
        
        avg_views = total_views / total_videos if total_videos > 0 else 0
        avg_engagement_rate = (total_likes + total_comments) / total_views * 100 if total_views > 0 else 0
        
        # 最新動画と最古動画の日付
        dates = [datetime.strptime(v['upload_date'], "%Y/%m/%d") for v in videos_data if v.get('upload_date')]
        latest_upload = max(dates) if dates else None
        oldest_upload = min(dates) if dates else None
        
        return {
            "total_videos": total_videos,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "average_views_per_video": round(avg_views, 2),
            "overall_engagement_rate": round(avg_engagement_rate, 2),
            "channel_age_days": (latest_upload - oldest_upload).days if latest_upload and oldest_upload else 0,
            "upload_frequency_per_week": round(total_videos / ((latest_upload - oldest_upload).days / 7), 2) if latest_upload and oldest_upload and (latest_upload - oldest_upload).days > 0 else 0
        }
        
    def _analyze_performance_trends(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """パフォーマンストレンド分析"""
        if len(videos_data) < 3:
            return {"error": "トレンド分析に必要な動画数が不足"}
            
        # 日付順にソート
        sorted_videos = sorted(videos_data, key=lambda x: datetime.strptime(x['upload_date'], "%Y/%m/%d"))
        
        # 最近の動画 vs 古い動画の比較
        recent_count = max(3, len(sorted_videos) // 4)
        recent_videos = sorted_videos[-recent_count:]
        older_videos = sorted_videos[:-recent_count] if len(sorted_videos) > recent_count else []
        
        if not older_videos:
            return {"error": "比較用の古い動画データが不足"}
            
        # パフォーマンス比較
        recent_avg_views = sum(v['previous_views'] for v in recent_videos) / len(recent_videos)
        older_avg_views = sum(v['previous_views'] for v in older_videos) / len(older_videos)
        
        recent_avg_engagement = sum((v['previous_likes'] + v['previous_comments']) / v['previous_views'] * 100 if v['previous_views'] > 0 else 0 for v in recent_videos) / len(recent_videos)
        older_avg_engagement = sum((v['previous_likes'] + v['previous_comments']) / v['previous_views'] * 100 if v['previous_views'] > 0 else 0 for v in older_videos) / len(older_videos)
        
        views_trend = (recent_avg_views - older_avg_views) / older_avg_views * 100 if older_avg_views > 0 else 0
        engagement_trend = recent_avg_engagement - older_avg_engagement
        
        return {
            "recent_videos_count": len(recent_videos),
            "older_videos_count": len(older_videos),
            "views_trend_percentage": round(views_trend, 2),
            "engagement_trend_percentage": round(engagement_trend, 2),
            "recent_avg_views": round(recent_avg_views, 2),
            "older_avg_views": round(older_avg_views, 2),
            "recent_avg_engagement": round(recent_avg_engagement, 2),
            "older_avg_engagement": round(older_avg_engagement, 2),
            "trend_status": self._determine_trend_status(views_trend, engagement_trend)
        }
        
    def _determine_trend_status(self, views_trend: float, engagement_trend: float) -> str:
        """トレンドステータスを判定"""
        if views_trend > 10 and engagement_trend > 0.5:
            return "急成長"
        elif views_trend > 0 and engagement_trend > 0:
            return "成長"
        elif views_trend > -10 and engagement_trend > -0.5:
            return "安定"
        elif views_trend > -25:
            return "低下気味"
        else:
            return "要改善"
            
    def _analyze_competitive_positioning(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """競合ポジション分析（チャンネル内での相対的位置）"""
        if not videos_data:
            return {}
            
        # パフォーマンスレベル別の分類
        views_list = [v['previous_views'] for v in videos_data if v['previous_views'] > 0]
        if not views_list:
            return {"error": "再生数データなし"}
            
        views_list.sort()
        n = len(views_list)
        
        # パフォーマンス閾値を設定
        elite_threshold = views_list[int(n * 0.9)] if n >= 10 else views_list[-1]
        good_threshold = views_list[int(n * 0.7)] if n >= 5 else views_list[int(n * 0.8)] if n >= 4 else views_list[-2] if n >= 2 else 0
        average_threshold = views_list[int(n * 0.5)] if n >= 2 else 0
        
        performance_categories = {
            "elite_performers": [],      # 上位10%
            "good_performers": [],       # 上位30%
            "average_performers": [],    # 中位
            "underperformers": []        # 下位
        }
        
        for video in videos_data:
            views = video['previous_views']
            if views >= elite_threshold:
                performance_categories["elite_performers"].append(video)
            elif views >= good_threshold:
                performance_categories["good_performers"].append(video)
            elif views >= average_threshold:
                performance_categories["average_performers"].append(video)
            else:
                performance_categories["underperformers"].append(video)
                
        return {
            "performance_thresholds": {
                "elite": elite_threshold,
                "good": good_threshold,
                "average": average_threshold
            },
            "category_counts": {
                "elite": len(performance_categories["elite_performers"]),
                "good": len(performance_categories["good_performers"]),
                "average": len(performance_categories["average_performers"]),
                "underperforming": len(performance_categories["underperformers"])
            },
            "elite_video_titles": [v['title'] for v in performance_categories["elite_performers"][:3]],
            "underperforming_analysis": self._analyze_underperformers(performance_categories["underperformers"])
        }
        
    def _analyze_underperformers(self, underperformers: List[Dict]) -> Dict[str, Any]:
        """低パフォーマンス動画の分析"""
        if not underperformers:
            return {"message": "低パフォーマンス動画なし"}
            
        # 共通テーマを抽出
        themes = {}
        for video in underperformers:
            theme = self._extract_theme_from_video(video)
            themes[theme] = themes.get(theme, 0) + 1
            
        common_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "count": len(underperformers),
            "common_themes": common_themes,
            "avg_views": round(sum(v['previous_views'] for v in underperformers) / len(underperformers), 2),
            "avg_engagement_rate": round(sum((v['previous_likes'] + v['previous_comments']) / v['previous_views'] * 100 if v['previous_views'] > 0 else 0 for v in underperformers) / len(underperformers), 2)
        }
        
    def _analyze_content_strategy(self, videos_data: List[Dict], relative_analysis: Dict) -> Dict[str, Any]:
        """コンテンツ戦略分析"""
        theme_performance = relative_analysis.get("theme_analysis", {}).get("theme_performance", {})
        
        if not theme_performance:
            return {"error": "テーマ分析データなし"}
            
        # テーマ別戦略分析
        strategy_recommendations = {}
        
        for theme, data in theme_performance.items():
            video_count = data.get("video_count", 0)
            avg_views = data.get("avg_views", 0)
            avg_engagement = data.get("avg_engagement_rate", 0)
            
            # 戦略カテゴリを決定
            if avg_views > 0 and video_count >= 2:
                if avg_views >= 1000 and avg_engagement >= 3.0:
                    strategy = "優先継続・拡大"
                elif avg_views >= 500 or avg_engagement >= 2.0:
                    strategy = "改善・最適化"
                else:
                    strategy = "見直し・実験"
            elif video_count == 1:
                strategy = "検証・追加投稿"
            else:
                strategy = "新規検討"
                
            strategy_recommendations[theme] = {
                "current_performance": {
                    "video_count": video_count,
                    "avg_views": round(avg_views, 2),
                    "avg_engagement": round(avg_engagement, 2)
                },
                "strategy": strategy,
                "priority_score": self._calculate_theme_priority_score(avg_views, avg_engagement, video_count)
            }
            
        # 優先度順にソート
        sorted_strategies = sorted(
            strategy_recommendations.items(),
            key=lambda x: x[1]["priority_score"],
            reverse=True
        )
        
        return {
            "theme_strategies": dict(sorted_strategies),
            "content_diversity_score": len(theme_performance),
            "recommended_focus_themes": [item[0] for item in sorted_strategies[:3]],
            "experimental_themes": [theme for theme, data in strategy_recommendations.items() 
                                  if data["strategy"] in ["見直し・実験", "新規検討"]]
        }
        
    def _calculate_theme_priority_score(self, avg_views: float, avg_engagement: float, video_count: int) -> float:
        """テーマの優先度スコアを計算"""
        views_score = min(avg_views / 1000, 10)  # 最大10点
        engagement_score = min(avg_engagement, 10)  # 最大10点
        consistency_score = min(video_count, 5)  # 最大5点
        
        return views_score + engagement_score + consistency_score
        
    def _generate_improvement_plans(self, relative_analysis: Dict, trend_analysis: Dict, 
                                  competitive_analysis: Dict, content_strategy: Dict) -> List[Dict[str, Any]]:
        """改善計画を生成"""
        plans = []
        
        # 1. コンテンツ戦略改善計画
        if content_strategy.get("recommended_focus_themes"):
            focus_themes = content_strategy["recommended_focus_themes"][:2]
            plans.append({
                "category": "コンテンツ戦略",
                "priority": "高",
                "action": f"高パフォーマンステーマ「{focus_themes[0]}」「{focus_themes[1] if len(focus_themes) > 1 else ''}」に集中",
                "expected_outcome": "平均再生数の向上",
                "timeline": "次の5本の動画"
            })
            
        # 2. パフォーマンストレンド改善計画
        trend_status = trend_analysis.get("trend_status", "")
        if trend_status in ["低下気味", "要改善"]:
            plans.append({
                "category": "パフォーマンス改善",
                "priority": "高",
                "action": "エンゲージメント要素の強化（視聴者参加型クイズ、コメント促進）",
                "expected_outcome": "エンゲージメント率の回復",
                "timeline": "即座実行"
            })
            
        # 3. 低パフォーマンス動画の分析に基づく改善計画
        underperforming_data = competitive_analysis.get("underperforming_analysis", {})
        if underperforming_data.get("count", 0) > 0:
            common_themes = underperforming_data.get("common_themes", [])
            if common_themes:
                avoided_theme = common_themes[0][0]
                plans.append({
                    "category": "テーマ最適化",
                    "priority": "中",
                    "action": f"「{avoided_theme}」テーマの見直しまたは一時休止",
                    "expected_outcome": "全体平均パフォーマンスの向上",
                    "timeline": "次回企画検討時"
                })
                
        # 4. 問題数維持計画
        plans.append({
            "category": "品質保証",
            "priority": "最高",
            "action": "漢字クイズは必ず10問で構成し、質を担保する",
            "expected_outcome": "視聴者満足度維持、チャンネル信頼性確保",
            "timeline": "毎回の動画制作"
        })
        
        return plans
        
    def _generate_next_video_recommendations(self, relative_analysis: Dict, content_strategy: Dict) -> List[Dict[str, Any]]:
        """次の動画制作の推奨事項を生成"""
        recommendations = []
        
        # テーマ推奨
        focus_themes = content_strategy.get("recommended_focus_themes", [])
        if focus_themes:
            recommendations.append({
                "type": "テーマ選択",
                "recommendation": f"「{focus_themes[0]}」テーマで10問構成",
                "reason": "最高パフォーマンステーマでの継続投稿"
            })
            
        # エンゲージメント向上施策
        avg_engagement = relative_analysis.get("performance_metrics", {}).get("engagement_rate", {}).get("avg", 0)
        if avg_engagement < 3.0:
            recommendations.append({
                "type": "エンゲージメント強化",
                "recommendation": "視聴者向け難易度調整とコメント促進要素の追加",
                "reason": f"現在のエンゲージメント率{avg_engagement:.2f}%の向上のため"
            })
            
        # 投稿タイミング
        recommendations.append({
            "type": "投稿戦略",
            "recommendation": "安定した投稿頻度を維持し、必ず10問構成を守る",
            "reason": "視聴者の期待に応え、チャンネル信頼性を保つため"
        })
        
        return recommendations
        
    def _extract_theme_from_video(self, video: Dict) -> str:
        """動画からテーマを抽出（PerformanceAnalyzerと同じロジック）"""
        try:
            if video.get('script'):
                script_data = json.loads(video['script'])
                return script_data.get('theme', '不明')
        except (json.JSONDecodeError, TypeError):
            pass
        
        # タイトルからテーマを推測
        title = video.get('title', '').lower()
        if '春' in title or 'はる' in title:
            return '春'
        elif '夏' in title or 'なつ' in title:
            return '夏'
        elif '秋' in title or 'あき' in title:
            return '秋'
        elif '冬' in title or 'ふゆ' in title:
            return '冬'
        elif '動物' in title or 'どうぶつ' in title:
            return '動物'
        elif '食べ物' in title or 'たべもの' in title:
            return '食べ物'
        elif '難読' in title:
            return '難読漢字'
        else:
            return '不明'