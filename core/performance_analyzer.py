# performance_analyzer.py
import json
import statistics
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

class PerformanceAnalyzer:
    """動画のパフォーマンスを相対評価・分析するクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_relative_performance(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """
        動画のパフォーマンスを相対評価し、チャンネル内での位置付けを分析する
        
        Args:
            videos_data: 動画データのリスト（get_all_videos_for_reportから取得）
        
        Returns:
            Dict: 相対評価分析結果
        """
        self.logger.info("動画の相対評価分析を開始...")
        
        if not videos_data or len(videos_data) < 2:
            self.logger.warning("相対評価に必要なデータが不足しています。")
            return {"error": "データ不足"}
        
        # パフォーマンス指標を計算
        performance_metrics = self._calculate_performance_metrics(videos_data)
        
        # 動画別順位付け
        rankings = self._calculate_rankings(videos_data)
        
        # テーマ別分析
        theme_analysis = self._analyze_by_theme(videos_data)
        
        # パフォーマンス分布分析
        distribution_analysis = self._analyze_performance_distribution(videos_data)
        
        # 改善提案の生成
        improvement_suggestions = self._generate_improvement_suggestions(
            performance_metrics, theme_analysis, rankings
        )
        
        analysis_result = {
            "analyzed_videos_count": len(videos_data),
            "analysis_timestamp": datetime.now().isoformat(),
            "performance_metrics": performance_metrics,
            "rankings": rankings,
            "theme_analysis": theme_analysis,
            "distribution_analysis": distribution_analysis,
            "improvement_suggestions": improvement_suggestions
        }
        
        self.logger.info(f"相対評価分析完了: {len(videos_data)}本の動画を分析")
        # 再生数変化分析を追加
        trend_analysis = self._analyze_view_trends(videos_data)
        analysis_result["trend_analysis"] = trend_analysis
        
        return analysis_result
    
    def _calculate_performance_metrics(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """パフォーマンス指標を計算"""
        views = [v['previous_views'] for v in videos_data if v['previous_views'] > 0]
        likes = [v['previous_likes'] for v in videos_data if v['previous_likes'] >= 0]
        comments = [v['previous_comments'] for v in videos_data if v['previous_comments'] >= 0]
        
        # エンゲージメント率を計算
        engagement_rates = []
        for v in videos_data:
            if v['previous_views'] > 0:
                engagement_rate = (v['previous_likes'] + v['previous_comments']) / v['previous_views'] * 100
                engagement_rates.append(engagement_rate)
        
        # 高評価率を計算
        like_rates = []
        for v in videos_data:
            if v['previous_views'] > 0:
                like_rate = v['previous_likes'] / v['previous_views'] * 100
                like_rates.append(like_rate)
        
        return {
            "views": {
                "avg": statistics.mean(views) if views else 0,
                "median": statistics.median(views) if views else 0,
                "max": max(views) if views else 0,
                "min": min(views) if views else 0,
                "std": statistics.stdev(views) if len(views) > 1 else 0
            },
            "likes": {
                "avg": statistics.mean(likes) if likes else 0,
                "median": statistics.median(likes) if likes else 0,
                "max": max(likes) if likes else 0,
                "min": min(likes) if likes else 0
            },
            "comments": {
                "avg": statistics.mean(comments) if comments else 0,
                "median": statistics.median(comments) if comments else 0,
                "max": max(comments) if comments else 0,
                "min": min(comments) if comments else 0
            },
            "engagement_rate": {
                "avg": statistics.mean(engagement_rates) if engagement_rates else 0,
                "median": statistics.median(engagement_rates) if engagement_rates else 0,
                "max": max(engagement_rates) if engagement_rates else 0,
                "min": min(engagement_rates) if engagement_rates else 0
            },
            "like_rate": {
                "avg": statistics.mean(like_rates) if like_rates else 0,
                "median": statistics.median(like_rates) if like_rates else 0,
                "max": max(like_rates) if like_rates else 0,
                "min": min(like_rates) if like_rates else 0
            }
        }
    
    def _calculate_rankings(self, videos_data: List[Dict]) -> Dict[str, List[Dict]]:
        """動画を各指標でランキング化"""
        # 再生数ランキング
        views_ranking = sorted(
            videos_data, 
            key=lambda x: x['previous_views'], 
            reverse=True
        )
        
        # エンゲージメント率ランキング
        engagement_ranking = []
        for v in videos_data:
            if v['previous_views'] > 0:
                engagement_rate = (v['previous_likes'] + v['previous_comments']) / v['previous_views'] * 100
                engagement_ranking.append({
                    **v,
                    "engagement_rate": engagement_rate
                })
        engagement_ranking = sorted(engagement_ranking, key=lambda x: x['engagement_rate'], reverse=True)
        
        # 高評価率ランキング
        like_rate_ranking = []
        for v in videos_data:
            if v['previous_views'] > 0:
                like_rate = v['previous_likes'] / v['previous_views'] * 100
                like_rate_ranking.append({
                    **v,
                    "like_rate": like_rate
                })
        like_rate_ranking = sorted(like_rate_ranking, key=lambda x: x['like_rate'], reverse=True)
        
        # コメント数ランキング
        comments_ranking = sorted(
            videos_data,
            key=lambda x: x['previous_comments'],
            reverse=True
        )
        
        return {
            "views_top10": views_ranking[:10],
            "engagement_top10": engagement_ranking[:10],
            "like_rate_top10": like_rate_ranking[:10],
            "comments_top10": comments_ranking[:10],
            "views_bottom5": views_ranking[-5:] if len(views_ranking) >= 5 else views_ranking,
            "engagement_bottom5": engagement_ranking[-5:] if len(engagement_ranking) >= 5 else engagement_ranking
        }
    
    def _analyze_by_theme(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """テーマ別のパフォーマンス分析"""
        theme_data = {}
        
        for video in videos_data:
            theme = self._extract_theme_from_video(video)
            
            if theme not in theme_data:
                theme_data[theme] = {
                    "count": 0,
                    "total_views": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "videos": []
                }
            
            theme_data[theme]["count"] += 1
            theme_data[theme]["total_views"] += video['previous_views']
            theme_data[theme]["total_likes"] += video['previous_likes']
            theme_data[theme]["total_comments"] += video['previous_comments']
            theme_data[theme]["videos"].append({
                "title": video['title'],
                "video_id": video['video_id'],
                "views": video['previous_views'],
                "likes": video['previous_likes'],
                "comments": video['previous_comments']
            })
        
        # テーマ別平均パフォーマンスを計算
        theme_performance = {}
        for theme, data in theme_data.items():
            if data["count"] > 0:
                theme_performance[theme] = {
                    "video_count": data["count"],
                    "avg_views": data["total_views"] / data["count"],
                    "avg_likes": data["total_likes"] / data["count"],
                    "avg_comments": data["total_comments"] / data["count"],
                    "avg_engagement_rate": (data["total_likes"] + data["total_comments"]) / data["total_views"] * 100 if data["total_views"] > 0 else 0,
                    "total_views": data["total_views"],
                    "best_performing_video": max(data["videos"], key=lambda x: x['views']) if data["videos"] else None
                }
        
        # テーマをパフォーマンスでソート
        sorted_themes = sorted(
            theme_performance.items(),
            key=lambda x: x[1]['avg_views'],
            reverse=True
        )
        
        return {
            "theme_performance": dict(sorted_themes),
            "total_themes": len(theme_performance),
            "most_popular_theme": sorted_themes[0][0] if sorted_themes else "不明",
            "theme_diversity_score": len(theme_performance) / len(videos_data) if videos_data else 0
        }
    
    def _analyze_performance_distribution(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """パフォーマンス分布を分析"""
        views = [v['previous_views'] for v in videos_data if v['previous_views'] > 0]
        
        if not views:
            return {"error": "再生数データがありません"}
        
        # パフォーマンス区分を定義
        median_views = statistics.median(views)
        q1 = statistics.quantiles(views, n=4)[0] if len(views) >= 4 else median_views * 0.5
        q3 = statistics.quantiles(views, n=4)[2] if len(views) >= 4 else median_views * 1.5
        
        performance_categories = {
            "high_performers": [],  # Q3以上
            "above_average": [],    # メディアン〜Q3
            "below_average": [],    # Q1〜メディアン
            "low_performers": []    # Q1未満
        }
        
        for video in videos_data:
            views = video['previous_views']
            if views >= q3:
                performance_categories["high_performers"].append(video)
            elif views >= median_views:
                performance_categories["above_average"].append(video)
            elif views >= q1:
                performance_categories["below_average"].append(video)
            else:
                performance_categories["low_performers"].append(video)
        
        return {
            "quartiles": {"q1": q1, "median": median_views, "q3": q3},
            "distribution": {
                "high_performers_count": len(performance_categories["high_performers"]),
                "above_average_count": len(performance_categories["above_average"]),
                "below_average_count": len(performance_categories["below_average"]),
                "low_performers_count": len(performance_categories["low_performers"])
            },
            "performance_categories": performance_categories
        }
    
    def _generate_improvement_suggestions(self, metrics: Dict, theme_analysis: Dict, rankings: Dict) -> List[str]:
        """改善提案を生成"""
        suggestions = []
        
        # テーマ戦略の提案
        if theme_analysis.get("theme_performance"):
            top_themes = list(theme_analysis["theme_performance"].keys())[:3]
            if top_themes:
                suggestions.append(f"高パフォーマンステーマ「{top_themes[0]}」を中心とした動画制作を増やす")
        
        # エンゲージメント改善提案
        if metrics.get("engagement_rate", {}).get("avg", 0) < 3.0:
            suggestions.append("エンゲージメント率が低いため、視聴者参加要素（質問・クイズ）を強化する")
        
        # 再生数向上提案
        avg_views = metrics.get("views", {}).get("avg", 0)
        max_views = metrics.get("views", {}).get("max", 0)
        if avg_views > 0 and max_views > avg_views * 2:
            suggestions.append("トップパフォーマンス動画の成功要因を分析し、他の動画に応用する")
        
        # コンテンツ多様性の提案
        theme_diversity = theme_analysis.get("theme_diversity_score", 0)
        if theme_diversity < 0.3:
            suggestions.append("テーマの多様性を増やして新しい視聴者層を開拓する")
        
        return suggestions
    
    def _extract_theme_from_video(self, video: Dict) -> str:
        """動画からテーマを抽出"""
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
    
    def get_relative_performance_score(self, video_data: Dict, all_videos: List[Dict]) -> Dict[str, float]:
        """
        特定の動画のチャンネル内相対パフォーマンススコアを計算
        
        Args:
            video_data: 対象動画のデータ
            all_videos: 全動画のデータ
        
        Returns:
            Dict: 各指標の相対スコア（0-100）
        """
        if len(all_videos) < 2:
            return {"views": 50.0, "likes": 50.0, "comments": 50.0, "engagement": 50.0}
        
        # 各指標での順位を計算
        views_rank = self._get_rank_percentile(video_data['previous_views'], [v['previous_views'] for v in all_videos])
        likes_rank = self._get_rank_percentile(video_data['previous_likes'], [v['previous_likes'] for v in all_videos])
        comments_rank = self._get_rank_percentile(video_data['previous_comments'], [v['previous_comments'] for v in all_videos])
        
        # エンゲージメント率の計算と順位
        current_engagement = (video_data['previous_likes'] + video_data['previous_comments']) / video_data['previous_views'] * 100 if video_data['previous_views'] > 0 else 0
        all_engagement_rates = []
        for v in all_videos:
            if v['previous_views'] > 0:
                engagement_rate = (v['previous_likes'] + v['previous_comments']) / v['previous_views'] * 100
                all_engagement_rates.append(engagement_rate)
        
        engagement_rank = self._get_rank_percentile(current_engagement, all_engagement_rates)
        
        return {
            "views": views_rank,
            "likes": likes_rank,
            "comments": comments_rank,
            "engagement": engagement_rank,
            "overall": (views_rank + likes_rank + comments_rank + engagement_rank) / 4
        }
    
    def _get_rank_percentile(self, value: float, all_values: List[float]) -> float:
        """値のパーセンタイル順位を計算（0-100）"""
        if not all_values:
            return 50.0
        
        sorted_values = sorted(all_values)
        if value <= sorted_values[0]:
            return 0.0
        if value >= sorted_values[-1]:
            return 100.0
        
        # パーセンタイル計算
        rank = sum(1 for v in sorted_values if v <= value)
        percentile = (rank / len(sorted_values)) * 100
        return percentile
    
    def _analyze_view_trends(self, videos_data: List[Dict]) -> Dict[str, Any]:
        """再生数変化に基づくトレンド分析"""
        self.logger.info("再生数変化のトレンド分析を開始...")
        
        # 前回記録された再生数と現在の再生数で変化を計算
        growing_videos = []
        theme_growth = {}
        
        for video in videos_data:
            # latest_statsは現在の統計、previous_viewsは前回記録された再生数
            if hasattr(video, 'latest_stats') and video.get('latest_stats'):
                current_views = video['latest_stats']['views']
                previous_views = video['previous_views']
                view_change = current_views - previous_views
                
                if view_change > 0:
                    growing_videos.append({
                        'video_id': video['video_id'],
                        'title': video['title'],
                        'view_change': view_change,
                        'growth_rate': (view_change / max(previous_views, 1)) * 100,
                        'current_views': current_views,
                        'previous_views': previous_views
                    })
                    
                    # テーマ別成長分析と解説の長さ分析
                    theme = self._extract_theme_from_video(video)
                    avg_explanation_length = self._get_avg_explanation_length(video)
                    
                    if theme not in theme_growth:
                        theme_growth[theme] = {
                            'total_growth': 0,
                            'video_count': 0,
                            'videos': [],
                            'explanation_lengths': []
                        }
                    
                    theme_growth[theme]['total_growth'] += view_change
                    theme_growth[theme]['video_count'] += 1
                    theme_growth[theme]['explanation_lengths'].append(avg_explanation_length)
                    theme_growth[theme]['videos'].append({
                        'title': video['title'],
                        'view_change': view_change,
                        'growth_rate': (view_change / max(previous_views, 1)) * 100,
                        'avg_explanation_length': avg_explanation_length
                    })
        
        # 成長率でソート
        growing_videos.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        # テーマ別平均成長率と解説の長さの傾向を計算
        theme_avg_growth = {}
        for theme, data in theme_growth.items():
            if data['video_count'] > 0:
                avg_explanation_length = sum(data['explanation_lengths']) / len(data['explanation_lengths']) if data['explanation_lengths'] else 0
                theme_avg_growth[theme] = {
                    'avg_growth': data['total_growth'] / data['video_count'],
                    'total_growth': data['total_growth'],
                    'video_count': data['video_count'],
                    'avg_explanation_length': avg_explanation_length,
                    'best_video': max(data['videos'], key=lambda x: x['growth_rate']) if data['videos'] else None
                }
        
        # テーマを平均成長でソート
        sorted_themes = sorted(
            theme_avg_growth.items(),
            key=lambda x: x[1]['avg_growth'],
            reverse=True
        )
        
        # 解説の長さと成長率の相関分析
        explanation_analysis = self._analyze_explanation_correlation(growing_videos)
        
        return {
            'growing_videos_count': len(growing_videos),
            'top_growing_videos': growing_videos[:10],
            'trending_themes': dict(sorted_themes),
            'most_trending_theme': sorted_themes[0][0] if sorted_themes else "不明",
            'total_view_growth': sum(v['view_change'] for v in growing_videos),
            'avg_growth_rate': sum(v['growth_rate'] for v in growing_videos) / len(growing_videos) if growing_videos else 0,
            'explanation_analysis': explanation_analysis
        }
    
    def _get_avg_explanation_length(self, video: Dict) -> float:
        """動画の平均解説文字数を計算"""
        try:
            if video.get('script'):
                script_data = json.loads(video['script'])
                quiz_data = script_data.get('quiz_data', [])
                
                total_length = 0
                count = 0
                for question in quiz_data:
                    kaisetsu = question.get('kaisetsu', '')
                    if kaisetsu:
                        total_length += len(kaisetsu)
                        count += 1
                
                return total_length / count if count > 0 else 0
        except (json.JSONDecodeError, TypeError):
            pass
        return 0
    
    def _analyze_explanation_correlation(self, growing_videos: List[Dict]) -> Dict[str, Any]:
        """解説の長さと成長率の相関を分析"""
        if not growing_videos:
            return {'message': '成長している動画がありません'}
        
        # 解説の長さごとにグループ化
        short_explanations = []  # 0-30文字
        medium_explanations = []  # 31-60文字  
        long_explanations = []   # 61文字以上
        
        for video in growing_videos:
            length = video.get('avg_explanation_length', 0)
            if length <= 30:
                short_explanations.append(video)
            elif length <= 60:
                medium_explanations.append(video)
            else:
                long_explanations.append(video)
        
        def calc_avg_growth(videos):
            return sum(v['growth_rate'] for v in videos) / len(videos) if videos else 0
        
        return {
            'short_explanations': {
                'count': len(short_explanations),
                'avg_growth_rate': calc_avg_growth(short_explanations),
                'length_range': '0-30文字'
            },
            'medium_explanations': {
                'count': len(medium_explanations),
                'avg_growth_rate': calc_avg_growth(medium_explanations),
                'length_range': '31-60文字'
            },
            'long_explanations': {
                'count': len(long_explanations),
                'avg_growth_rate': calc_avg_growth(long_explanations),
                'length_range': '61文字以上'
            },
            'recommendation': self._get_explanation_length_recommendation(
                calc_avg_growth(short_explanations),
                calc_avg_growth(medium_explanations), 
                calc_avg_growth(long_explanations)
            )
        }
    
    def _get_explanation_length_recommendation(self, short_growth: float, medium_growth: float, long_growth: float) -> str:
        """解説の長さに基づく推奨事項を生成"""
        max_growth = max(short_growth, medium_growth, long_growth)
        
        if max_growth == short_growth:
            return "短い解説（0-30文字）が最も効果的です。簡潔で覚えやすい解説を心がけましょう。"
        elif max_growth == medium_growth:
            return "中程度の解説（31-60文字）が最も効果的です。適度な詳しさが視聴者に好まれています。"
        else:
            return "長い解説（61文字以上）が最も効果的です。詳しい豆知識が視聴者の興味を引いています。"