# video_generator_horizontal.py
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from moviepy.editor import *
import moviepy.audio.fx.all as afx
import os
import textwrap
import random

# --- 1. ヘルパー関数 ---

def create_text_image_horizontal(text, font_path, font_size, font_color, size, bg_color=(0,0,0,0), 
                      stroke_width=0, stroke_color="black", text_align="center",
                      fit_to_size=False):
    """
    横型動画用のテキスト画像生成関数
    """
    img = Image.new("RGBA", size, bg_color)
    draw = ImageDraw.Draw(img)
    
    font = ImageFont.truetype(font_path, font_size)

    # 横型用のテキスト調整
    char_per_line = int(size[0] / (font_size * 0.65)) if font_size > 0 and fit_to_size else 20
    wrapped_text = "\n".join(textwrap.wrap(text, width=char_per_line, break_long_words=True))

    # 自動フォントサイズ調整
    if fit_to_size:
        current_font_size = font_size
        while current_font_size > 10:
            font = ImageFont.truetype(font_path, current_font_size)
            if hasattr(draw, "multiline_textbbox"):
                bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=10)
            else:
                w, h = draw.multiline_textsize(wrapped_text, font=font, spacing=10)
                bbox = (0, 0, w, h)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            if text_width < size[0] and text_height < size[1]:
                break
            current_font_size -= 5
        font = ImageFont.truetype(font_path, current_font_size)
    
    # 最終的な描画
    pos = (size[0]/2, size[1]/2)
    anchor = "mm" if text_align == "center" else "la"
    if stroke_width > 0:
        draw.multiline_text(pos, wrapped_text, font=font, fill=stroke_color, stroke_width=stroke_width, anchor=anchor, spacing=15, align=text_align)
    draw.multiline_text(pos, wrapped_text, font=font, fill=font_color, anchor=anchor, spacing=15, align=text_align)

    return np.array(img)

def create_timer_bar_horizontal(duration, size, color, pos):
    """横型用タイマーバー"""
    bar = ColorClip(size=size, color=color, duration=duration)
    bar_fx = bar.fx(vfx.resize, newsize=lambda t: (max(1, size[0] * (1 - t / duration)), size[1]))
    return bar_fx.set_position(pos)

def create_question_counter_horizontal(current, total, size):
    """横型用の問題カウンター表示"""
    counter_text = f"問題 {current} / {total}"
    return create_text_image_horizontal(
        text=counter_text, 
        font_path=r"C:/Windows/Fonts/meiryob.ttc", 
        font_size=40, 
        font_color="white", 
        size=size, 
        stroke_width=3, 
        stroke_color="black"
    )

