import undetected_chromedriver as uc
from pathlib import Path
import pickle
import time

def get_cookie_folder():
    path = Path("Data") / "Cookies"
    path.mkdir(parents=True, exist_ok=True)
    return path

def setup_driver(settings, url=None):
    options = uc.ChromeOptions()
    # --- CẤU HÌNH TỐI ƯU ---
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--hide-crash-restore-bubble")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-default-browser-check")
    
    options.add_argument("--window-size=800,600") 
    # -----------------------
    
    # Logic profile tách rời
    options.add_argument(f'--user-data-dir={settings["chrome_user_data"]}')
    options.add_argument(f'--profile-directory={settings["chrome_profile"]}')
    
    if "default_download_dir" in settings:
        prefs = {
            "download.default_directory": str(settings["default_download_dir"]),
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "exit_type": "Normal"
        }
        options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(options=options, use_subprocess=False)
    if url: driver.get(url)
    return driver

def save_cookie(driver, profile_name):
    try:
        folder = get_cookie_folder()
        pickle.dump(driver.get_cookies(), open(folder / f"{profile_name}.pkl", "wb"))
        return True
    except: return False

def load_cookie(driver, profile_name):
    try:
        c_path = get_cookie_folder() / f"{profile_name}.pkl"
        if c_path.exists():
            for c in pickle.load(open(c_path, "rb")): driver.add_cookie(c)
            driver.refresh()
            time.sleep(3)
    except: pass