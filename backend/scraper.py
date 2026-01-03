import time
from datetime import datetime
from selenium.webdriver.common.by import By
import utils
from backend import browser

def run(settings, tags_str, num_videos, cat, sub, stop_check_func, log_func):
    driver = None
    try:
        paths = utils.get_paths(cat, sub)
        
        # [FIX] 1. Đọc các link ĐÃ CÓ trong file để tránh trùng lặp, KHÔNG XÓA FILE CŨ
        existing_links = set()
        if paths["link_file"].exists():
            with paths["link_file"].open("r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split("|")
                    if parts[0].strip():
                        existing_links.add(parts[0].strip())

        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        if not tags:
            log_func("⚠️ Chưa nhập hashtag!")
            return

        driver = browser.setup_driver(settings)
        collected_links = set() # Chỉ tính các link MỚI quét được trong phiên này
        
        log_func(f"🔍 Bắt đầu quét thêm {num_videos} video...")

        for tag in tags:
            stop_check_func()
            url = f"https://www.tiktok.com/tag/{tag.replace('#', '')}"
            driver.get(url)
            time.sleep(3)

            p_height = 0
            # Vòng lặp quét
            while len(collected_links) < num_videos:
                stop_check_func()
                elems = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
                
                for e in elems:
                    link = e.get_attribute("href")
                    # Chỉ lấy nếu link chưa có trong file cũ VÀ chưa có trong list mới
                    if link and link not in existing_links and link not in collected_links:
                        collected_links.add(link)
                        existing_links.add(link) # Add vào để không lặp lại trong vòng lặp sau
                        
                        # Ghi ngay vào file (Append mode 'a')
                        now_str = datetime.now().strftime("%d/%m %H:%M")
                        with paths["link_file"].open("a", encoding="utf-8") as f:
                            f.write(f"{link}|{now_str}\n")
                        
                        log_func(f"🔎 Tìm mới: {len(collected_links)}/{num_videos}")
                        if len(collected_links) >= num_videos:
                            break
                
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == p_height: break
                p_height = new_height

                if len(collected_links) >= num_videos: break
            
            if len(collected_links) >= num_videos: break

        log_func(f"✅ Hoàn tất. Đã thêm {len(collected_links)} link mới.")

    except Exception as e:
        if str(e) == "UserStopped": raise e
        log_func(f"❌ Lỗi Scraper: {e}")
    finally:
        if driver: driver.quit()