import os
import re
import platform
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

def clean_path_name(name):
    name = "".join([c for c in str(name) if c.isprintable()])
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()

def get_paths(cat, sub_cat):
    safe_cat = clean_path_name(cat)
    safe_sub = clean_path_name(sub_cat)
    if not safe_cat: safe_cat = "Uncategorized"
    if not safe_sub: safe_sub = "General"
    base = Path("Data") / safe_cat / safe_sub
    return {
        "link_file": base / "tiktok_links.txt",
        "video_dir": base / "Videos",
        "history_dl": base / "downloaded_history.txt",
        "history_up": base / "uploaded_history.txt",
        "thumb_dir": base / "Videos" / "_thumbs"
    }

def open_local_path(path_str):
    try:
        path = os.path.normpath(path_str)
        if not os.path.exists(path): return
        if platform.system() == "Windows": os.startfile(path)
        elif platform.system() == "Darwin": subprocess.Popen(["open", path])
        else: subprocess.Popen(["xdg-open", path])
    except: pass

def open_folder_containing(file_path):
    try:
        folder = os.path.dirname(file_path)
        open_local_path(folder)
    except: pass

def get_video_thumbnail(video_path, thumb_path):
    if not CV2_AVAILABLE: return None
    try:
        Path(thumb_path).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(thumb_path): return str(thumb_path)
        cam = cv2.VideoCapture(str(video_path))
        ret, frame = cam.read()
        if ret:
            h, w = frame.shape[:2]
            new_w = 150; new_h = int(h * (new_w / w))
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            ext = os.path.splitext(thumb_path)[1]
            is_success, im_buf = cv2.imencode(ext, resized)
            if is_success:
                im_buf.tofile(str(thumb_path))
                cam.release()
                return str(thumb_path)
        cam.release()
        return None
    except: return None

def wait_file(folder):
    start = time.time()
    initial = set(folder.glob("*.mp4"))
    while time.time() - start < 60:
        current = set(folder.glob("*.mp4"))
        new = current - initial
        if new and not list(folder.glob("*.crdownload")): return list(new)[0].name
        time.sleep(1)
    return None