# --- 2. 横型耐久クイズ動画生成ロジック ---
def create_horizontal_endurance_quiz(quiz_data, base_filename, output_path):
    """10分横型耐久漢字クイズ動画を生成する"""
    print("INFO: 横型耐久漢字クイズ動画の生成を開始...")
    SCREEN_SIZE = (1920, 1080)  # 横型フォーマット
    FONT_BOLD = r"C:/Windows/Fonts/meiryob.ttc"
    FONT_REGULAR = r"C:/Windows/Fonts/meiryo.ttc"
    
    num_questions = len(quiz_data.get("quiz_data", []))
    THINKING_TIME = 4.0  # 耐久でも十分な考慮時間を確保
    ANSWER_TIME = 3.0    # 解答と解説時間を十分に確保
    
    BASE_DIR = Path(__file__).parent.parent
    IMAGE_DIR = BASE_DIR / "image"
    BGM_DIR = BASE_DIR / "bgm"
    SE_DIR = BASE_DIR / "se"
    VOICE_DIR = BASE_DIR / "voice"
    
    try:
        # 背景画像を横型用にリサイズ
        image_files = list(IMAGE_DIR.glob("*.jpg")) + list(IMAGE_DIR.glob("*.png"))
        if not image_files: raise FileNotFoundError("背景画像がimageフォルダに見つかりません。")
        bg_image_base = ImageClip(str(random.choice(image_files)))
        
        # 横型用の白板サイズ
        whiteboard_image = ColorClip(size=(1600, 800), color=(255, 255, 255)).set_opacity(0.85)
        
        bgm_files = list(BGM_DIR.glob("*.mp3")) + list(BGM_DIR.glob("*.wav"))
        bgm_files = [f for f in bgm_files if f.name != "dummy_bgm.mp3"]
        if not bgm_files: raise FileNotFoundError("BGMがbgmフォルダに見つかりません。")
        selected_bgm_path = random.choice(bgm_files)
        print(f"INFO: Selected BGM -> {selected_bgm_path.name}")
        bgm = AudioFileClip(str(selected_bgm_path)).volumex(0.03)  # 耐久なのでBGMはさらに小さく

        se_question = AudioFileClip(str(SE_DIR / "question.mp3")).volumex(0.7)
        se_correct = AudioFileClip(str(SE_DIR / "correct.mp3")).volumex(0.7)
        se_tick = AudioFileClip(str(SE_DIR / "tick.mp3")).volumex(0.3)
    except Exception as e:
        print(f"❌エラー: アセットファイルの読み込みに失敗: {e}")
        return

    all_video_clips, all_audio_clips = [], []
    current_time = 0
    
    def resize_bg_horizontal(clip, duration):
        return clip.set_duration(duration).fx(vfx.resize, newsize=SCREEN_SIZE)

    # オープニング (短縮版)
    OPENING_DURATION = 2.0
    opening_title = f"漢字耐久クイズ - {num_questions}問連続チャレンジ！"
    title_img = create_text_image_horizontal(
        text=opening_title, 
        font_path=FONT_BOLD, 
        font_size=80, 
        font_color="red", 
        size=(1500, 200), 
        stroke_width=5, 
        stroke_color="white", 
        fit_to_size=True
    )
    subtitle_img = create_text_image_horizontal(
        text="集中力と知識力の限界に挑戦！", 
        font_path=FONT_BOLD, 
        font_size=50, 
        font_color="black", 
        size=(1500, 100), 
        stroke_width=3, 
        stroke_color="white"
    )
    
    opening_scene = CompositeVideoClip([
        resize_bg_horizontal(bg_image_base, OPENING_DURATION),
        whiteboard_image.set_position("center"),
        ImageClip(title_img).set_position(("center", 350)),
        ImageClip(subtitle_img).set_position(("center", 550))
    ]).set_duration(OPENING_DURATION)
    all_video_clips.append(opening_scene.set_start(current_time))
    current_time += OPENING_DURATION

    # メインクイズループ
    for i, quiz in enumerate(quiz_data.get("quiz_data", [])):
        q_num = i + 1
        
        # 問題カウンター
        counter_img = create_question_counter_horizontal(q_num, num_questions, (200, 60))
        
        # ナレーション音声の処理（耐久版でも完全な音声を使用）
        q_narration_path = str(VOICE_DIR / f"{base_filename}_q{q_num}_before.wav")
        if os.path.exists(q_narration_path):
            q_narration_audio = AudioFileClip(q_narration_path).volumex(1.2)
            q_narration_duration = q_narration_audio.duration
            all_audio_clips.append(q_narration_audio.set_start(current_time))
        else:
            q_narration_duration = 2.0  # デフォルト時間
        
        # 問題提示シーン (簡略化)
        q_header_text = f"第 {q_num} 問"
        q_header_img = create_text_image_horizontal(
            text=q_header_text, 
            font_path=FONT_REGULAR, 
            font_size=50, 
            font_color="blue", 
            size=(300, 80)
        )
        
        question_narration_scene = CompositeVideoClip([
            resize_bg_horizontal(bg_image_base, q_narration_duration),
            whiteboard_image.set_position("center"),
            ImageClip(counter_img).set_position((180, 80)),
            ImageClip(q_header_img).set_position(("center", 300))
        ]).set_duration(q_narration_duration)
        all_video_clips.append(question_narration_scene.set_start(current_time))
        current_time += q_narration_duration
        
        # シンキングタイム (メイン問題表示)
        question_kanji_img = create_text_image_horizontal(
            text=quiz['kanji'], 
            font_path=FONT_BOLD, 
            font_size=300, 
            font_color="black", 
            size=(800, 400), 
            fit_to_size=True
        )
        timer_bar = create_timer_bar_horizontal(THINKING_TIME, size=(600, 15), color=(255, 100, 100), pos=('center', 800))
        
        thinking_scene = CompositeVideoClip([
            resize_bg_horizontal(bg_image_base, THINKING_TIME),
            whiteboard_image.set_position("center"),
            ImageClip(counter_img).set_position((180, 80)),
            ImageClip(question_kanji_img).set_position("center"),
            timer_bar
        ]).set_duration(THINKING_TIME)
        all_video_clips.append(thinking_scene.set_start(current_time))
        
        if se_question: all_audio_clips.append(se_question.set_start(current_time))
        # カウントダウン効果音のタイミングを正確に配置
        for t_se in range(int(THINKING_TIME)):
            if se_tick: all_audio_clips.append(se_tick.set_start(current_time + t_se))
        current_time += THINKING_TIME
        
        # 解答発表（完全版）
        a_narration_path = str(VOICE_DIR / f"{base_filename}_q{q_num}_after.wav")
        if os.path.exists(a_narration_path):
            a_narration_audio = AudioFileClip(a_narration_path).volumex(1.2)
            a_narration_duration = a_narration_audio.duration
            all_audio_clips.append(a_narration_audio.set_start(current_time))
        else:
            a_narration_duration = ANSWER_TIME

        answer_text = f"{quiz.get('yomi', '')}"
        answer_text_img = create_text_image_horizontal(
            text=answer_text, 
            font_path=FONT_BOLD, 
            font_size=120, 
            font_color="red", 
            size=(600, 150), 
            fit_to_size=True,
            stroke_width=3,
            stroke_color="white"
        )
        
        answer_scene = CompositeVideoClip([
            resize_bg_horizontal(bg_image_base, a_narration_duration),
            whiteboard_image.set_position("center"),
            ImageClip(counter_img).set_position((180, 80)),
            ImageClip(question_kanji_img).set_position(("center", 300)),
            ImageClip(answer_text_img).set_position(("center", 600))
        ]).set_duration(a_narration_duration)
        all_video_clips.append(answer_scene.set_start(current_time))
        if se_correct: all_audio_clips.append(se_correct.set_start(current_time))
        current_time += a_narration_duration

    # エンディング
    outro_narration_path = str(VOICE_DIR / f"{base_filename}_outro.wav")
    if os.path.exists(outro_narration_path):
        outro_narration_audio = AudioFileClip(outro_narration_path).volumex(1.0)
        outro_duration = outro_narration_audio.duration
        all_audio_clips.append(outro_narration_audio.set_start(current_time))
    else:
        outro_duration = 3.0

    outro_text = f"お疲れさまでした！\n{num_questions}問すべて完走できましたか？"
    ending_text_img = create_text_image_horizontal(
        text=outro_text, 
        font_path=FONT_BOLD, 
        font_size=70, 
        font_color="blue", 
        size=(1400, 300), 
        fit_to_size=True,
        stroke_width=4,
        stroke_color="white"
    )
    
    ending_scene = CompositeVideoClip([
        resize_bg_horizontal(bg_image_base, outro_duration), 
        whiteboard_image.set_position("center"), 
        ImageClip(ending_text_img).set_position("center")
    ]).set_duration(outro_duration)
    all_video_clips.append(ending_scene.set_start(current_time))
    current_time += outro_duration

    # 最終的な結合とオーディオ設定
    try:
        print(f"INFO: 横型動画クリップ数: {len(all_video_clips)}, 音声クリップ数: {len(all_audio_clips)}")
        print(f"INFO: 総動画時間: {current_time:.1f}秒 ({current_time/60:.1f}分)")
        
        final_clip = CompositeVideoClip(all_video_clips, size=SCREEN_SIZE).set_duration(current_time)
        print(f"INFO: 横型動画クリップ合成完了")
        
        if all_audio_clips:
            looped_bgm = bgm.fx(afx.audio_loop, duration=final_clip.duration)
            final_audio = CompositeAudioClip([looped_bgm] + all_audio_clips)
            final_clip = final_clip.set_audio(final_audio)
            print(f"INFO: 音声クリップ合成完了")
        else:
            print("WARNING: 音声クリップが見つかりません")
        
        print("INFO: 横型耐久動画を書き出しています...")
        final_clip.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", verbose=True, temp_audiofile="temp-audio-horizontal.m4a")
        
        # 生成されたファイルサイズを確認
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"INFO: 横型耐久動画生成完了: {output_path} ({file_size:,} bytes)")
        else:
            print(f"ERROR: 横型動画ファイルが生成されませんでした: {output_path}")
            
    except Exception as e:
        print(f"ERROR: 横型動画生成中にエラー発生: {e}")
        import traceback
        traceback.print_exc()