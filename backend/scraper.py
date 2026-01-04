import time
import os
from datetime import datetime
from selenium.webdriver.common.by import By
import utils
from backend import browser

def run(settings, tags_str, num_videos, cat, sub, stop_check_func, log_func):
    driver = None
    try:
        paths = utils.get_paths(cat, sub)
        # [FIX] Tạo thư mục nếu chưa có để tránh lỗi FileNotFoundError
        if not paths["link_file"].parent.exists():
            paths["link_file"].parent.mkdir(parents=True, exist_ok=True)

        existing_links = set()
        if paths["link_file"].exists():
            with paths["link_file"].open("r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split("|")
                    if parts[0].strip(): existing_links.add(parts[0].strip())

        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        if not tags: log_func("Chưa nhập hashtag!"); return

        driver = browser.setup_driver(settings)
        collected_links = set()

        log_func(f"Bắt đầu lấy thêm {num_videos} link")
        log_func("Đang mở trình duyệt")

        for tag in tags:
            stop_check_func()
            url = f"https://www.tiktok.com/tag/{tag.replace('#', '')}"
            driver.get(url)
            time.sleep(3)

            p_height = 0
            while len(collected_links) < num_videos:
                stop_check_func()
                elems = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")

                for e in elems:
                    link = e.get_attribute("href")
                    if link and link not in existing_links and link not in collected_links:
                        collected_links.add(link)
                        existing_links.add(link)
                        now_str = datetime.now().strftime("%d/%m %H:%M")
                        with paths["link_file"].open("a", encoding="utf-8") as f: f.write(f"{link}|{now_str}\n")

                        log_func(f"Tìm mới: {len(collected_links)}/{num_videos} link")
                        if len(collected_links) >= num_videos: break

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == p_height: break
                p_height = new_height
                if len(collected_links) >= num_videos: break
            if len(collected_links) >= num_videos: break

        log_func(f"Hoàn tất. Đã thêm {len(collected_links)} links mới")

    except Exception as e:
        if str(e) == "UserStopped": raise e
        log_func(f"Lỗi Scraper: {e}")
    finally:
        if driver: driver.quit()