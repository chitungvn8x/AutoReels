import requests
import json
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
import utils

def count_posts_on_date(cat, sub_cat, target_date_str):
    paths = utils.get_paths(cat, sub_cat)
    if not paths["history_up"].exists(): return 0
    count = 0
    with paths["history_up"].open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 3:
                date_part = parts[2].strip().split(' ')[0]
                if date_part == target_date_str: count += 1
    return count

def _api_upload(path, caption, time_pub, page_id, token):
    try:
        base = "https://graph.facebook.com/v21.0"
        r = requests.post(f"{base}/{page_id}/video_reels", params={"upload_phase":"start", "access_token":token})
        if r.status_code!=200: return False, r.text
        d = r.json(); vid_id, up_url = d.get("video_id"), d.get("upload_url")
        with open(path, "rb") as f:
            requests.post(up_url, headers={"Authorization":f"OAuth {token}", "offset":"0", "file_size":str(path.stat().st_size)}, data=f)
        p = {"access_token":token, "video_id":vid_id, "upload_phase":"finish", "description":caption, "video_state":"PUBLISHED"}
        if time_pub:
            p["video_state"] = "SCHEDULED"
            p["scheduled_publish_time"] = int(time_pub.timestamp())
        rf = requests.post(f"{base}/{page_id}/video_reels", params=p)
        resp = rf.json()
        if resp.get("success"): return True, "OK"
        return False, json.dumps(resp)
    except Exception as e: return False, str(e)

def run(settings, specific_times, target_files, cat, sub_cat, config_data, stop_check_func, log_func):
    paths = utils.get_paths(cat, sub_cat)
    page_id = config_data.get("page_id", "").strip()
    token = config_data.get("access_token", "").strip()
    if not page_id or not token: log_func("Thiếu Page ID/Token"); return

    log_func(f"Bắt đầu Upload {len(target_files)} video...")
    captions = config_data.get("captions", []) or ["Video hay"]
    hashtags = config_data.get("hashtags", []) or ["#reels"]
    aff_links = config_data.get("affiliate_links", []) or ["https://shopee.vn"]
    fomo_list = config_data.get("fomo_titles", []) or ["🔥 Xem ngay!"]
    schedule_list = specific_times if specific_times else []

    for i, video_path_str in enumerate(target_files):
        stop_check_func()
        video_path = Path(video_path_str)
        if not video_path.exists(): continue

        final_cap = f"{random.choice(fomo_list)}\n\n{random.choice(captions)}\n\n👉 {random.choice(aff_links)}\n\n{' '.join(random.sample(hashtags, min(10, len(hashtags))))}"
        pub_time = schedule_list[i] if (schedule_list and i < len(schedule_list)) else None
        
        if pub_time:
            now = datetime.now()
            if (pub_time - now).total_seconds() < 900:
                log_func(f"⚠️ Giờ đăng {pub_time.strftime('%H:%M')} quá gần. Đã +20p.")
                pub_time = now + timedelta(minutes=20)

        log_func(f"Upload: {video_path.name}")
        success, api_msg = _api_upload(video_path, final_cap, pub_time, page_id, token)
        
        if success:
            log_func("   ✅ Thành công")
            st_str = "SCHEDULED" if pub_time else "PUBLISHED"
            tm_str = pub_time.strftime("%d/%m %H:%M") if pub_time else datetime.now().strftime("%d/%m %H:%M")
            with paths["history_up"].open("a", encoding="utf-8") as f:
                f.write(f"{str(video_path)}|{st_str}|{tm_str}\n")
            if not pub_time and i < len(target_files)-1: 
                time.sleep(int(settings.get("upload_delay_minutes", 5)) * 60)
        else:
            log_func(f"   ❌ Thất bại: {api_msg}")