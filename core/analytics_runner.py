# analytics_runner.py
"""
分析と計画を実行するためのランナースクリプト
"""
import os
import sys
import logging
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analytics_planner import AnalyticsPlanner
from handlers.g_sheet_handler import get_sheet, get_all_videos_for_report
from utils.utils import get_unique_log_filename

def setup_logging():
    """ロギングの設定"""
    log_file_path = get_unique_log_filename("analytics")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_comprehensive_analysis():
    """包括的分析を実行"""
    logger = setup_logging()
    logger.info("=== 包括的チャンネル分析開始 ===")
    
    try:
        # スプレッドシートから動画データを取得
        sheet = get_sheet()
        if not sheet:
            logger.error("スプレッドシートに接続できませんでした")
            return
            
        videos_data = get_all_videos_for_report(sheet)
        if not videos_data:
            logger.error("分析対象の動画データが見つかりませんでした")
            return
            
        logger.info(f"分析対象動画数: {len(videos_data)}本")
        
        # 分析実行
        planner = AnalyticsPlanner()
        comprehensive_report = planner.create_comprehensive_analysis_report(videos_data)
        
        # 結果を出力
        print_analysis_report(comprehensive_report, logger)
        
        # 分析結果を保存
        save_analysis_report(comprehensive_report, logger)
        
        logger.info("=== 包括的チャンネル分析完了 ===")
        
    except Exception as e:
        logger.error(f"分析実行中にエラーが発生: {e}")
        import traceback
        logger.error(traceback.format_exc())

def print_analysis_report(report: dict, logger):
    """分析レポートをコンソールに出力"""
    logger.info("\n" + "="*50)
    logger.info("📊 チャンネル分析レポート")
    logger.info("="*50)
    
    # チャンネルサマリー
    summary = report.get('channel_summary', {})
    if summary:
        logger.info(f"\n🎯 チャンネル概要:")
        logger.info(f"  総動画数: {summary.get('total_videos', 0)}本")
        logger.info(f"  総再生数: {summary.get('total_views', 0):,}回")
        logger.info(f"  平均再生数: {summary.get('average_views_per_video', 0):,.0f}回/本")
        logger.info(f"  全体エンゲージメント率: {summary.get('overall_engagement_rate', 0):.2f}%")
        logger.info(f"  投稿頻度: {summary.get('upload_frequency_per_week', 0):.1f}本/週")
    
    # トレンド分析
    trend = report.get('trend_analysis', {})
    if trend and 'error' not in trend:
        logger.info(f"\n📈 パフォーマンストレンド:")
        logger.info(f"  ステータス: {trend.get('trend_status', '不明')}")
        logger.info(f"  再生数トレンド: {trend.get('views_trend_percentage', 0):+.1f}%")
        logger.info(f"  エンゲージメントトレンド: {trend.get('engagement_trend_percentage', 0):+.2f}%")
    
    # 競合ポジション
    competitive = report.get('competitive_positioning', {})
    if competitive and 'error' not in competitive:
        logger.info(f"\n🏆 パフォーマンス分布:")
        counts = competitive.get('category_counts', {})
        logger.info(f"  エリート動画: {counts.get('elite', 0)}本")
        logger.info(f"  好調動画: {counts.get('good', 0)}本")
        logger.info(f"  平均的動画: {counts.get('average', 0)}本")
        logger.info(f"  要改善動画: {counts.get('underperforming', 0)}本")
        
        elite_titles = competitive.get('elite_video_titles', [])
        if elite_titles:
            logger.info(f"  トップパフォーマンス動画: {', '.join(elite_titles[:2])}")
    
    # コンテンツ戦略
    content_strategy = report.get('content_strategy', {})
    if content_strategy and 'error' not in content_strategy:
        focus_themes = content_strategy.get('recommended_focus_themes', [])
        if focus_themes:
            logger.info(f"\n🎨 推奨フォーカステーマ:")
            for theme in focus_themes[:3]:
                logger.info(f"  • {theme}")
    
    # 改善計画
    plans = report.get('improvement_plans', [])
    if plans:
        logger.info(f"\n📋 改善計画:")
        for i, plan in enumerate(plans[:5], 1):
            logger.info(f"  {i}. [{plan.get('priority', '中')}] {plan.get('action', '')}")
            logger.info(f"     期待効果: {plan.get('expected_outcome', '')}")
            logger.info(f"     実施時期: {plan.get('timeline', '')}")
    
    # 次回動画推奨
    recommendations = report.get('next_video_recommendations', [])
    if recommendations:
        logger.info(f"\n🎬 次回動画推奨事項:")
        for rec in recommendations[:3]:
            logger.info(f"  • {rec.get('type', '')}: {rec.get('recommendation', '')}")

def save_analysis_report(report: dict, logger):
    """分析レポートをファイルに保存"""
    try:
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析レポートを保存しました: {filename}")
        
    except Exception as e:
        logger.error(f"分析レポートの保存に失敗: {e}")

if __name__ == "__main__":
    run_comprehensive_analysis()