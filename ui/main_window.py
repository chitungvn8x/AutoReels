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
        self.title("AutoReels Pro V90 (Full Fixed)")
        self.geometry("1280x800")
        self.minsize(1024, 700)
        
        self.downloading_states = set()
        self.checked_links_cache = set()
        self.upload_selected_files = [] 
        self.download_queue_items = {}
        self.current_edited_items = {} 
        self.current_view_mode = "PENDING"

        self.settings = self.load_settings()
        self.backend = AutomationBackend(self.settings, self.update_log_safe)
        self.card_factory = VideoCardFactory(self)
        
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tab_ops = self.tabview.add("🔥 VẬN HÀNH")
        self.tab_settings = self.tabview.add("⚙️ CÀI ĐẶT")

        self.setup_operations_tab()
        self.settings_ui = SettingsTab(self.tab_settings, self)
        
        self.refresh_cat_list_ui()
        self.refresh_ops_combos()
        try: self.after(0, lambda: self.state("zoomed"))
        except: pass

    # --- SETUP UI VẬN HÀNH ---
    def setup_operations_tab(self):
        self.tab_ops.grid_columnconfigure(0, weight=1)
        
        # 1. HEADER
        f_top = ctk.CTkFrame(self.tab_ops, height=60)
        f_top.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(f_top, text="NGÁCH:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        self.combo_cat_ops = ctk.CTkComboBox(f_top, command=self.on_change_cat_ops, width=200)
        self.combo_cat_ops.pack(side="left", padx=5)
        
        self.combo_sub_ops = ctk.CTkComboBox(f_top, command=self.on_change_sub_ops, width=200)
        self.combo_sub_ops.pack(side="left", padx=5)
        
        ctk.CTkButton(f_top, text="⚙️ CÀI ĐẶT", command=lambda: self.tabview.set("⚙️ CÀI ĐẶT"), width=100, fg_color="#34495E").pack(side="left", padx=10)
        self.btn_stop = ctk.CTkButton(f_top, text="🛑 DỪNG", command=self.stop_process, fg_color="#C0392B", width=80, state="disabled")
        self.btn_stop.pack(side="right", padx=10)
        
        # 2. MAIN PANED
        paned = ctk.CTkFrame(self.tab_ops, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- LEFT PANEL (SCRAPER) ---
        f_left = ctk.CTkFrame(paned, width=280)
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
        ctk.CTkButton(f_left, text="Mở File Link", command=self.open_link_file, fg_color="gray").pack(fill="x", padx=5)

        # --- CENTER PANEL (LIST VIEW) ---
        f_center = ctk.CTkFrame(paned)
        f_center.pack(side="left", fill="both", expand=True, padx=5)
        
        # Navigation Buttons
        f_ctrl = ctk.CTkFrame(f_center, fg_color="transparent")
        f_ctrl.pack(fill="x", pady=5)
        
        self.btn_nav_pending = ctk.CTkButton(f_ctrl, text="DANH SÁCH CHỜ TẢI", command=lambda: self.log_and_load("PENDING"), width=140, fg_color="#555")
        self.btn_nav_pending.pack(side="left", padx=2)
        
        self.btn_nav_orig = ctk.CTkButton(f_ctrl, text="QUẢN LÝ VIDEO ĐÃ TẢI", command=lambda: self.log_and_load("ORIGINAL"), width=160, fg_color="#E67E22")
        self.btn_nav_orig.pack(side="left", padx=2)
        
        self.btn_nav_edit = ctk.CTkButton(f_ctrl, text="QUẢN LÝ VIDEO ĐÃ CHỈNH SỬA & ĐĂNG", command=lambda: self.log_and_load("EDITED"), width=240, fg_color="#27AE60")
        self.btn_nav_edit.pack(side="left", padx=2)

        # Scroll List
        self.scroll_queue = ctk.CTkScrollableFrame(f_center)
        self.scroll_queue.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Action Bar (Footer)
        self.f_action = ctk.CTkFrame(f_center, height=50, fg_color="#222")
        self.f_action.pack(fill="x")
        self.lbl_sel = ctk.CTkLabel(self.f_action, text="CHỌN: 0", font=("Arial", 12, "bold"), text_color="cyan")
        self.lbl_sel.pack(side="left", padx=15)
        
        # Container nút bấm động
        self.f_batch_dl = ctk.CTkFrame(self.f_action, fg_color="transparent")
        self.f_batch_up = ctk.CTkFrame(self.f_action, fg_color="transparent")
        
        ctk.CTkButton(self.f_batch_dl, text="⬇ TẢI TẤT CẢ ĐÃ CHỌN", command=self.run_downloader_queue, fg_color="orange").pack(side="right")
        
        ctk.CTkButton(self.f_batch_up, text="ĐĂNG NGAY", command=self.upload_now, fg_color="green", width=100).pack(side="right", padx=5)
        ctk.CTkButton(self.f_batch_up, text="LÊN LỊCH", command=self.upload_schedule, width=100).pack(side="right", padx=5)

        # --- RIGHT PANEL (LOG) ---
        # [FIX] Thu hẹp Log còn khoảng 300px
        f_right = ctk.CTkFrame(paned, width=300) 
        f_right.pack(side="right", fill="y", padx=5)
        
        ctk.CTkLabel(f_right, text="NHẬT KÝ HOẠT ĐỘNG", font=("Arial", 12, "bold")).pack(pady=5)
        self.txt_log = ctk.CTkTextbox(f_right, width=280)
        self.txt_log.pack(fill="both", expand=True, padx=2, pady=2)

    # --- LOGIC CHUYỂN TAB & LOAD LIST ---
    def log_and_load(self, mode):
        self.log_message(f"📂 Chuyển sang tab: {mode}")
        self.load_list(mode)

    def load_list(self, mode):
        self.current_view_mode = mode
        
        # Reset màu nút
        self.btn_nav_pending.configure(fg_color="#555", border_width=0)
        self.btn_nav_orig.configure(fg_color="#E67E22", border_width=0)
        self.btn_nav_edit.configure(fg_color="#27AE60", border_width=0)
        
        # Ẩn nút batch action
        self.f_batch_dl.pack_forget()
        self.f_batch_up.pack_forget()
        
        # Reset dữ liệu chọn
        self.upload_selected_files = []
        self.checked_links_cache = set()
        self.lbl_sel.configure(text="CHỌN: 0")
        
        # Xóa list cũ
        for w in list(self.scroll_queue.winfo_children()): w.destroy()
        
        items = []

        # --- LOAD DATA TÙY TAB ---
        if mode == "PENDING":
            self.btn_nav_pending.configure(fg_color="#3498DB", border_width=2, border_color="white")
            self.f_batch_dl.pack(side="right", padx=10) # Hiện nút Tải
            
            items = self.backend.get_download_list(self.combo_cat_ops.get(), self.combo_sub_ops.get(), "PENDING")
            self.download_queue_items = {}
            for i in items:
                link = i["data"]
                # Tạo Card Pending
                refs = self.card_factory.create_queue_card(self.scroll_queue, i, initial_check=False)
                self.download_queue_items[link] = refs

        elif mode == "ORIGINAL":
            self.btn_nav_orig.configure(fg_color="#D35400", border_width=2, border_color="white")
            items = self.backend.get_original_videos(self.combo_cat_ops.get(), self.combo_sub_ops.get())
            for i in items:
                # Tạo Card Video (Gốc)
                self.card_factory.create_upload_card(self.scroll_queue, i)
        
        elif mode == "EDITED":
            self.btn_nav_edit.configure(fg_color="#1E8449", border_width=2, border_color="white")
            self.f_batch_up.pack(side="right", padx=10) # Hiện nút Đăng/Lên lịch
            
            items = self.backend.get_edited_videos(self.combo_cat_ops.get(), self.combo_sub_ops.get())
            # Lưu map để lấy file gốc cho Review
            self.current_edited_items = {i['path']: i for i in items}
            for i in items:
                # Tạo Card Video (Edit)
                self.card_factory.create_upload_card(self.scroll_queue, i)

        if not items:
            ctk.CTkLabel(self.scroll_queue, text="DANH SÁCH TRỐNG", text_color="gray", font=("Arial", 16)).pack(pady=50)
        
        self.log_message(f"Tải xong danh sách {mode}: {len(items)} items")

    # --- MENU CHUỘT PHẢI (CONTEXT MENU) ---
    def show_context_menu(self, event, item, menu_type):
        try:
            menu = tk.Menu(self, tearoff=0)
            
            if menu_type == "PENDING":
                link = item["data"]
                # [FIX] Mở link gốc
                menu.add_command(label="🔗 Mở Link Gốc (Trình duyệt)", command=lambda: webbrowser.open(link))
                menu.add_separator()
                menu.add_command(label="Xóa khỏi danh sách", command=lambda: self.remove_from_queue(link))
                
            elif menu_type == "ORIGINAL":
                path = item["path"]
                folder = os.path.dirname(path)
                menu.add_command(label="📂 Mở Thư Mục Chứa", command=lambda: os.startfile(folder))
                menu.add_command(label="▶ Xem Video (System)", command=lambda: os.startfile(path))
                menu.add_separator()
                menu.add_command(label="⚡ Auto Edit", command=lambda: self.process_single_video(path, "quick"))
                menu.add_command(label="🛠 Tùy chỉnh Edit", command=lambda: self.process_single_video(path, "custom"))
                
            elif menu_type == "EDITED":
                path = item["path"]
                folder = os.path.dirname(path)
                menu.add_command(label="📂 Mở Thư Mục Chứa", command=lambda: os.startfile(folder))
                menu.add_command(label="👁 Review So Sánh", command=lambda: self.open_review_for_item(item))
                menu.add_separator()
                menu.add_command(label="Đăng Ngay", command=lambda: self.run_task(lambda: self.exec_single_upload(path, None)))
                menu.add_command(label="Lên Lịch", command=lambda: self.single_schedule(path))

            menu.tk_popup(event.x_root, event.y_root)
            self.log_message(f"🖱️ Mở menu chuột phải cho: {item.get('name', 'Link')}")
        except: pass

    # --- DOWNLOADER (FIX TREO & AUTO REFRESH) ---
    def run_downloader_queue(self):
        if not self.combo_cat_ops.get():
             messagebox.showwarning("!", "Vui lòng chọn Ngách!"); return
        
        to_dl = list(self.checked_links_cache)
        if not to_dl: 
            messagebox.showwarning("!", "Chưa chọn link nào để tải!"); return
            
        self.log_message(f"⬇ Bắt đầu tải {len(to_dl)} video...")
        self.f_batch_dl.pack_forget() # Ẩn nút tải đi để tránh bấm nhiều lần
        
        # [FIX] Chạy luồng riêng (Threading)
        threading.Thread(target=self._download_thread_worker, args=(to_dl,), daemon=True).start()

    def _download_thread_worker(self, to_dl):
        # Gọi backend xử lý
        self.backend.process_download_queue(
            self.combo_cat_ops.get(), 
            self.combo_sub_ops.get(), 
            to_dl, 
            self.update_dl_status_safe # Callback update UI
        )
        # [FIX] Refresh ngay sau khi xong (quay về main thread)
        self.after(0, lambda: self.finish_download_batch())

    def finish_download_batch(self):
        self.log_message("✅ Đã hoàn tất phiên tải.")
        messagebox.showinfo("Thông báo", "Đã tải xong toàn bộ video đã chọn!")
        self.log_and_load("PENDING") # Refresh list

    def update_dl_status_safe(self, link, status, path, thumb, tm, url=None):
        # Đẩy update UI về main thread
        self.after(0, lambda: self._update_dl_card_ui(link, status, path, thumb))

    def _update_dl_card_ui(self, link, status, path, thumb):
        if link in self.download_queue_items:
            ui = self.download_queue_items[link]
            ui["lbl"].configure(text=status)
            
            # [FIX] Hiển thị Progress Bar
            if "Đang tải" in status:
                ui["lbl"].configure(text_color="#3498DB")
                ui["prog"].pack(pady=5) # Hiện thanh
                ui["prog"].start()
            elif "THÀNH CÔNG" in status:
                ui["lbl"].configure(text="✅ XONG", text_color="green")
                ui["prog"].stop()
                ui["prog"].pack_forget() # Ẩn thanh
                # Tự xóa khỏi list visual
                self.remove_from_queue(link) 
            else:
                ui["lbl"].configure(text_color="red")
                ui["prog"].stop()
                ui["prog"].pack_forget()

    # --- CÁC HÀM XỬ LÝ KHÁC (CHECKBOX, SCRAPER, EDIT...) ---
    def run_scraper_action(self):
        self.log_message("🔍 Bấm nút Quét Link...")
        if not self.combo_cat_ops.get():
             messagebox.showwarning("!", "Vui lòng chọn Ngách!"); return
        self.run_task(self.run_scraper, cb=lambda: self.load_list("PENDING"))

    def run_scraper(self): 
        self.backend.run_tiktok_scraper(
            self.entry_hash_ops.get("1.0", "end"), int(self.entry_num_ops.get()), 
            self.combo_cat_ops.get(), self.combo_sub_ops.get(), self.settings["current_tiktok_profile"])

    def on_check_dl(self, var, link):
        if var.get(): self.checked_links_cache.add(link)
        else: self.checked_links_cache.remove(link)

    def on_check_upload(self, var, path):
        # [FIX] Logic Checkbox chọn video file
        if var.get(): 
            if path not in self.upload_selected_files:
                self.upload_selected_files.append(path)
        else: 
            if path in self.upload_selected_files:
                self.upload_selected_files.remove(path)
        self.lbl_sel.configure(text=f"CHỌN: {len(self.upload_selected_files)}")
    
    def on_change_cat_ops(self, cat):
        # [FIX] Update Sub theo Cat
        subs = list(self.settings["categories"][cat]["sub_categories"].keys())
        self.combo_sub_ops.configure(values=subs)
        if subs: 
            self.combo_sub_ops.set(subs[0])
            self.on_change_sub_ops(subs[0])
        else:
            self.combo_sub_ops.set("")
            self.entry_hash_ops.delete("1.0", "end")

    def on_change_sub_ops(self, sub):
        cat = self.combo_cat_ops.get()
        if cat and sub:
            d = self.settings["categories"][cat]["sub_categories"].get(sub, {})
            self.entry_hash_ops.delete("1.0", "end")
            self.entry_hash_ops.insert("1.0", ", ".join(d.get("hashtags", [])))
            # Reset view khi đổi ngách để tránh nhầm lẫn
            self.load_list(self.current_view_mode)

    # --- EDIT & UPLOAD ---
    def process_single_video(self, file_path, mode):
        self.upload_selected_files = [file_path] # Set tạm chọn 1 file
        if mode == "quick":
            self.log_message(f"⚡ Auto Edit 1 video: {os.path.basename(file_path)}")
            default_settings = {"speed": 1.05, "crop": 10, "gamma": 1.1, "mirror": False}
            self.run_processing_task(default_settings)
        else:
            self.log_message(f"🛠 Tùy chỉnh Edit: {os.path.basename(file_path)}")
            EditConfigDialog(self, self.run_processing_task)

    def run_processing_task(self, settings):
        self.btn_stop.configure(state="normal")
        threading.Thread(target=lambda: self._thread_process(settings)).start()

    def _thread_process(self, settings):
        try:
            new_files = self.backend.batch_process_videos(self.upload_selected_files, settings)
            self.after(0, lambda: self._post_process_ui(new_files))
        except Exception as e: self.after(0, lambda: messagebox.showerror("Lỗi", str(e)))

    def _post_process_ui(self, new_files):
        self.btn_stop.configure(state="disabled")
        if new_files:
            self.log_message(f"✅ Đã edit xong {len(new_files)} video.")
            if messagebox.askyesno("XONG", f"Đã edit xong {len(new_files)} video.\nChuyển sang tab ĐÃ SỬA & ĐĂNG để kiểm tra?"):
                self.load_list("EDITED")
            else: self.load_list("ORIGINAL") # Refresh tại chỗ
        else: messagebox.showwarning("!", "Có lỗi khi xử lý video")

    def upload_now(self):
        if not self.upload_selected_files:
             messagebox.showwarning("!", "Chưa chọn video!"); return
        self.log_message("🚀 Bấm nút Đăng Ngay...")
        self.run_task(lambda: self.exec_upload(None), cb=lambda: self.load_list("EDITED"))

    def upload_schedule(self):
        if not self.upload_selected_files:
             messagebox.showwarning("!", "Chưa chọn video!"); return
        self.log_message("📅 Bấm nút Lên Lịch...")
        ScheduleDialog(self, self.exec_upload, len(self.upload_selected_files))

    def exec_upload(self, times):
        cat = self.combo_cat_ops.get(); sub = self.combo_sub_ops.get()
        conf = self.settings["categories"][cat]["sub_categories"].get(sub, {})
        self.backend.run_uploader(times, self.upload_selected_files, cat, sub, conf)
        self.after(0, lambda: self.on_upload_complete(times))

    def on_upload_complete(self, times):
        if messagebox.askyesno("XONG", "Mở Content Library kiểm tra?"):
            webbrowser.open("https://www.facebook.com/professional_dashboard/content/content_library")
        self.load_list("EDITED")

    def open_review_for_item(self, item):
        orig = item.get("original_path")
        edited = item.get("path")
        if orig and edited: 
            self.log_message("👁 Mở Review video...")
            ReviewDialog(self, orig, edited)
        else: messagebox.showerror("Lỗi", "Không tìm thấy file gốc để so sánh!")

    def remove_from_queue(self, link):
        if link in self.download_queue_items:
            try: self.download_queue_items[link]["card"].destroy()
            except: pass
            del self.download_queue_items[link]
            if link in self.checked_links_cache: self.checked_links_cache.remove(link)

    # --- BOILERPLATE ---
    def run_task(self, func, cb=None):
        self.btn_stop.configure(state="normal")
        threading.Thread(target=lambda: [func(), self.after(0, lambda: self.reset_ui(cb))], daemon=True).start()
    def reset_ui(self, cb):
        self.btn_stop.configure(state="disabled"); self.log_message("✅ Tác vụ hoàn tất.")
        if cb: cb()
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
    def open_video_folder(self): self.backend.open_local_path(str(self.backend.get_paths(self.combo_cat_ops.get(), self.combo_sub_ops.get())["video_dir"]))
    def stop_process(self): self.backend.stop_flag = True
    def refresh_cat_list_ui(self): self.settings_ui.refresh_cat_list_ui()
    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(self.settings, f, ensure_ascii=False, indent=4)
    def add_item(self, t): self.settings_ui.add_item(t)
    def delete_item(self, t): self.settings_ui.delete_item(t)
    def import_txt(self, t): self.settings_ui.import_txt(t)
    def verify_fanpage_connection(self): self.settings_ui.verify_fanpage_connection()
    def get_cookie_action(self): self.start_cookie_flow()
    def single_schedule(self, path): ScheduleDialog(self, lambda times: self.exec_single_upload(path, times), 1)
    def exec_single_upload(self, path, times):
        cat = self.combo_cat_ops.get(); sub = self.combo_sub_ops.get()
        conf = self.settings["categories"][cat]["sub_categories"].get(sub, {})
        self.backend.run_uploader(times, [path], cat, sub, conf)
        self.after(0, lambda: self.on_upload_complete(times))