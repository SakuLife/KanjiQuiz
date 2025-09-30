# unified_scoring_system.py
"""
統一スコアリングシステム
動画パフォーマンスを0-100点で評価し、改善提案を生成する
"""

import json
import statistics
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging

class UnifiedScoringSystem:
    """動画パフォーマンスの統一評価システム"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # スコアリング重み設定
        self.weights = {
            'views': 0.60,        # 再生数
            'comments_count': 0.25,  # コメント数
            'comments_quality': 0.10, # コメント内容の質
            'likes': 0.05         # いいね数
        }
        
        # チャンネル成長段階に応じた目標設定
        self.growth_targets = {
            'micro': {  # 0-100フォロワー (現状)
                'min_subscribers': 0,
                'max_subscribers': 100,
                'target_views_per_video': 50,
                'target_comments_per_video': 2,
                'target_likes_per_video': 3,
                'excellent_threshold': 80,  # 80点以上で優秀
                'good_threshold': 60       # 60点以上で良好
            },
            'small': {  # 100-1000フォロワー
                'min_subscribers': 100,
                'max_subscribers': 1000,
                'target_views_per_video': 200,
                'target_comments_per_video': 8,
                'target_likes_per_video': 15,
                'excellent_threshold': 85,
                'good_threshold': 65
            }
        }
        
        # テーマ別難易度補正（テーマが取りにくいものほど高い補正）
        self.theme_difficulty_bonus = {
            '春': 1.0,      # 季節物は一般的
            '夏': 1.0,
            '秋': 1.0,
            '冬': 1.0,
            '食べ物': 1.1,   # やや人気
            '動物': 1.1,
            '難読漢字': 1.3, # 専門性が高い
            '魚へん': 1.2,   # ニッチ
            '虫へん': 1.4,   # かなりニッチ
            '不明': 1.0
        }
    
    def calculate_unified_score(self, video_data: Dict, all_videos: List[Dict], channel_subscribers: int = 50) -> Dict[str, Any]:
        """
        統一スコア（0-100点）を算出
        
        Args:
            video_data: 対象動画のデータ
            all_videos: 全動画のデータ（相対評価用）
            channel_subscribers: チャンネル登録者数
            
        Returns:
            スコア詳細とレコメンデーション
        """
        # 成長段階の特定
        growth_stage = self._get_growth_stage(channel_subscribers)
        targets = self.growth_targets[growth_stage]
        
        # 各指標のスコア算出
        views_score = self._calculate_views_score(video_data, all_videos, targets)
        comments_count_score = self._calculate_comments_count_score(video_data, all_videos, targets)
        comments_quality_score = self._calculate_comments_quality_score(video_data)
        likes_score = self._calculate_likes_score(video_data, all_videos, targets)
        
        # テーマ別難易度補正
        theme_bonus = self._get_theme_difficulty_bonus(video_data)
        
        # 重み付き合計スコア
        weighted_score = (
            views_score * self.weights['views'] +
            comments_count_score * self.weights['comments_count'] +
            comments_quality_score * self.weights['comments_quality'] +
            likes_score * self.weights['likes']
        )
        
        # テーマ補正適用（最大110点まで）
        final_score = min(110, weighted_score * theme_bonus)
        
        # ランク付け
        rank = self._get_performance_rank(final_score, targets)
        
        # 改善提案生成
        recommendations = self._generate_recommendations(
            video_data, views_score, comments_count_score, 
            comments_quality_score, likes_score, targets
        )
        
        return {
            'unified_score': round(final_score, 1),
            'rank': rank,
            'growth_stage': growth_stage,
            'score_breakdown': {
                'views': round(views_score, 1),
                'comments_count': round(comments_count_score, 1),
                'comments_quality': round(comments_quality_score, 1),
                'likes': round(likes_score, 1)
            },
            'theme_bonus': round(theme_bonus, 2),
            'recommendations': recommendations,
            'targets': targets
        }
    
    def _get_growth_stage(self, subscribers: int) -> str:
        """チャンネルの成長段階を判定"""
        for stage, data in self.growth_targets.items():
            if data['min_subscribers'] <= subscribers <= data['max_subscribers']:
                return stage
        return 'micro'  # デフォルト
    
    def _calculate_views_score(self, video_data: Dict, all_videos: List[Dict], targets: Dict) -> float:
        """再生数スコア算出（相対評価50% + 絶対評価50%）"""
        views = video_data.get('latest_stats', {}).get('views', 0)
        
        # 相対評価（チャンネル内順位）
        all_views = [v.get('latest_stats', {}).get('views', 0) for v in all_videos if v.get('latest_stats', {}).get('views', 0) > 0]
        if all_views:
            percentile = self._calculate_percentile(views, all_views)
            relative_score = percentile
        else:
            relative_score = 50
        
        # 絶対評価（目標達成度）
        target_views = targets['target_views_per_video']
        absolute_score = min(100, (views / target_views) * 100)
        
        # 50%ずつで合成
        return (relative_score * 0.5) + (absolute_score * 0.5)
    
    def _calculate_comments_count_score(self, video_data: Dict, all_videos: List[Dict], targets: Dict) -> float:
        """コメント数スコア算出"""
        comments = video_data.get('latest_stats', {}).get('comments', 0)
        
        # 相対評価
        all_comments = [v.get('latest_stats', {}).get('comments', 0) for v in all_videos]
        percentile = self._calculate_percentile(comments, all_comments)
        
        # 絶対評価
        target_comments = targets['target_comments_per_video']
        absolute_score = min(100, (comments / target_comments) * 100)
        
        return (percentile * 0.5) + (absolute_score * 0.5)
    
    def _calculate_comments_quality_score(self, video_data: Dict) -> float:
        """コメント内容の質スコア算出"""
        # 現状はプレースホルダー（将来的にコメント内容分析を実装）
        # ポジティブ/ネガティブ、長さ、建設的フィードバックの有無等
        
        comments_count = video_data.get('latest_stats', {}).get('comments', 0)
        
        # コメント数に基づく簡易評価
        if comments_count == 0:
            return 0
        elif comments_count <= 2:
            return 50  # 基本点
        elif comments_count <= 5:
            return 70  # 中程度のエンゲージメント
        else:
            return 90  # 高いエンゲージメント
    
    def _calculate_likes_score(self, video_data: Dict, all_videos: List[Dict], targets: Dict) -> float:
        """いいね数スコア算出"""
        likes = video_data.get('latest_stats', {}).get('likes', 0)
        
        # 相対評価
        all_likes = [v.get('latest_stats', {}).get('likes', 0) for v in all_videos]
        percentile = self._calculate_percentile(likes, all_likes)
        
        # 絶対評価
        target_likes = targets['target_likes_per_video']
        absolute_score = min(100, (likes / target_likes) * 100)
        
        return (percentile * 0.5) + (absolute_score * 0.5)
    
    def _get_theme_difficulty_bonus(self, video_data: Dict) -> float:
        """テーマ別難易度ボーナス算出"""
        try:
            if video_data.get('script'):
                script_data = json.loads(video_data['script'])
                theme = script_data.get('theme', '不明')
                return self.theme_difficulty_bonus.get(theme, 1.0)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # スクリプトからテーマを抽出できない場合はタイトルから推測
        title = video_data.get('title', '').lower()
        for theme_key, bonus in self.theme_difficulty_bonus.items():
            if theme_key in title:
                return bonus
        
        return 1.0  # デフォルト
    
    def _calculate_percentile(self, value: float, all_values: List[float]) -> float:
        """パーセンタイル順位を計算（0-100）"""
        if not all_values or len(all_values) < 2:
            return 50.0
        
        sorted_values = sorted(all_values)
        rank = sum(1 for v in sorted_values if v <= value)
        return (rank / len(sorted_values)) * 100
    
    def _get_performance_rank(self, score: float, targets: Dict) -> str:
        """スコアに基づくランク付け"""
        if score >= targets['excellent_threshold']:
            return 'S'  # 優秀
        elif score >= targets['good_threshold']:
            return 'A'  # 良好
        elif score >= 40:
            return 'B'  # 普通
        elif score >= 20:
            return 'C'  # 要改善
        else:
            return 'D'  # 大幅改善必要
    
    def _generate_recommendations(self, video_data: Dict, views_score: float, 
                                comments_score: float, quality_score: float, 
                                likes_score: float, targets: Dict) -> List[str]:
        """具体的な改善提案を生成"""
        recommendations = []
        
        # 再生数改善提案
        if views_score < 50:
            recommendations.append("タイトルをより興味を引くものに変更（例：「○○の難読漢字」→「読めたら天才！○○の超難読漢字クイズ」）")
            recommendations.append("サムネイルに問題の一部を表示して視覚的な興味を引く")
        
        # コメント数改善提案
        if comments_score < 50:
            recommendations.append("動画内で視聴者に質問を投げかける（例：「全問正解できた人はコメントで教えて！」）")
            recommendations.append("コメント欄でのやり取りを促進する仕掛けを追加")
        
        # コメント質改善提案
        if quality_score < 50:
            recommendations.append("より議論を呼ぶような問題を含める")
            recommendations.append("解説で豆知識を充実させ、コメントでの共有を促す")
        
        # テーマ別改善提案
        theme_bonus = self._get_theme_difficulty_bonus(video_data)
        if theme_bonus < 1.1:
            recommendations.append("より専門性の高いテーマ（虫へん、難読漢字など）に挑戦してみる")
        
        # 解説の長さ改善提案
        avg_explanation_length = self._get_avg_explanation_length(video_data)
        if avg_explanation_length > 60:
            recommendations.append("解説を60文字以内に短縮し、テンポを向上させる")
        elif avg_explanation_length < 20:
            recommendations.append("解説に豆知識を追加して30-50文字程度に充実させる")
        
        return recommendations[:3]  # 最大3つの提案
    
    def _get_avg_explanation_length(self, video_data: Dict) -> float:
        """平均解説文字数を取得"""
        try:
            if video_data.get('script'):
                script_data = json.loads(video_data['script'])
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

    def analyze_channel_performance(self, all_videos: List[Dict], channel_subscribers: int = 50) -> Dict[str, Any]:
        """チャンネル全体のパフォーマンス分析"""
        if not all_videos:
            return {'error': '分析対象の動画がありません'}
        
        # 各動画のスコア算出
        scored_videos = []
        for video in all_videos:
            if video.get('latest_stats', {}).get('views', 0) >= 1:
                score_data = self.calculate_unified_score(video, all_videos, channel_subscribers)
                scored_videos.append({
                    **video,
                    'score_data': score_data
                })
        
        if not scored_videos:
            return {'error': 'スコア算出可能な動画がありません'}
        
        # 統計情報算出
        scores = [v['score_data']['unified_score'] for v in scored_videos]
        
        # ランク別集計
        rank_counts = {}
        for video in scored_videos:
            rank = video['score_data']['rank']
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        # トップパフォーマーとワーストパフォーマー
        top_performers = sorted(scored_videos, key=lambda x: x['score_data']['unified_score'], reverse=True)[:3]
        worst_performers = sorted(scored_videos, key=lambda x: x['score_data']['unified_score'])[:3]
        
        # テーマ別パフォーマンス
        theme_performance = self._analyze_theme_performance(scored_videos)
        
        return {
            'total_videos_analyzed': len(scored_videos),
            'average_score': round(statistics.mean(scores), 1),
            'median_score': round(statistics.median(scores), 1),
            'score_distribution': {
                'max': round(max(scores), 1),
                'min': round(min(scores), 1),
                'std': round(statistics.stdev(scores) if len(scores) > 1 else 0, 1)
            },
            'rank_distribution': rank_counts,
            'top_performers': [
                {
                    'title': v['title'],
                    'score': v['score_data']['unified_score'],
                    'rank': v['score_data']['rank']
                } for v in top_performers
            ],
            'worst_performers': [
                {
                    'title': v['title'],
                    'score': v['score_data']['unified_score'],
                    'rank': v['score_data']['rank']
                } for v in worst_performers
            ],
            'theme_performance': theme_performance,
            'channel_recommendations': self._generate_channel_recommendations(scored_videos, theme_performance)
        }
    
    def _analyze_theme_performance(self, scored_videos: List[Dict]) -> Dict[str, Any]:
        """テーマ別パフォーマンス分析"""
        theme_data = {}
        
        for video in scored_videos:
            # テーマ抽出
            theme = '不明'
            try:
                if video.get('script'):
                    script_data = json.loads(video['script'])
                    theme = script_data.get('theme', '不明')
            except (json.JSONDecodeError, TypeError):
                pass
            
            if theme not in theme_data:
                theme_data[theme] = {
                    'videos': [],
                    'scores': [],
                    'total_views': 0,
                    'total_comments': 0
                }
            
            theme_data[theme]['videos'].append(video)
            theme_data[theme]['scores'].append(video['score_data']['unified_score'])
            theme_data[theme]['total_views'] += video.get('latest_stats', {}).get('views', 0)
            theme_data[theme]['total_comments'] += video.get('latest_stats', {}).get('comments', 0)
        
        # テーマ別統計
        theme_stats = {}
        for theme, data in theme_data.items():
            if data['scores']:
                theme_stats[theme] = {
                    'video_count': len(data['videos']),
                    'avg_score': round(statistics.mean(data['scores']), 1),
                    'avg_views': round(data['total_views'] / len(data['videos']), 1),
                    'avg_comments': round(data['total_comments'] / len(data['videos']), 1),
                    'best_video': max(data['videos'], key=lambda x: x['score_data']['unified_score'])['title']
                }
        
        # パフォーマンス順でソート
        sorted_themes = sorted(theme_stats.items(), key=lambda x: x[1]['avg_score'], reverse=True)
        
        return dict(sorted_themes)
    
    def _generate_channel_recommendations(self, scored_videos: List[Dict], theme_performance: Dict) -> List[str]:
        """チャンネル全体の改善提案"""
        recommendations = []
        
        # 低スコア動画の傾向分析
        low_score_videos = [v for v in scored_videos if v['score_data']['unified_score'] < 50]
        
        if len(low_score_videos) > len(scored_videos) * 0.3:  # 30%以上が低スコア
            recommendations.append("全体的にタイトルとサムネイルの見直しを行い、クリック率向上を図る")
        
        # テーマ戦略提案
        if theme_performance:
            best_theme = list(theme_performance.keys())[0]
            recommendations.append(f"高パフォーマンステーマ「{best_theme}」の動画を増やす")
            
            if len(theme_performance) < 3:
                recommendations.append("テーマの多様性を増やして新しい視聴者層を開拓する")
        
        # エンゲージメント向上提案
        avg_comments = statistics.mean([
            v.get('latest_stats', {}).get('comments', 0) for v in scored_videos
        ])
        if avg_comments < 2:
            recommendations.append("動画内で視聴者との対話を促進する仕組みを導入する")
        
        return recommendations[:3]