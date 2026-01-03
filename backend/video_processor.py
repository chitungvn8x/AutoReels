import os
import random
from pathlib import Path
from moviepy.editor import VideoFileClip, vfx, ImageClip, CompositeVideoClip

def process_video(input_path, output_path, settings, log_func=print):
    """
    settings:
      - speed, crop, gamma, mirror
      - logo_path: đường dẫn file ảnh
      - logo_size: float (0.1 -> 0.5) tỷ lệ so với chiều rộng video
      - logo_pos: 'tl', 'tr', 'bl', 'br' (Top-Left, Top-Right...)
    """
    clip = None
    final_clip = None
    try:
        log_func(f"⚙️ Đang xử lý: {Path(input_path).name}")
        
        clip = VideoFileClip(str(input_path))
        w, h = clip.size

        # 1. Lật video
        if settings.get("mirror", False):
            clip = clip.fx(vfx.mirror_x)

        # 2. Thay đổi tốc độ
        speed_val = float(settings.get("speed", 1.0))
        if speed_val != 1.0:
            clip = clip.fx(vfx.speedx, speed_val)

        # 3. Cắt viền
        crop_val = int(settings.get("crop", 0))
        if crop_val > 0 and w > (crop_val*2) and h > (crop_val*2):
            clip = clip.crop(x1=crop_val, y1=crop_val, 
                             width=w - (crop_val*2), height=h - (crop_val*2))

        # 4. Chỉnh màu
        gamma_val = float(settings.get("gamma", 1.0))
        if gamma_val != 1.0:
            clip = clip.fx(vfx.gamma_corr, gamma_val)
            
        final_clip = clip

        # 5. Chèn Logo (NẾU CÓ)
        logo_path = settings.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            try:
                logo_size_ratio = float(settings.get("logo_size", 0.15)) # Mặc định 15% width
                logo_pos_code = settings.get("logo_pos", "tr") # Mặc định Top-Right
                
                logo = ImageClip(logo_path)
                
                # Resize logo
                new_w = w * logo_size_ratio
                logo = logo.resize(width=new_w)
                
                # Padding lề
                margin = 20
                pos_map = {
                    "tl": (margin, margin),
                    "tr": (w - new_w - margin, margin),
                    "bl": (margin, h - logo.h - margin),
                    "br": (w - new_w - margin, h - logo.h - margin)
                }
                pos = pos_map.get(logo_pos_code, ("right", "top"))
                
                logo = logo.set_position(pos).set_duration(clip.duration)
                
                # Ghép logo vào video
                final_clip = CompositeVideoClip([clip, logo])
            except Exception as e:
                log_func(f"⚠️ Lỗi chèn logo: {e}")

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
        # Close clip để giải phóng RAM
        if clip: clip.close()
        if final_clip and final_clip != clip: final_clip.close()