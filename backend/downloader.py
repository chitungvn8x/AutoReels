import time
import shutil
import random
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import utils

def run(driver, cat, sub_cat, queue_list, status_cb, settings, stop_check_func, log_func):
    if not queue_list: return

    paths = utils.get_paths(cat, sub_cat)
    paths["video_dir"].mkdir(parents=True, exist_ok=True)
    paths["thumb_dir"].mkdir(parents=True, exist_ok=True)

    dl_temp = Path(settings["default_download_dir"])
    main_window = driver.current_window_handle

    for index, link in enumerate(queue_list):
        stop_check_func()

        log_func(f"Đang đợi file thứ {index+1}")
        # [UPDATED] Send initial pct text
        status_cb(link, "Đang tải...", None, None, None, "0%", link)

        try:
            driver.get("https://snaptik.vn/en")
            wait = WebDriverWait(driver, 25)
            inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='TikTok']")))
            inp.clear(); inp.send_keys(link); time.sleep(0.5)

            try:
                submit = driver.find_element(By.XPATH, "//button[@id='submit']")
                driver.execute_script("arguments[0].click();", submit)
            except:
                driver.find_element(By.XPATH, "//button[contains(@class,'download')]").click()

            status_cb(link, "Đang tải...", None, None, None, "50%", link)

            time.sleep(2)
            if len(driver.window_handles) > 1:
                for handle in driver.window_handles:
                    if handle != main_window:
                        driver.switch_to.window(handle); driver.close()
                driver.switch_to.window(main_window)

            hd_found = False
            xpaths = ["//a[contains(text(), ' Video (original HD)')]", "//a[normalize-space()='Video (original HD)']", "//a[contains(@href, 'token=')]"]
            for xpath in xpaths:
                try:
                    hd_btn = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hd_btn)
                    time.sleep(1); driver.execute_script("arguments[0].click();", hd_btn)
                    hd_found = True; break
                except: continue

            if not hd_found:
                status_cb(link, "Lỗi nút HD", None, None, None, "0%", link)
                continue

            fname = utils.wait_file(dl_temp)
            if fname:
                ts = int(time.time())
                new_name = f"vid_{ts}_{random.randint(100,999)}.mp4"
                final_path = paths["video_dir"] / new_name
                shutil.move(str(dl_temp/fname), str(final_path))
                with paths["history_dl"].open("a", encoding="utf-8") as f: f.write(f"{link}\n")

                thumb = utils.get_video_thumbnail(final_path, paths["thumb_dir"] / (final_path.stem + ".jpg"))
                now_str = datetime.now().strftime("%d/%m %H:%M")

                status_cb(link, "THÀNH CÔNG", str(final_path), thumb, now_str, "100%", link)
                log_func(f"Tải xong video thứ {index+1}")
            else:
                status_cb(link, "Timeout", None, None, None, "0%", link)
                log_func("Hết thời gian chờ")

        except WebDriverException:
            log_func("Trình duyệt bị đóng"); return
        except Exception as e:
            status_cb(link, "Lỗi", None, None, None, "0%", link)
            log_func(f"Lỗi link: {e}")

    log_func("Đã hoàn tất phiên tải")