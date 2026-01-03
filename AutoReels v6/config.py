import os

SETTINGS_FILE = "settings_pro.json"

DEFAULT_SETTINGS = {
    "chrome_user_data": r"C:\ChromeProfiles\RecraftBot",
    "chrome_profile": "Profile 2",
    "default_download_dir": f"C:\\Users\\{os.getlogin()}\\Downloads",
    "upload_delay_minutes": 5,
    "current_tiktok_profile": "",
    "categories": {}
}