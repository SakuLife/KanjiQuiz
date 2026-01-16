# video_generator.py
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from moviepy.editor import *
import moviepy.audio.fx.all as afx
import os
import textwrap
import random

# --- 1. ヘルパー関数 ---

def create_text_image(text, font_path, font_size, font_color, size, bg_color=(0,0,0,0),
                      stroke_width=0, stroke_color="black", text_align="center",
                      fit_to_size=False, max_chars_per_line=None):
    """
    Pillowを使って、指定された領域にテキスト画像を生成する関数。
    自動フォントサイズ調整、自動折り返し機能付き。
    max_chars_per_line: 1行あたりの最大文字数（日本語向け、指定時に優先）
    """
    img = Image.new("RGBA", size, bg_color)
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(font_path, font_size)

    # テキストの自動折り返し処理（日本語対応）
    if max_chars_per_line:
        # 明示的に指定された場合はその値を使用
        char_per_line = max_chars_per_line
    elif fit_to_size and font_size > 0:
        char_per_line = int(size[0] / (font_size * 0.65))
    else:
        char_per_line = 15
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

def create_timer_bar(duration, size, color, pos):
    """時間経過で縮むタイマーバーを生成する関数"""
    bar = ColorClip(size=size, color=color, duration=duration)
    bar_fx = bar.fx(vfx.resize, newsize=lambda t: (max(1, size[0] * (1 - t / duration)), size[1]))
    return bar_fx.set_position(pos)

