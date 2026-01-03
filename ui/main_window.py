import customtkinter as ctk
import threading
import json
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import webbrowser

from backend.manager import AutomationBackend
from ui.dialogs import ScheduleDialog
from ui.edit_dialog import EditConfigDialog
from ui.review_dialog import ReviewDialog
from ui.cards import VideoCardFactory
from ui.settings_tab import SettingsTab
from config import SETTINGS_FILE, DEFAULT_SETTINGS

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AutoReels Pro V92")
        self.geometry("1280x800")

        self.downloading_states = set()
        self.checked_links_cache = set()
        self.upload_selected_files = []
        self.download_queue_items = {}
        self.current_edited_items = {}
        self.current_view_mode = "PENDING"

        self.settings = self.load_settings()
        self.backend = AutomationBackend(self.settings, self.update_log_safe)
        self.card_factory = VideoCardFactory(self)

        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        self.tab_ops = self.tabview.add("🔥 VẬN HÀNH")
        self.tab_settings = self.tabview.add("⚙️ CÀI ĐẶT")

        # Cột Log
        self.setup_log_column()

        self.setup_operations_tab()
        self.settings_ui = SettingsTab(self.tab_settings, self)

        self.refresh_cat_list_ui()
        self.refresh_ops_combos()

    def setup_log_column(self):
        # [UPDATED] Frame log này sẽ được ẩn/hiện tùy Tab
        self.f_log_container = ctk.CTkFrame(self, fg_color="#1E1E1E")
        self.f_log_container.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(self.f_log_container, text="NHẬT KÝ HỆ THỐNG", font=("Arial", 12, "bold"), text_color="gray").pack(pady=5)
        self.txt_log = ctk.CTkTextbox(self.f_log_container)
        self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_log.configure(state="disabled")

    def on_tab_change(self):
        # [NEW] Ẩn cột Log khi ở tab Cài Đặt để nhường chỗ
        if self.tabview.get() == "⚙️ CÀI ĐẶT":
            self.f_log_container.grid_remove()
            self.grid_columnconfigure(1, weight=0) # Thu nhỏ cột log
        else:
            self.f_log_container.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
            self.grid_columnconfigure(1, weight=1)

    def setup_operations_tab(self):
        self.tab_ops.grid_columnconfigure(0, weight=1)

        f_top = ctk.CTkFrame(self.tab_ops, height=60, fg_color="transparent")
        f_top.pack(fill="x", padx=10, pady=5)

        f_top.grid_columnconfigure(0, weight=1); f_top.grid_columnconfigure(1, weight=1)
        f_top.grid_columnconfigure(2, weight=0); f_top.grid_columnconfigure(3, weight=0)

        # [UPDATED] Đổi tên Label
        f_cat = ctk.CTkFrame(f_top, fg_color="transparent")
        f_cat.grid(row=0, column=0, sticky="ew", padx=5)
        ctk.CTkLabel(f_cat, text="DANH MỤC:", font=("Arial", 14, "bold")).pack(side="left")
        self.combo_cat_ops = ctk.CTkComboBox(f_cat, command=self.on_change_cat_ops, width=250)
        self.combo_cat_ops.pack(side="left", fill="x", expand=True, padx=5)

        f_sub = ctk.CTkFrame(f_top, fg_color="transparent")
        f_sub.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(f_sub, text="NGÁCH:", font=("Arial", 14, "bold")).pack(side="left")
        self.combo_sub_ops = ctk.CTkComboBox(f_sub, command=self.on_change_sub_ops, width=250)
        self.combo_sub_ops.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(f_top, text="QUẢN LÝ DANH MỤC", command=lambda: self.tabview.set("⚙️ CÀI ĐẶT"),
                      width=150, fg_color="#34495E").grid(row=0, column=2, padx=5)

        self.btn_stop = ctk.CTkButton(f_top, text="🛑 DỪNG", command=self.stop_process,
                                      fg_color="#C0392B", width=80, state="disabled")
        self.btn_stop.grid(row=0, column=3, padx=5)

        paned = ctk.CTkFrame(self.tab_ops, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        f_left = ctk.CTkFrame(paned, width=250)
        f_left.pack(side="left", fill="y", padx=5)

        ctk.CTkLabel(f_left, text="1. TÌM KIẾM VIDEO", font=("Arial", 14, "bold")).pack(pady=10)
        self.entry_hash_ops = ctk.CTkTextbox(f_left, height=150)
        self.entry_hash_ops.pack(fill="x", padx=5)

        f_n = ctk.CTkFrame(f_left, fg_color="transparent")
        f_n.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(f_n, text="Số lượng:").pack(side="left")
        self.entry_num_ops = ctk.CTkEntry(f_n, width=60)
        self.entry_num_ops.pack(side="right"); self.entry_num_ops.insert(0,"5")

        ctk.CTkButton(f_left, text="QUÉT LINK TIKTOK", command=self.run_scraper_action, fg_color="green", height=40).pack(fill="x", padx=5, pady=10)

        # [UPDATED] Loại bỏ nút "Mở File Link" theo yêu cầu

        f_center = ctk.CTkFrame(paned)
        f_center.pack(side="left", fill="both", expand=True, padx=5)

        f_ctrl = ctk.CTkFrame(f_center, fg_color="transparent")
        f_ctrl.pack(fill="x", pady=5)

        self.btn_nav_pending = ctk.CTkButton(f_ctrl, text="DANH SÁCH CHỜ TẢI", command=lambda: self.log_and_load("PENDING"), width=140, fg_color="#555")
        self.btn_nav_pending.pack(side="left", padx=2)

        self.btn_nav_orig = ctk.CTkButton(f_ctrl, text="QUẢN LÝ VIDEO ĐÃ TẢI", command=lambda: self.log_and_load("ORIGINAL"), width=160, fg_color="#E67E22")
        self.btn_nav_orig.pack(side="left", padx=2)

        self.btn_nav_edit = ctk.CTkButton(f_ctrl, text="QUẢN LÝ VIDEO ĐÃ CHỈNH SỬA & ĐĂNG", command=lambda: self.log_and_load("EDITED"), width=240, fg_color="#27AE60")
        self.btn_nav_edit.pack(side="left", padx=2)

        self.scroll_queue = ctk.CTkScrollableFrame(f_center)
        self.scroll_queue.pack(fill="both", expand=True, padx=5, pady=5)

        self.f_action = ctk.CTkFrame(f_center, height=50, fg_color="#222")
        self.f_action.pack(fill="x")
        self.lbl_sel = ctk.CTkLabel(self.f_action, text="CHỌN: 0", font=("Arial", 12, "bold"), text_color="cyan")
        self.lbl_sel.pack(side="left", padx=15)

        self.f_batch_dl = ctk.CTkFrame(self.f_action, fg_color="transparent")
        self.f_batch_orig = ctk.CTkFrame(self.f_action, fg_color="transparent")
        self.f_batch_up = ctk.CTkFrame(self.f_action, fg_color="transparent")

        ctk.CTkButton(self.f_batch_dl, text="⬇ TẢI TẤT CẢ ĐÃ CHỌN", command=self.run_downloader_queue, fg_color="orange").pack(side="right")

        ctk.CTkButton(self.f_batch_orig, text="⚡ AUTO EDIT (BATCH)", command=self.run_batch_auto_edit, fg_color="purple").pack(side="right")

        ctk.CTkButton(self.f_batch_up, text="ĐĂNG NGAY", command=self.upload_now, fg_color="green", width=100).pack(side="right", padx=5)
        ctk.CTkButton(self.f_batch_up, text="LÊN LỊCH", command=self.upload_schedule, width=100).pack(side="right", padx=5)

    def log_and_load(self, mode):
        self.log_message(f"📂 Chuyển sang tab: {mode}")
        self.load_list(mode)

    def load_list(self, mode):
        self.current_view_mode = mode
        self.btn_nav_pending.configure(fg_color="#555", border_width=0)
        self.btn_nav_orig.configure(fg_color="#E67E22", border_width=0)
        self.btn_nav_edit.configure(fg_color="#27AE60", border_width=0)

        self.f_batch_dl.pack_forget(); self.f_batch_orig.pack_forget(); self.f_batch_up.pack_forget()
        self.upload_selected_files = []; self.checked_links_cache = set()
        self.lbl_sel.configure(text="CHỌN: 0")

        for w in list(self.scroll_queue.winfo_children()): w.destroy()
        self.scroll_queue._parent_canvas.yview_moveto(0)

        items = []
        if mode == "PENDING":
            self.btn_nav_pending.configure(fg_color="#3498DB", border_width=2, border_color="white")
            self.f_batch_dl.pack(side="right", padx=10)
            items = self.backend.get_download_list(self.combo_cat_ops.get(), self.combo_sub_ops.get(), "PENDING")
            self.download_queue_items = {}
            for i in items:
                link = i["data"]
                refs = self.card_factory.create_queue_card(self.scroll_queue, i, initial_check=False)
                self.download_queue_items[link] = refs

        elif mode == "ORIGINAL":
            self.btn_nav_orig.configure(fg_color="#D35400", border_width=2, border_color="white")
            self.f_batch_orig.pack(side="right", padx=10)
            items = self.backend.get_original_videos(self.combo_cat_ops.get(), self.combo_sub_ops.get())
            for i in items: self.card_factory.create_upload_card(self.scroll_queue, i)

        elif mode == "EDITED":
            self.btn_nav_edit.configure(fg_color="#1E8449", border_width=2, border_color="white")
            self.f_batch_up.pack(side="right", padx=10)
            items = self.backend.get_edited_videos(self.combo_cat_ops.get(), self.combo_sub_ops.get())
            for i in items: self.card_factory.create_upload_card(self.scroll_queue, i)

        if not items:
            ctk.CTkLabel(self.scroll_queue, text="DANH SÁCH TRỐNG", text_color="gray", font=("Arial", 16)).pack(pady=50)

    # ... (Keep existing helpers: on_check_dl, on_check_upload, run_downloader_queue, ...)
    def on_check_dl(self, var, link):
        if var.get(): self.checked_links_cache.add(link)
        else: self.checked_links_cache.remove(link)
        self.lbl_sel.configure(text=f"CHỌN: {len(self.checked_links_cache)}")
    def on_check_upload(self, var, path):
        if var.get():
            if path not in self.upload_selected_files: self.upload_selected_files.append(path)
        else:
            if path in self.upload_selected_files: self.upload_selected_files.remove(path)
        self.lbl_sel.configure(text=f"CHỌN: {len(self.upload_selected_files)}")
    def run_downloader_queue(self):
        to_dl = list(self.checked_links_cache)
        if not to_dl: messagebox.showwarning("!", "Chưa chọn link!"); return
        ordered_dl = []
        for link in self.download_queue_items.keys():
            if link in to_dl: ordered_dl.append(link)
        self.log_message(f"⬇ Bắt đầu tải {len(ordered_dl)} video...")
        threading.Thread(target=self._download_thread_worker, args=(ordered_dl,), daemon=True).start()

    # --- UPDATED ACTIONS ---
    def process_single_video(self, file_path, mode):
        self.upload_selected_files = [file_path]

        # [NEW] Cảnh báo nếu đã edit rồi
        # Check status from UI or Backend path logic (tạm check qua tên file hoặc trạng thái hiển thị)
        # Tuy nhiên ở đây ta trigger từ nút, nên cứ cảnh báo chung

        if mode == "quick":
            # Show default params
            msg = "⚡ CẤU HÌNH AUTO EDIT:\n\n- Speed: 1.05x\n- Crop: 10px\n- Gamma: 1.1\n- Cut Start/End: 0s\n\nBạn có ĐỒNG Ý không?"
            if messagebox.askyesno("Xác nhận Auto Edit", msg):
                self.run_processing_task({"speed": 1.05, "crop": 10, "gamma": 1.1, "mirror": False})
            else:
                # Nếu không đồng ý -> Mở form tùy chỉnh
                EditConfigDialog(self, self.run_processing_task)
        else:
            EditConfigDialog(self, self.run_processing_task)

    def run_batch_auto_edit(self):
        if not self.upload_selected_files: messagebox.showwarning("!", "Chưa chọn video!"); return

        # [NEW] Batch logic: Đồng ý hoặc Hủy bỏ
        msg = f"⚡ AUTO EDIT {len(self.upload_selected_files)} VIDEO?\n\nCấu hình mặc định:\n- Speed: 1.05x\n- Crop: 10px\n- Gamma: 1.1"
        res = messagebox.askyesno("Xác nhận Batch Edit", msg) # Yes/No
        if res:
            self.run_processing_task({"speed": 1.05, "crop": 10, "gamma": 1.1, "mirror": False})
        else:
            # Hủy bỏ (Không làm gì)
            return

    # --- CONTEXT MENU (Updated) ---
    def show_context_menu(self, event, item, menu_type):
        try:
            menu = tk.Menu(self, tearoff=0)
            if menu_type == "PENDING":
                link = item["data"]
                menu.add_command(label="⬇ Tải Ngay", command=lambda: self.run_single_download(link))
                menu.add_command(label="🌐 Xem Online", command=lambda: self.log_open_browser(link))
                menu.add_separator()
                menu.add_command(label="🗑 Xóa", command=lambda: self.remove_from_queue(link)) # Icon text
            elif menu_type == "ORIGINAL":
                path = item["path"]
                menu.add_command(label="▶ Xem Ngay (Local)", command=lambda: os.startfile(path))
                menu.add_command(label="🌐 Xem Link Gốc (Online)", command=lambda: self.log_open_browser("https://tiktok.com")) # Placeholder link, cần lưu link gốc vào metadata nếu muốn chính xác
                menu.add_separator()
                menu.add_command(label="📂 Mở Thư Mục", command=lambda: os.startfile(os.path.dirname(path)))
                menu.add_command(label="⚡ Auto Edit", command=lambda: self.process_single_video(path, "quick"))
                menu.add_command(label="🛠 Tùy chỉnh", command=lambda: self.process_single_video(path, "custom"))
            elif menu_type == "EDITED":
                path = item["path"]
                menu.add_command(label="▶ Xem Ngay", command=lambda: os.startfile(path))
                menu.add_command(label="📂 Mở Thư Mục", command=lambda: os.startfile(os.path.dirname(path)))
                menu.add_command(label="👁 Review So Sánh", command=lambda: self.open_review_for_item(item))
                menu.add_separator()
                menu.add_command(label="🚀 Đăng Ngay", command=lambda: self.run_task(lambda: self.exec_single_upload(path, None)))
                menu.add_command(label="📅 Lên Lịch", command=lambda: self.single_schedule(path))
            menu.tk_popup(event.x_root, event.y_root)
        except: pass

    # ... (Keep other helpers)
    def log_open_browser(self, link): webbrowser.open(link)
    def run_single_download(self, link): threading.Thread(target=self._download_thread_worker, args=([link],), daemon=True).start()
    def _download_thread_worker(self, to_dl):
        self.backend.process_download_queue(self.combo_cat_ops.get(), self.combo_sub_ops.get(), to_dl, self.update_dl_status_safe)
        self.after(0, lambda: self.finish_download_batch())
    def finish_download_batch(self):
        self.log_message("✅ Đã hoàn tất phiên tải."); messagebox.showinfo("Thông báo", "Đã tải xong!"); self.log_and_load("PENDING")
    def update_dl_status_safe(self, link, status, path, thumb, tm, url=None): self.after(0, lambda: self._update_dl_card_ui(link, status, path, thumb))
    def _update_dl_card_ui(self, link, status, path, thumb):
        if link in self.download_queue_items:
            ui = self.download_queue_items[link]
            ui["lbl"].configure(text=status)
            if "Đang tải" in status: ui["lbl"].configure(text_color="#3498DB"); ui["prog"].pack(pady=5); ui["prog"].start()
            elif "THÀNH CÔNG" in status:
                ui["lbl"].configure(text="✅ XONG", text_color="green"); ui["prog"].stop(); ui["prog"].pack_forget(); self.remove_from_queue(link)
            else: ui["lbl"].configure(text_color="red"); ui["prog"].stop(); ui["prog"].pack_forget()
    def run_scraper_action(self):
        if not self.combo_cat_ops.get(): messagebox.showwarning("!", "Vui lòng chọn Ngách!"); return
        self.run_task(self.run_scraper, cb=lambda: self.load_list("PENDING"))
    def run_scraper(self): self.backend.run_tiktok_scraper(self.entry_hash_ops.get("1.0", "end"), int(self.entry_num_ops.get()), self.combo_cat_ops.get(), self.combo_sub_ops.get(), self.settings["current_tiktok_profile"])
    def on_change_cat_ops(self, cat):
        subs = list(self.settings["categories"][cat]["sub_categories"].keys()); self.combo_sub_ops.configure(values=subs)
        if subs: self.combo_sub_ops.set(subs[0]); self.on_change_sub_ops(subs[0])
        else: self.combo_sub_ops.set(""); self.entry_hash_ops.delete("1.0", "end")
    def on_change_sub_ops(self, sub):
        cat = self.combo_cat_ops.get()
        if cat and sub:
            d = self.settings["categories"][cat]["sub_categories"].get(sub, {})
            self.entry_hash_ops.delete("1.0", "end"); self.entry_hash_ops.insert("1.0", ", ".join(d.get("hashtags", []))); self.load_list(self.current_view_mode)
    def run_processing_task(self, settings): self.btn_stop.configure(state="normal"); threading.Thread(target=lambda: self._thread_process(settings)).start()
    def _thread_process(self, settings):
        try:
            new_files = self.backend.batch_process_videos(self.upload_selected_files, settings)
            self.after(0, lambda: self._post_process_ui(new_files))
        except Exception as e: self.after(0, lambda: messagebox.showerror("Lỗi", str(e)))
    def _post_process_ui(self, new_files):
        self.btn_stop.configure(state="disabled")
        if new_files:
            if messagebox.askyesno("XONG", f"Đã edit {len(new_files)} video. Xem danh sách?"): self.load_list("EDITED")
            else: self.load_list("ORIGINAL")
    def upload_now(self):
        if not self.upload_selected_files: messagebox.showwarning("!", "Chưa chọn video!"); return
        self.run_task(lambda: self.exec_upload(None), cb=lambda: self.load_list("EDITED"))
    def upload_schedule(self):
        if not self.upload_selected_files: messagebox.showwarning("!", "Chưa chọn video!"); return
        file_names = [os.path.basename(p) for p in self.upload_selected_files]
        ScheduleDialog(self, self.exec_upload, file_names)
    def exec_upload(self, times):
        cat = self.combo_cat_ops.get(); sub = self.combo_sub_ops.get()
        conf = self.settings["categories"][cat]["sub_categories"].get(sub, {})
        self.backend.run_uploader(times, self.upload_selected_files, cat, sub, conf)
        self.after(0, lambda: self.on_upload_complete(times))
    def on_upload_complete(self, times):
        if messagebox.askyesno("XONG", "Mở Content Library?"): webbrowser.open("https://www.facebook.com/professional_dashboard/content/content_library")
        self.load_list("EDITED")
    def open_review_for_item(self, item): ReviewDialog(self, item.get("original_path"), item.get("path"))
    def remove_from_queue(self, link):
        if link in self.download_queue_items:
            try: self.download_queue_items[link]["card"].destroy()
            except: pass
            del self.download_queue_items[link]
            if link in self.checked_links_cache: self.checked_links_cache.remove(link)
    def run_task(self, func, cb=None): self.btn_stop.configure(state="normal"); threading.Thread(target=lambda: [func(), self.after(0, lambda: self.reset_ui(cb))], daemon=True).start()
    def reset_ui(self, cb): self.btn_stop.configure(state="disabled"); self.log_message("✅ Tác vụ hoàn tất."); cb() if cb else None
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try: return {**DEFAULT_SETTINGS, **json.load(open(SETTINGS_FILE, encoding="utf-8"))}
            except: pass
        return DEFAULT_SETTINGS
    def update_log_safe(self, msg): self.after(0, lambda: self.log_message(msg))
    def log_message(self, msg):
        try: self.txt_log.configure(state="normal"); self.txt_log.insert("end", f"{msg}\n"); self.txt_log.see("end"); self.txt_log.configure(state="disabled")
        except: pass
    def refresh_ops_combos(self):
        cats = list(self.settings["categories"].keys())
        self.combo_cat_ops.configure(values=cats)
        if cats: self.combo_cat_ops.set(cats[0]); self.on_change_cat_ops(cats[0])
    def open_link_file(self): self.backend.open_local_path(str(self.backend.get_paths(self.combo_cat_ops.get(), self.combo_sub_ops.get())["link_file"]))
    def stop_process(self): self.backend.stop_flag = True
    def refresh_cat_list_ui(self): self.settings_ui.refresh_cat_list_ui()
    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(self.settings, f, ensure_ascii=False, indent=4)
    def add_item(self, t): self.settings_ui.add_item(t)
    def delete_item(self, t): self.settings_ui.delete_item(t)
    def import_txt(self, t): self.settings_ui.import_txt(t)
    def verify_fanpage_connection(self): self.settings_ui.verify_fanpage_connection()
    def get_cookie_action(self): self.start_cookie_flow()
    def single_schedule(self, path): ScheduleDialog(self, lambda times: self.exec_single_upload(path, times), [os.path.basename(path)])
    def exec_single_upload(self, path, times):
        cat = self.combo_cat_ops.get(); sub = self.combo_sub_ops.get()
        conf = self.settings["categories"][cat]["sub_categories"].get(sub, {})
        self.backend.run_uploader(times, [path], cat, sub, conf)
        self.after(0, lambda: self.on_upload_complete(times))