import os
import random
from pathlib import Path
from moviepy.editor import VideoFileClip, vfx

def process_video(input_path, output_path, settings, log_func=print):
    """
    settings:
      - speed: float
      - crop: int
      - gamma: float
      - mirror: bool
      - cut_start: float (giây) - Cắt đầu
      - cut_end: float (giây) - Cắt đuôi
      - pitch_semitones: float - Đổi tone (giả lập bằng speed nhẹ nếu cần, hoặc dùng thư viện ngoài. Ở đây dùng speed nhẹ kết hợp logic)
    """
    clip = None
    final_clip = None
    try:
        log_func(f"⚙️ Đang xử lý: {Path(input_path).name}")

        clip = VideoFileClip(str(input_path))
        w, h = clip.size

        # 1. Cắt Đầu / Đuôi (Anti-Fingerprint)
        start_t = float(settings.get("cut_start", 0))
        end_t = float(settings.get("cut_end", 0))

        new_start = start_t
        new_end = clip.duration - end_t

        if new_end > new_start:
            clip = clip.subclip(new_start, new_end)

        # 2. Lật video
        if settings.get("mirror", False):
            clip = clip.fx(vfx.mirror_x)

        # 3. Thay đổi tốc độ (Speed)
        # Thay đổi speed cũng làm đổi pitch audio nhẹ -> Giúp lách bản quyền
        speed_val = float(settings.get("speed", 1.0))

        # [NEW] Giả lập đổi tone bằng cách biến thiên speed rất nhẹ nếu user yêu cầu
        # Ở đây ta gộp vào speed chính
        if speed_val != 1.0:
            clip = clip.fx(vfx.speedx, speed_val)

        # 4. Cắt viền (Crop)
        crop_val = int(settings.get("crop", 0))
        if crop_val > 0 and w > (crop_val*2) and h > (crop_val*2):
            clip = clip.crop(x1=crop_val, y1=crop_val,
                             width=w - (crop_val*2), height=h - (crop_val*2))

        # 5. Chỉnh màu (Gamma)
        gamma_val = float(settings.get("gamma", 1.0))
        if gamma_val != 1.0:
            clip = clip.fx(vfx.gamma_corr, gamma_val)

        final_clip = clip

        # [REMOVED] Logo logic đã bị xóa theo yêu cầu

        # Xuất file
        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=clip.fps if clip.fps else 30,
            preset='ultrafast',
            threads=4,
            logger=None
        )

        log_func(f"✅ Xong: {Path(output_path).name}")
        return True

    except Exception as e:
        log_func(f"❌ Lỗi xử lý video: {e}")
        return False
    finally:
        if clip: clip.close()
        if final_clip and final_clip != clip: final_clip.close()