# --- 2. メインの動画生成ロジック ---
def create_thumbnail(quiz_data, base_filename, output_path):
    """サムネイル用画像を生成する（回答をネタバレしない）"""
    print("INFO: サムネイル画像の生成を開始...")
    SCREEN_SIZE = (1280, 720)  # YouTubeサムネイル推奨サイズ

    # フォントパスの設定（OSに応じて切り替え）
    if os.environ.get('GITHUB_ACTIONS_MODE') == 'true':
        # GitHub Actions (Linux)用フォント
        FONT_BOLD = os.environ.get('FONT_PATH_BOLD', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
        FONT_REGULAR = os.environ.get('FONT_PATH_REGULAR', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    else:
        # Windows用フォント
        FONT_BOLD = r"C:/Windows/Fonts/meiryob.ttc"
        FONT_REGULAR = r"C:/Windows/Fonts/meiryo.ttc"

    BASE_DIR = Path(__file__).parent.parent
    IMAGE_DIR = BASE_DIR / "image"

    try:
        # 背景画像の選択
        image_files = list(IMAGE_DIR.glob("*.jpg")) + list(IMAGE_DIR.glob("*.png"))
        if not image_files:
            raise FileNotFoundError("背景画像がimageフォルダに見つかりません。")
        bg_image_path = str(random.choice(image_files))

        # PIL で画像生成
        bg_img = Image.open(bg_image_path).resize(SCREEN_SIZE)

        # 半透明の白背景を重ねる
        overlay = Image.new("RGBA", SCREEN_SIZE, (255, 255, 255, 200))
        bg_img = bg_img.convert("RGBA")
        bg_img = Image.alpha_composite(bg_img, overlay)

        draw = ImageDraw.Draw(bg_img)

        # タイトルテキスト
        title = quiz_data.get("theme", "難読漢字クイズ")
        try:
            title_font = ImageFont.truetype(FONT_BOLD, 80)
        except:
            title_font = ImageFont.load_default()

        # 問題数テキスト
        num_questions = len(quiz_data.get("quiz_data", []))
        subtitle = f"全{num_questions}問にチャレンジ！"
        try:
            subtitle_font = ImageFont.truetype(FONT_REGULAR, 50)
        except:
            subtitle_font = ImageFont.load_default()

        # 最初の漢字を取得（1問目をサムネイルに使用）
        first_kanji = ""
        if quiz_data.get("quiz_data"):
            first_kanji = quiz_data["quiz_data"][0].get("kanji", "")

        # 漢字フォント
        try:
            kanji_font = ImageFont.truetype(FONT_BOLD, 200)
        except:
            kanji_font = ImageFont.load_default()

        # テキスト配置計算
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (SCREEN_SIZE[0] - title_width) // 2

        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (SCREEN_SIZE[0] - subtitle_width) // 2

        if first_kanji:
            kanji_bbox = draw.textbbox((0, 0), first_kanji, font=kanji_font)
            kanji_width = kanji_bbox[2] - kanji_bbox[0]
            kanji_x = (SCREEN_SIZE[0] - kanji_width) // 2

        # テキスト描画（縁取り付き）
        # タイトル
        for dx in [-3, -2, -1, 0, 1, 2, 3]:
            for dy in [-3, -2, -1, 0, 1, 2, 3]:
                if dx != 0 or dy != 0:
                    draw.text((title_x + dx, 50 + dy), title, font=title_font, fill="white")
        draw.text((title_x, 50), title, font=title_font, fill="black")

        # サブタイトル
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((subtitle_x + dx, 150 + dy), subtitle, font=subtitle_font, fill="white")
        draw.text((subtitle_x, 150), subtitle, font=subtitle_font, fill="blue")

        # 漢字（ネタバレしないように "？" マークと組み合わせ）
        if first_kanji:
            question_text = f"{first_kanji}\n？"
            # マルチライン対応
            lines = question_text.split("\n")
            y_offset = 300
            for line in lines:
                if line == "？":
                    # "？"マークは赤色で
                    line_bbox = draw.textbbox((0, 0), line, font=kanji_font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_x = (SCREEN_SIZE[0] - line_width) // 2

                    for dx in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
                        for dy in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
                            if dx != 0 or dy != 0:
                                draw.text((line_x + dx, y_offset + dy), line, font=kanji_font, fill="white")
                    draw.text((line_x, y_offset), line, font=kanji_font, fill="red")
                else:
                    # 漢字は黒色で
                    line_bbox = draw.textbbox((0, 0), line, font=kanji_font)
                    line_width = line_bbox[2] - line_bbox[0]
                    line_x = (SCREEN_SIZE[0] - line_width) // 2

                    for dx in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
                        for dy in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
                            if dx != 0 or dy != 0:
                                draw.text((line_x + dx, y_offset + dy), line, font=kanji_font, fill="white")
                    draw.text((line_x, y_offset), line, font=kanji_font, fill="black")

                y_offset += 220

        # サムネイル保存
        thumbnail_path = output_path.replace(".mp4", "_thumbnail.jpg")
        bg_img.convert("RGB").save(thumbnail_path, "JPEG", quality=95)
        print(f"INFO: サムネイル生成完了: {thumbnail_path}")
        return thumbnail_path

    except Exception as e:
        print(f"ERROR: サムネイル生成中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_advanced_quiz_video(quiz_data, base_filename, output_path):
    """改善案をすべて反映したクイズ動画を生成する"""
    print("INFO: クイズ動画の生成を開始...")
    SCREEN_SIZE = (1080, 1920)

    # フォントパスの設定（OSに応じて切り替え）
    if os.environ.get('GITHUB_ACTIONS_MODE') == 'true':
        # GitHub Actions (Linux)用フォント
        FONT_BOLD = os.environ.get('FONT_PATH_BOLD', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
        FONT_REGULAR = os.environ.get('FONT_PATH_REGULAR', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    else:
        # Windows用フォント
        FONT_BOLD = r"C:/Windows/Fonts/meiryob.ttc"
        FONT_REGULAR = r"C:/Windows/Fonts/meiryo.ttc"
    
    num_questions = len(quiz_data.get("quiz_data", []))
    THINKING_TIME = 3.0
    
    BASE_DIR = Path(__file__).parent.parent
    IMAGE_DIR = BASE_DIR / "image"
    BGM_DIR = BASE_DIR / "bgm"
    SE_DIR = BASE_DIR / "se"
    VOICE_DIR = BASE_DIR / "voice"
    
    try:
        image_files = list(IMAGE_DIR.glob("*.jpg")) + list(IMAGE_DIR.glob("*.png"))
        if not image_files: raise FileNotFoundError("背景画像がimageフォルダに見つかりません。")
        bg_image_base = ImageClip(str(random.choice(image_files)))
        
        whiteboard_image = ColorClip(size=(1000, 1000), color=(255, 255, 255)).set_opacity(0.8)
        
        bgm_files = list(BGM_DIR.glob("*.mp3")) + list(BGM_DIR.glob("*.wav"))
        # 破損したdummy_bgm.mp3を除外
        bgm_files = [f for f in bgm_files if f.name != "dummy_bgm.mp3"]
        if not bgm_files: raise FileNotFoundError("BGMがbgmフォルダに見つかりません。")
        selected_bgm_path = random.choice(bgm_files)
        print(f"INFO: Selected BGM -> {selected_bgm_path.name}")
        bgm = AudioFileClip(str(selected_bgm_path)).volumex(0.05) # BGMの音量をさらに下げる

        se_question = AudioFileClip(str(SE_DIR / "question.mp3"))
        se_correct = AudioFileClip(str(SE_DIR / "correct.mp3"))
        se_tick = AudioFileClip(str(SE_DIR / "tick.mp3")).volumex(0.5)
    except Exception as e:
        print(f"❌エラー: アセットファイルの読み込みに失敗: {e}")
        return

    all_video_clips, all_audio_clips = [], []
    current_time = 0
    
    def resize_bg(clip, duration):
        return clip.set_duration(duration).fx(vfx.resize, newsize=SCREEN_SIZE)

    OPENING_DURATION = 1.5
    opening_title = quiz_data.get("theme", "難読漢字クイズ")
    title_img = create_text_image(text=opening_title, font_path=FONT_BOLD, font_size=100, font_color="black", size=(950, 400), stroke_width=6, stroke_color="white", fit_to_size=True)
    subtitle_img = create_text_image(text=f"問題は全部で{num_questions}問", font_path=FONT_BOLD, font_size=55, font_color="black", size=(950, 120), stroke_width=4, stroke_color="white")
    
    opening_scene = CompositeVideoClip([
        resize_bg(bg_image_base, OPENING_DURATION),
        whiteboard_image.set_position("center"),
        ImageClip(title_img).set_position(("center", 550)),
        ImageClip(subtitle_img).set_position(("center", 950))
    ]).set_duration(OPENING_DURATION)
    all_video_clips.append(opening_scene.set_start(current_time))
    current_time += OPENING_DURATION

    for i, quiz in enumerate(quiz_data.get("quiz_data", [])):
        q_num = i + 1
        
        # --- ナレーションと映像の同期 ---
        q_narration_path = str(VOICE_DIR / f"{base_filename}_q{q_num}_before.wav")
        q_narration_audio = AudioFileClip(q_narration_path).volumex(1.2) if os.path.exists(q_narration_path) else None # ナレーションの音量を少し上げる
        q_narration_duration = q_narration_audio.duration if q_narration_audio else 0
        if q_narration_audio: all_audio_clips.append(q_narration_audio.set_start(current_time))
        
        # --- 改善点: 問題番号と「なんと読む？」を一枚の画像にまとめる ---
        q_header_text = f"【第 {q_num} / {num_questions} 問】\nこの漢字なんと読む？"
        q_header_img = create_text_image(text=q_header_text, font_path=FONT_REGULAR, font_size=60, font_color="black", size=(1000, 200))
        
        question_narration_scene = CompositeVideoClip([
            resize_bg(bg_image_base, q_narration_duration),
            whiteboard_image.set_position("center"),
            ImageClip(q_header_img).set_position(("center", 650))
        ]).set_duration(q_narration_duration)
        all_video_clips.append(question_narration_scene.set_start(current_time))
        current_time += q_narration_duration
        
        # --- シンキングタイム ---
        # 3文字以上の漢字でもはみ出さないよう、幅を狭くしてfit_to_sizeを有効化
        question_kanji_img = create_text_image(text=quiz['kanji'], font_path=FONT_BOLD, font_size=350, font_color="black", size=(950, 450), fit_to_size=True)
        timer_bar = create_timer_bar(THINKING_TIME, size=(800, 20), color=(50, 150, 255), pos=('center', 1300))
        
        thinking_scene = CompositeVideoClip([
            resize_bg(bg_image_base, THINKING_TIME), 
            whiteboard_image.set_position("center"), 
            ImageClip(question_kanji_img).set_position("center"),
            # ここではヘッダーを表示しないことで、漢字に集中させる
            timer_bar
        ]).set_duration(THINKING_TIME)
        all_video_clips.append(thinking_scene.set_start(current_time))
        
        if se_question: all_audio_clips.append(se_question.set_start(current_time))
        for t_se in range(int(THINKING_TIME)):
             if se_tick: all_audio_clips.append(se_tick.set_start(current_time + t_se))
        current_time += THINKING_TIME
        
        # --- 解答発表 ---
        a_narration_path = str(VOICE_DIR / f"{base_filename}_q{q_num}_after.wav")
        a_narration_audio = AudioFileClip(a_narration_path).volumex(1.2) if os.path.exists(a_narration_path) else None # ナレーションの音量を少し上げる
        a_narration_duration = a_narration_audio.duration if a_narration_audio else 2.5
        if a_narration_audio: all_audio_clips.append(a_narration_audio.set_start(current_time))

        answer_text = f"正解：{quiz.get('yomi', '')}"
        # 5文字以上の読みでもはみ出さないよう、幅を画面内に収める
        answer_text_img = create_text_image(text=answer_text, font_path=FONT_BOLD, font_size=120, font_color="red", size=(950, 200), fit_to_size=True)
        
        answer_scene = CompositeVideoClip([
            resize_bg(bg_image_base, a_narration_duration), 
            whiteboard_image.set_position("center"), 
            ImageClip(question_kanji_img).set_position("center"), 
            ImageClip(answer_text_img).set_position(("center", SCREEN_SIZE[1] / 4 + 50))
        ]).set_duration(a_narration_duration)
        all_video_clips.append(answer_scene.set_start(current_time))
        if se_correct: all_audio_clips.append(se_correct.set_start(current_time))
        current_time += a_narration_duration

    # --- シーン3: エンディング ---
    outro_narration_path = str(VOICE_DIR / f"{base_filename}_outro.wav")
    outro_narration_audio = AudioFileClip(outro_narration_path).volumex(1.2) if os.path.exists(outro_narration_path) else None # ナレーションの音量を少し上げる
    outro_duration = outro_narration_audio.duration if outro_narration_audio else 3.0
    if outro_narration_audio: all_audio_clips.append(outro_narration_audio.set_start(current_time))

    outro_text = quiz_data.get("outro_narration", "お疲れさまでした！")
    # 日本語の読みやすさを考慮して1行あたり12文字で改行
    ending_text_img = create_text_image(text=outro_text, font_path=FONT_BOLD, font_size=70, font_color="black", size=(950, 500), fit_to_size=True, max_chars_per_line=12)
    
    ending_scene = CompositeVideoClip([
        resize_bg(bg_image_base, outro_duration), 
        whiteboard_image.set_position("center"), 
        ImageClip(ending_text_img).set_position("center")
    ]).set_duration(outro_duration)
    all_video_clips.append(ending_scene.set_start(current_time))
    current_time += outro_duration

    # --- 最終的な結合とオーディオ設定 ---
    try:
        print(f"INFO: 動画クリップ数: {len(all_video_clips)}, 音声クリップ数: {len(all_audio_clips)}")
        print(f"INFO: 総動画時間: {current_time}秒")
        
        final_clip = CompositeVideoClip(all_video_clips, size=SCREEN_SIZE).set_duration(current_time)
        print(f"INFO: 動画クリップ合成完了")
        
        if all_audio_clips:
            looped_bgm = bgm.fx(afx.audio_loop, duration=final_clip.duration)
            final_audio = CompositeAudioClip([looped_bgm] + all_audio_clips)
            final_clip = final_clip.set_audio(final_audio)
            print(f"INFO: 音声クリップ合成完了")
        else:
            print("WARNING: 音声クリップが見つかりません")
        
        print("INFO: 動画を書き出しています...")
        final_clip.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", verbose=False, logger=None, temp_audiofile="temp-audio.m4a")

        # サムネイル生成
        thumbnail_path = create_thumbnail(quiz_data, base_filename, output_path)

        # 生成されたファイルサイズを確認
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"INFO: 動画生成完了: {output_path} ({file_size:,} bytes)")
            if thumbnail_path:
                print(f"INFO: サムネイル生成完了: {thumbnail_path}")
        else:
            print(f"ERROR: 動画ファイルが生成されませんでした: {output_path}")

        return thumbnail_path
            
    except Exception as e:
        print(f"ERROR: 動画生成中にエラー発生: {e}")
        import traceback
        traceback.print_exc()

