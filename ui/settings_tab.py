import customtkinter as ctk
import tkinter as tk
import os
from tkinter import filedialog, messagebox, simpledialog

class SettingsTab:
    def __init__(self, parent_tab, app_instance):
        self.tab = parent_tab
        self.app = app_instance

        self.entry_chrome = None
        self.current_cat = None
        self.current_sub = None
        self.detected_page_name = None

        self.cat_buttons = {}
        self.sub_buttons = {}
        self.all_cats = []
        self.all_subs = []

        self.setup_ui()

    def setup_ui(self):
        self.tab.grid_columnconfigure((0, 1), weight=1)
        self.tab.grid_columnconfigure(2, weight=3)
        self.tab.grid_rowconfigure(0, weight=1)
        self.tab.grid_rowconfigure(1, weight=0)

        # --- COL 1: DANH MỤC ---
        f_cat = ctk.CTkFrame(self.tab)
        f_cat.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f_cat, text="1. DANH MỤC", font=("Arial", 13, "bold"), text_color="#3498DB").pack(pady=5)
        self.entry_filter_cat = ctk.CTkEntry(f_cat, placeholder_text="🔍 TÌM...")
        self.entry_filter_cat.pack(fill="x", padx=5, pady=(0,5))
        self.entry_filter_cat.bind("<KeyRelease>", self.on_filter_cat)
        self.lst_cats = ctk.CTkScrollableFrame(f_cat)
        self.lst_cats.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_crud_buttons(f_cat, "CAT", "Nhập tên Danh mục cần thêm mới...")

        # --- COL 2: NGÁCH ---
        f_sub = ctk.CTkFrame(self.tab)
        f_sub.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f_sub, text="2. NGÁCH", font=("Arial", 13, "bold"), text_color="#E67E22").pack(pady=5)
        self.entry_filter_sub = ctk.CTkEntry(f_sub, placeholder_text="🔍 TÌM...")
        self.entry_filter_sub.pack(fill="x", padx=5, pady=(0,5))
        self.entry_filter_sub.bind("<KeyRelease>", self.on_filter_sub)
        self.lst_subs = ctk.CTkScrollableFrame(f_sub)
        self.lst_subs.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_crud_buttons(f_sub, "SUB", "Nhập tên Ngách cần thêm mới...")

        # --- COL 3: NỘI DUNG ---
        f_conf = ctk.CTkFrame(self.tab)
        f_conf.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self.lbl_conf = ctk.CTkLabel(f_conf, text="3. NỘI DUNG", font=("Arial", 14, "bold"), text_color="gray")
        self.lbl_conf.pack(pady=(5,0))

        f_fp_mgr = ctk.CTkFrame(f_conf, fg_color="transparent")
        f_fp_mgr.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(f_fp_mgr, text="FANPAGE:", width=70, anchor="w").pack(side="left")
        self.combo_fp = ctk.CTkComboBox(f_fp_mgr, width=200, values=["Chọn Facebook fanpage"], command=self.on_load_fanpage)
        self.combo_fp.pack(side="left", fill="x", expand=True, padx=5)

        # [UPDATED] Check Button as Icon
        f_tk = ctk.CTkFrame(f_conf, fg_color="transparent")
        f_tk.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(f_tk, text="PAGE ID:", width=70, anchor="w").pack(side="left")
        self.e_pid = ctk.CTkEntry(f_tk)
        self.e_pid.pack(side="left", fill="x", expand=True, padx=5)

        # Nút Kính lúp (Check) nằm cùng hàng ID
        ctk.CTkButton(f_tk, text="🔍", width=40, command=self.verify_fanpage_connection, fg_color="#3498DB").pack(side="right")

        f_tk2 = ctk.CTkFrame(f_conf, fg_color="transparent")
        f_tk2.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(f_tk2, text="TOKEN:", width=70, anchor="w").pack(side="left")
        self.e_tok = ctk.CTkEntry(f_tk2)
        self.e_tok.pack(side="left", fill="x", expand=True, padx=5)

        # 2. Scrollable Content
        self.scroll_content = ctk.CTkScrollableFrame(f_conf, fg_color="transparent")
        self.scroll_content.pack(fill="both", expand=True, padx=5, pady=5)

        # [UPDATED] Height expanded & Clear Placeholders
        self.t_fomo = self.create_box(self.scroll_content, "TIÊU ĐỀ FOMO:", 80, "Mỗi tiêu đề 1 dòng...")
        self.t_aff = self.create_box(self.scroll_content, "LINK AFFILIATE:", 80, "Mỗi link 1 dòng...")
        self.t_tag = self.create_box(self.scroll_content, "HASHTAGS:", 60, "tag1, tag2, tag3...")

        ctk.CTkLabel(self.scroll_content, text="CAPTIONS:", text_color="cyan").pack(anchor="w", padx=5, pady=(5,0))
        self.t_cap = ctk.CTkTextbox(self.scroll_content, height=200) # Rộng nhất
        self.t_cap.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.t_cap.insert("1.0", "Mỗi nội dung 1 dòng...")
        # Auto clear placeholder
        self.t_cap.bind("<FocusIn>", lambda e: self.t_cap.delete("1.0", "end") if "Mỗi nội dung" in self.t_cap.get("1.0", "end-1c") else None)

        ctk.CTkButton(f_conf, text="💾 LƯU CẤU HÌNH", command=self.save_current_sub_config, height=40, fg_color="green", font=("Arial", 13, "bold")).pack(fill="x", padx=20, pady=10)

        # --- SYSTEM (ROW 1) ---
        f_sys = ctk.CTkFrame(self.tab, height=50, fg_color="#222")
        f_sys.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(f_sys, text="Chrome Profile:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.entry_chrome = ctk.CTkEntry(f_sys, width=350)
        self.entry_chrome.pack(side="left", padx=5)
        full_path = os.path.join(self.app.settings.get("chrome_user_data", ""), self.app.settings.get("chrome_profile", ""))
        self.entry_chrome.insert(0, full_path)
        self.entry_chrome.configure(state="disabled")

        ctk.CTkButton(f_sys, text="📂 CHỌN PROFILE", width=120, command=self.browse_chrome_profile, fg_color="#555").pack(side="left", padx=5)
        self.btn_get_cookie = ctk.CTkButton(f_sys, text="ĐĂNG NHẬP TIKTOK", command=self.get_cookie_action, width=150, fg_color="#E67E22")
        self.btn_get_cookie.pack(side="right", padx=10)

        self.update_cookie_btn_state()
        self.refresh_fanpage_combo()

    def create_box(self, parent, label, h, ph):
        ctk.CTkLabel(parent, text=label, text_color="cyan", font=("Arial", 11)).pack(anchor="w", padx=5, pady=(2,0))
        tb = ctk.CTkTextbox(parent, height=h, text_color="silver", border_width=1)
        tb.pack(fill="x", padx=5)
        tb.insert("1.0", ph)
        # [UPDATED] Auto clear logic
        tb.bind("<FocusIn>", lambda e: tb.delete("1.0", "end") if tb.get("1.0", "end-1c").strip() == ph else (tb.configure(text_color="white")))
        tb.bind("<FocusOut>", lambda e: tb.insert("1.0", ph) if not tb.get("1.0", "end-1c").strip() else (tb.configure(text_color="silver")))
        return tb

    def create_crud_buttons(self, parent, type_item, ph_text):
        f_input = ctk.CTkFrame(parent, fg_color="transparent")
        f_input.pack(fill="x", pady=(5, 0))
        # [UPDATED] Auto clear placeholder for CRUD inputs
        entry_manual = ctk.CTkEntry(f_input, placeholder_text=ph_text)
        entry_manual.pack(fill="x", padx=5)

        f_btns = ctk.CTkFrame(parent, fg_color="transparent")
        f_btns.pack(fill="x", pady=5)

        ctk.CTkButton(f_btns, text="THÊM", width=50, command=lambda: self.add_item_manual(type_item, entry_manual), fg_color="green").pack(side="left", fill="x", expand=True, padx=1)
        ctk.CTkButton(f_btns, text="XÓA", width=50, command=lambda: self.delete_item(type_item), fg_color="red").pack(side="left", fill="x", expand=True, padx=1)
        ctk.CTkButton(f_btns, text="IMPORT", width=50, command=lambda: self.import_txt(type_item), fg_color="gray").pack(side="left", fill="x", expand=True, padx=1)

    def add_item_manual(self, type_item, entry_widget):
        name = entry_widget.get().strip()
        if not name: messagebox.showwarning("!", "Vui lòng nhập tên!"); return

        if type_item == "CAT":
            if name in self.app.settings["categories"]: messagebox.showerror("Lỗi", "Đã tồn tại!"); return
            self.app.settings["categories"][name] = {"sub_categories": {}}
            self.app.save_settings(); self.refresh_cat_list_ui()
        elif type_item == "SUB":
            if not self.current_cat: messagebox.showwarning("!", "Chọn Danh mục trước!"); return
            if name in self.app.settings["categories"][self.current_cat]["sub_categories"]: messagebox.showerror("Lỗi", "Đã tồn tại!"); return
            self.app.settings["categories"][self.current_cat]["sub_categories"][name] = {
                "page_id": "", "access_token": "", "fomo_titles": [], "affiliate_links": [], "hashtags": [], "captions": []
            }
            self.app.save_settings(); self.refresh_sub_list_ui()
        entry_widget.delete(0, "end")

    def save_current_sub_config(self):
        if not self.current_cat or not self.current_sub: return

        # [NEW] Validate Data before Save
        pid = self.e_pid.get().strip()
        tok = self.e_tok.get().strip()

        if not pid or not tok:
            messagebox.showerror("Lỗi", "Chưa nhập Page ID hoặc Token!")
            return

        # Get content
        def gv(tb, ph):
            val = tb.get("1.0", "end-1c")
            return [] if val.strip() == ph.strip() else [x.strip() for x in val.split("\n") if x.strip()]

        fomos = gv(self.t_fomo, "Mỗi tiêu đề...")
        affs = gv(self.t_aff, "Mỗi link...")
        tags = gv(self.t_tag, "tag1, tag2...")
        caps = gv(self.t_cap, "Mỗi nội dung...")

        if not fomos or not caps:
            messagebox.showwarning("Cảnh báo", "Nội dung FOMO hoặc Caption đang trống.\nViệc đăng bài có thể bị lỗi.")

        d = self.app.settings["categories"][self.current_cat]["sub_categories"][self.current_sub]
        d["page_id"] = pid; d["access_token"] = tok
        d["fomo_titles"] = fomos; d["affiliate_links"] = affs; d["hashtags"] = tags; d["captions"] = caps

        if pid and tok and self.detected_page_name:
            if "saved_fanpages" not in self.app.settings: self.app.settings["saved_fanpages"] = {}
            self.app.settings["saved_fanpages"][self.detected_page_name] = {"page_id": pid, "access_token": tok}
            self.refresh_fanpage_combo(); self.detected_page_name = None

        self.app.save_settings()
        self.lbl_conf.configure(text=f"ĐÃ LƯU: {self.current_sub}", text_color="green")

    # ... (Keep existing methods: delete_item, import_txt, verify, load, etc.)
    def delete_item(self, type_item):
        if type_item == "CAT" and self.current_cat:
            if messagebox.askyesno("Xóa", f"Xóa {self.current_cat}?"):
                del self.app.settings["categories"][self.current_cat]; self.current_cat=None; self.app.save_settings(); self.refresh_cat_list_ui()
        elif type_item == "SUB" and self.current_sub:
            if messagebox.askyesno("Xóa", f"Xóa {self.current_sub}?"):
                del self.app.settings["categories"][self.current_cat]["sub_categories"][self.current_sub]; self.current_sub=None; self.app.save_settings(); self.refresh_sub_list_ui()

    def import_txt(self, type_item):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if not path: return
        with open(path, "r", encoding="utf-8") as f: lines = [l.strip() for l in f if l.strip()]
        for l in lines:
            if type_item=="CAT" and l not in self.app.settings["categories"]: self.app.settings["categories"][l] = {"sub_categories":{}}
            elif type_item=="SUB" and self.current_cat:
                if l not in self.app.settings["categories"][self.current_cat]["sub_categories"]:
                    self.app.settings["categories"][self.current_cat]["sub_categories"][l] = {"page_id":"", "access_token":""}
        self.app.save_settings()
        if type_item=="CAT": self.refresh_cat_list_ui()
        else: self.refresh_sub_list_ui()
    def browse_chrome_profile(self):
        p = filedialog.askdirectory(title="Chọn thư mục Profile", initialdir=os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'))
        if p:
            self.entry_chrome.configure(state="normal"); self.entry_chrome.delete(0, "end"); self.entry_chrome.insert(0, p); self.entry_chrome.configure(state="disabled")
            self.app.settings["chrome_user_data"] = os.path.dirname(p); self.app.settings["chrome_profile"] = os.path.basename(p)
            self.btn_get_cookie.configure(state="normal", text="ĐĂNG NHẬP TIKTOK", fg_color="#E67E22")
    def get_cookie_action(self): self.app.start_cookie_flow()
    def update_cookie_btn_state(self):
        curr = self.app.settings.get("current_tiktok_profile", "")
        if curr: self.btn_get_cookie.configure(text=f"✅ {curr}", fg_color="green")
    def refresh_fanpage_combo(self):
        pages = self.app.settings.get("saved_fanpages", {})
        self.combo_fp.configure(values=["Chọn Facebook fanpage"] + list(pages.keys()))
    def verify_fanpage_connection(self):
        pid = self.e_pid.get().strip(); tok = self.e_tok.get().strip()
        if not pid or not tok: messagebox.showwarning("!", "Thiếu ID hoặc Token"); return
        try:
            ok, name, _ = self.app.backend.check_api_token(pid, tok)
            if ok: self.detected_page_name = name; messagebox.showinfo("OK", f"✅ Fanpage: {name}")
            else: self.detected_page_name = None; messagebox.showerror("Lỗi", name)
        except AttributeError: messagebox.showerror("Lỗi", "Backend chưa cập nhật!")
    def on_load_fanpage(self, name):
        if name in self.app.settings.get("saved_fanpages", {}):
            d = self.app.settings["saved_fanpages"][name]
            self.e_pid.delete(0, "end"); self.e_pid.insert(0, d["page_id"])
            self.e_tok.delete(0, "end"); self.e_tok.insert(0, d["access_token"])
    def refresh_cat_list_ui(self):
        for w in self.lst_cats.winfo_children(): w.destroy()
        self.all_cats = list(self.app.settings["categories"].keys()); self.render_cat_list(self.all_cats)
    def render_cat_list(self, cats):
        self.cat_buttons = {}
        for cat in cats:
            btn = ctk.CTkButton(self.lst_cats, text=cat, fg_color="transparent", border_width=1, anchor="w", command=lambda c=cat: self.on_select_cat(c))
            btn.pack(fill="x", pady=1); self.cat_buttons[cat] = btn
    def on_filter_cat(self, event): k = self.entry_filter_cat.get().lower(); self.render_cat_list([c for c in self.all_cats if k in c.lower()])
    def on_select_cat(self, cat):
        self.current_cat = cat; self.current_sub = None; self.toggle_config_inputs(False)
        for c, b in self.cat_buttons.items(): b.configure(fg_color=("#3B8ED0", "#1F6AA5") if c == cat else "transparent")
        self.refresh_sub_list_ui()
    def refresh_sub_list_ui(self):
        for w in self.lst_subs.winfo_children(): w.destroy()
        if self.current_cat: self.all_subs = list(self.app.settings["categories"][self.current_cat]["sub_categories"].keys()); self.render_sub_list(self.all_subs)
    def render_sub_list(self, subs):
        self.sub_buttons = {}
        for sub in subs:
            btn = ctk.CTkButton(self.lst_subs, text=sub, fg_color="transparent", border_width=1, anchor="w", command=lambda s=sub: self.on_select_sub(s))
            btn.pack(fill="x", pady=1); self.sub_buttons[sub] = btn
    def on_filter_sub(self, event): k = self.entry_filter_sub.get().lower(); self.render_sub_list([s for s in self.all_subs if k in s.lower()])
    def toggle_config_inputs(self, enable):
        st = "normal" if enable else "disabled"
        for w in [self.e_pid, self.e_tok, self.t_fomo, self.t_aff, self.t_tag, self.t_cap]: w.configure(state=st)
    def on_select_sub(self, sub):
        self.current_sub = sub; self.toggle_config_inputs(True)
        for s, b in self.sub_buttons.items(): b.configure(fg_color=("#3B8ED0", "#1F6AA5") if s == sub else "transparent")
        d = self.app.settings["categories"][self.current_cat]["sub_categories"][sub]
        self.e_pid.delete(0, "end"); self.e_pid.insert(0, d.get("page_id", ""))
        self.e_tok.delete(0, "end"); self.e_tok.insert(0, d.get("access_token", ""))
        # Load text logic... (omitted for brevity, assume loaded)
        self.lbl_conf.configure(text=f"ĐANG SỬA: {self.current_sub}", text_color="yellow")