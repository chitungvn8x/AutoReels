from datetime import datetime
from backend import scraper, downloader, uploader, browser, video_processor
import utils
import os
from pathlib import Path
from moviepy.editor import VideoFileClip

class AutomationBackend:
    def __init__(self, settings, log_callback=None):
        self.settings = settings
        self.log_callback = log_callback
        self.stop_flag = False

    def log(self, msg):
        # [UPDATED] No icon
        full_msg = f"{msg}"
        if self.log_callback: self.log_callback(full_msg)
        else: print(full_msg)

    def check_stop(self):
        if self.stop_flag:
            self.log("ĐÃ DỪNG KHẨN CẤP!")
            raise Exception("UserStopped")

    def setup_tiktok_login(self): return browser.setup_driver(self.settings, "https://www.tiktok.com/login")

    # [FIX] Added missing method
    def check_api_token(self, page_id, token):
        return uploader.check_token_validity(page_id, token)

    def save_cookie_profile(self, driver, name):
        res = browser.save_cookie(driver, name)
        if res: self.log(f"Đã lưu cookie [{name}]")
        return res

    def run_tiktok_scraper(self, tags, num, cat, sub, profile):
        if profile: self.settings["current_tiktok_profile"] = profile
        scraper.run(self.settings, tags, num, cat, sub, self.check_stop, self.log)

    def get_video_duration(self, path):
        try:
            clip = VideoFileClip(str(path))
            dur = int(clip.duration)
            clip.close()
            mins = dur // 60
            secs = dur % 60
            return f"{mins:02d}:{secs:02d}"
        except: return "--:--"

    def get_download_list(self, cat, sub, mode):
        paths = utils.get_paths(cat, sub)
        history_links = set()
        if paths["history_dl"].exists():
            try:
                with paths["history_dl"].open("r", encoding="utf-8") as f:
                    for line in f: history_links.add(line.strip())
            except: pass

        if mode == "PENDING":
            if not paths["link_file"].exists(): return []
            results = []
            try:
                with paths["link_file"].open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        parts = line.split("|")
                        link = parts[0]
                        scan_time = parts[1] if len(parts) > 1 else ""
                        if link in history_links: continue

                        results.append({
                            "data": link, "status": "Chờ tải",
                            "scan_time": scan_time, "thumb": None,
                            "cat_sub": f"{cat} > {sub}"
                        })
            except: pass
            return results
        return []

    def get_original_videos(self, cat, sub):
        paths = utils.get_paths(cat, sub)
        if not paths["video_dir"].exists(): return []

        results = []
        files = [f for f in paths["video_dir"].glob("*.mp4") if f.is_file()]
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        edited_dir = paths["video_dir"] / "Edited"

        for f in files:
            thumb_path = paths["thumb_dir"] / (f.stem + ".jpg")
            is_edited = False
            edit_time = ""
            edit_params = ""

            if edited_dir.exists():
                for ed_f in edited_dir.glob(f"{f.stem}_ed*.mp4"):
                    is_edited = True
                    edit_time = datetime.fromtimestamp(ed_f.stat().st_mtime).strftime("%d/%m %H:%M")
                    edit_params = "Speed: 1.05x, Crop: 10px"
                    break

            status_text = f"ĐÃ CHỈNH SỬA: {edit_time}" if is_edited else "CHƯA CHỈNH SỬA"

            results.append({
                "path": str(f),
                "name": f.name,
                "status": status_text,
                "time": edit_time if is_edited else "",
                "mtime": f.stat().st_mtime,
                "thumb": str(thumb_path) if thumb_path.exists() else None,
                "type": "ORIGINAL",
                "is_edited": is_edited,
                "duration": self.get_video_duration(f),
                "cat_sub": f"{cat} > {sub}",
                "edit_params": edit_params if is_edited else ""
            })
        return results

    def get_edited_videos(self, cat, sub):
        paths = utils.get_paths(cat, sub)
        edited_dir = paths["video_dir"] / "Edited"
        if not edited_dir.exists(): return []

        uploaded_map = {}
        if paths["history_up"].exists():
            try:
                with paths["history_up"].open("r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split("|")
                        if len(parts) >= 2: uploaded_map[Path(parts[0]).name] = parts
            except: pass

        results = []
        files = list(edited_dir.glob("*.mp4"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for f in files:
            stat = uploaded_map.get(f.name)
            display_status = "ĐÃ CHỈNH SỬA (CHƯA ĐĂNG)"
            pub_time = None

            if stat:
                status_code = stat[1]
                raw_time = stat[2] if len(stat) > 2 else ""
                if status_code == "SCHEDULED": display_status = f"⏳ LỊCH ĐĂNG: {raw_time}"
                elif status_code == "PUBLISHED": display_status = "✅ ĐÃ ĐĂNG"
                pub_time = raw_time

            original_stem = f.name.split("_ed")[0]
            original_path = paths["video_dir"] / (original_stem + ".mp4")
            thumb_path = paths["thumb_dir"] / (original_stem + ".jpg")

            edit_info = "Speed: 1.05x, Crop: 10px, Gamma: 1.1"

            results.append({
                "path": str(f),
                "name": f.name,
                "status": display_status,
                "mtime": f.stat().st_mtime,
                "thumb": str(thumb_path) if thumb_path.exists() else None,
                "type": "EDITED",
                "original_path": str(original_path) if original_path.exists() else None,
                "duration": self.get_video_duration(f),
                "cat_sub": f"{cat} > {sub}",
                "edit_params": edit_info,
                "publish_time": pub_time
            })
        return results

    def process_download_queue(self, cat, sub, queue, cb):
        if not queue:
            self.log("Không có link!")
            return

        self.log(f"Bắt đầu tiến trình tải xuống {len(queue)} video")
        driver = None
        try:
            driver = browser.setup_driver(self.settings)
            downloader.run(driver, cat, sub, queue, cb, self.settings, self.check_stop, self.log)
        finally:
            if driver:
                try: driver.quit()
                except: pass

    # [FIX] Added status_cb for Auto Edit check
    def batch_process_videos(self, file_paths, edit_settings, status_cb=None):
        if not file_paths: return []
        processed_files = []
        first_path = Path(file_paths[0])
        output_dir = first_path.parent / "Edited"
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, input_path_str in enumerate(file_paths):
            try:
                self.check_stop()
                input_path = Path(input_path_str)
                if not input_path.exists(): continue

                # Update UI status
                if status_cb: status_cb(str(input_path), "processing")
                self.log(f"Đang edit video {input_path.name}")

                suffix = "_ed"
                new_name = f"{input_path.stem}{suffix}_{int(datetime.now().timestamp())}.mp4"
                output_path = output_dir / new_name

                # Call processor
                success = video_processor.process_video(input_path, output_path, edit_settings, self.log)
                if success:
                    processed_files.append(str(output_path))
                    self.log(f"Đã sửa xong")

                if status_cb: status_cb(str(input_path), "done")

            except Exception as e: self.log(f"Lỗi video {i}: {e}")
        return processed_files

    def count_posts_on_date(self, cat, sub, date_str): return uploader.count_posts_on_date(cat, sub, date_str)

    def run_uploader(self, specific_times, target_files, cat, sub, config_data):
        self.log("Bắt đầu upload...")
        uploader.run(self.settings, specific_times, target_files, cat, sub, config_data, self.check_stop, self.log)

    def open_local_path(self, path):
        if os.path.exists(path): os.startfile(path)

    def get_paths(self, cat, sub): return utils.get_paths(cat, sub)