# season_utils.py
"""
季節判定とテーマ提案のユーティリティ
"""

import datetime
from typing import Dict, List, Tuple

def get_current_season() -> Tuple[str, str, List[str]]:
    """
    現在の季節を判定し、季節名、説明、おすすめテーマを返す
    
    Returns:
        Tuple[季節名, 季節説明, おすすめテーマリスト]
    """
    now = datetime.datetime.now()
    month = now.month
    day = now.day
    
    # 日本の季節区分（二十四節気を簡略化）
    if month == 3 and day >= 20 or month in [4, 5] or month == 6 and day < 21:
        season = "春"
        description = "新緑の季節、桜や花々が美しい時期"
        themes = [
            "春の花（桜、桃、菜の花など）",
            "新緑・若葉",
            "春野菜（筍、蕨、土筆など）", 
            "卒業・入学",
            "暖かい春の虫",
            "春告魚（魚へん）"
        ]
    elif month == 6 and day >= 21 or month in [7, 8] or month == 9 and day < 23:
        season = "夏"
        description = "暑い夏、活動的な季節"
        themes = [
            "夏の花（向日葵、朝顔、蓮など）",
            "夏野菜（胡瓜、茄子、西瓜など）",
            "夏祭り・花火",
            "海の生き物（魚へん夏編）",
            "夏の虫（蝉、蛍など）",
            "冷たい食べ物（氷、冷菓など）"
        ]
    elif month == 9 and day >= 23 or month in [10, 11] or month == 12 and day < 22:
        season = "秋"  
        description = "実りの秋、紅葉が美しい季節"
        themes = [
            "秋の花（菊、桔梗、萩など）",
            "紅葉・落葉",
            "秋の味覚（柿、栗、茸など）",
            "秋の虫（鈴虫、蟋蟀など）",
            "収穫・実り",
            "読書・芸術"
        ]
    else:  # 12/22以降または1,2月
        season = "冬"
        description = "寒い冬、静寂と美しさの季節"  
        themes = [
            "冬の花（椿、梅、水仙など）",
            "雪・氷",
            "冬野菜（大根、白菜、蕪など）",
            "年末年始・正月",
            "温かい食べ物（鍋、汁物など）",
            "冬の魚（鰤、鱈、鰰など）"
        ]
    
    return season, description, themes

def get_seasonal_context() -> str:
    """
    現在の季節に応じたコンテキスト文を生成
    AIプロンプトに挿入する用
    """
    season, description, themes = get_current_season()
    now = datetime.datetime.now()
    
    context = f"""
【現在の季節情報】
- 現在: {now.month}月{now.day}日 ({season})
- 季節特徴: {description}
- この時期におすすめの漢字テーマ例:
  {', '.join(themes[:3])}など

※季節感を取り入れる場合は、視聴者が「今の時期にぴったり！」と感じるテーマを選んでください。
※ただし、季節に関係ないテーマ（地名、職業、動物一般など）も効果的です。バランスを考慮してください。
"""
    return context

def is_theme_seasonal_appropriate(theme: str) -> Tuple[bool, str]:
    """
    指定されたテーマが現在の季節に適しているかチェック
    
    Args:
        theme: チェックするテーマ名
        
    Returns:
        Tuple[適切かどうか, 理由/コメント]
    """
    current_season, _, current_themes = get_current_season()
    theme_lower = theme.lower()
    
    # 季節キーワードマッピング
    season_keywords = {
        "春": ["春", "桜", "花", "新緑", "若葉", "入学", "卒業"],
        "夏": ["夏", "暑", "海", "祭", "花火", "蝉", "蛍", "氷"],
        "秋": ["秋", "紅葉", "落葉", "収穫", "実り", "柿", "栗", "茸"],
        "冬": ["冬", "雪", "氷", "寒", "正月", "年末", "鍋", "梅"]
    }
    
    # 現在の季節のキーワードが含まれているかチェック
    current_keywords = season_keywords[current_season]
    for keyword in current_keywords:
        if keyword in theme:
            return True, f"現在の季節（{current_season}）にぴったりのテーマです"
    
    # 他の季節のキーワードが含まれているかチェック
    for season, keywords in season_keywords.items():
        if season != current_season:
            for keyword in keywords:
                if keyword in theme:
                    return False, f"{season}のテーマなので、現在の季節（{current_season}）には少し早い/遅いかもしれません"
    
    # 季節に関係ないテーマの場合
    return True, "季節に関係ないテーマなので、いつでも適切です"

if __name__ == "__main__":
    # テスト実行
    season, desc, themes = get_current_season()
    print(f"現在の季節: {season}")
    print(f"説明: {desc}")
    print(f"おすすめテーマ: {themes}")
    print("\n" + get_seasonal_context())
    
    # テーマチェックテスト
    test_themes = ["春の花", "夏祭り", "秋の虫", "冬の味覚", "魚へん", "地名"]
    for theme in test_themes:
        appropriate, reason = is_theme_seasonal_appropriate(theme)
        print(f"{theme}: {'✓' if appropriate else '⚠'} {reason}")