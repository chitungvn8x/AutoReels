import customtkinter as ctk
from PIL import Image
from datetime import datetime
import os
import webbrowser

class VideoCardFactory:
    def __init__(self, app_ref):
        self.app = app_ref
        self.HAS_PIL = True

    def _bind_recursive(self, widget, item, menu_type):
        try: widget.bind("<Button-3>", lambda event: self.app.show_context_menu(event, item, menu_type))
        except: pass
        for child in widget.winfo_children(): self._bind_recursive(child, item, menu_type)

    def create_queue_card(self, parent, item, initial_check=False):
        # Card Chờ Tải
        f_card = ctk.CTkFrame(parent, height=100, fg_color="#2B2B2B")
        f_card.pack(fill="x", pady=2, padx=5)
        # [FIX] Cố định chiều cao thẻ chờ tải
        f_card.pack_propagate(False)

        var_chk = ctk.BooleanVar(value=initial_check)
        chk = ctk.CTkCheckBox(f_card, text="", variable=var_chk, width=20,
                              command=lambda: self.app.on_check_dl(var_chk, item["data"]))
        chk.pack(side="left", padx=5)

        # Thumbnail
        f_thumb = ctk.CTkFrame(f_card, width=60, height=90, fg_color="#111")
        f_thumb.pack(side="left", fill="y", padx=2, pady=2)
        f_thumb.pack_propagate(False)
        lbl_thumb = ctk.CTkLabel(f_thumb, text="TIKTOK", font=("Arial", 8), text_color="gray")
        lbl_thumb.pack(expand=True, fill="both")

        if item.get("thumb") and os.path.exists(item.get("thumb")):
            try:
                # Resize ảnh cho vừa khít
                img = ctk.CTkImage(Image.open(item.get("thumb")), size=(60, 96))
                lbl_thumb.configure(image=img, text="")
            except: pass

        f_info = ctk.CTkFrame(f_card, fg_color="transparent")
        f_info.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        link = item["data"]
        short_link = link[:40] + "..." if len(link) > 40 else link
        ctk.CTkLabel(f_info, text=short_link, font=("Arial", 12, "bold"), anchor="w").pack(fill="x")

        lbl_status = ctk.CTkLabel(f_info, text=item.get("status", "Chờ tải"), font=("Arial", 11), text_color="orange", anchor="w")
        lbl_status.pack(fill="x")

        prog = ctk.CTkProgressBar(f_info, height=5); prog.set(0); prog.pack_forget()

        f_actions = ctk.CTkFrame(f_card, fg_color="transparent")
        f_actions.pack(side="right", padx=5, fill="y")
        ctk.CTkButton(f_actions, text="⬇ Tải", width=50, height=25, fg_color="#2980B9", command=lambda: self.app.run_single_download(link)).pack(pady=2)
        ctk.CTkButton(f_actions, text="🌐 Xem", width=50, height=25, fg_color="#555", command=lambda: webbrowser.open(link)).pack(pady=2)
        ctk.CTkButton(f_actions, text="🗑", width=30, height=25, fg_color="#C0392B", command=lambda: self.app.remove_from_queue(link)).pack(pady=2)

        self._bind_recursive(f_card, item, "PENDING")
        return {"card": f_card, "lbl": lbl_status, "prog": prog}

    def create_upload_card(self, parent, item):
        # [UPDATED] Card Video - Cố định chiều cao để Thumbnail tràn viền chuẩn
        card_height = 120
        f_card = ctk.CTkFrame(parent, height=card_height, fg_color="#2B2B2B")
        f_card.pack(fill="x", pady=4, padx=5)

        # [QUAN TRỌNG] Cố định chiều cao frame, không cho text đẩy giãn frame
        f_card.pack_propagate(False)

        # Checkbox
        is_checked = item["path"] in self.app.upload_selected_files
        var_chk = ctk.BooleanVar(value=is_checked)
        chk = ctk.CTkCheckBox(f_card, text="", variable=var_chk, width=20,
                              command=lambda: self.app.on_check_upload(var_chk, item["path"]))
        chk.pack(side="left", padx=8)

        # Full-height Thumbnail
        f_thumb = ctk.CTkFrame(f_card, width=80, fg_color="black")
        f_thumb.pack(side="left", fill="y", padx=0, pady=0)
        f_thumb.pack_propagate(False)

        lbl_img = ctk.CTkLabel(f_thumb, text="NO IMG", font=("Arial", 10))
        lbl_img.pack(expand=True, fill="both")

        if item["thumb"] and os.path.exists(item["thumb"]):
            try:
                img_pil = Image.open(item["thumb"])
                # Ép ảnh resize đúng bằng chiều cao card
                img = ctk.CTkImage(img_pil, size=(80, card_height))
                lbl_img.configure(image=img, text="")
            except: pass

        # Info Area
        f_content = ctk.CTkFrame(f_card, fg_color="transparent")
        f_content.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        name = item["name"]
        if len(name) > 40: name = name[:40] + "..."
        ctk.CTkLabel(f_content, text=name, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")

        mtime_str = datetime.fromtimestamp(item["mtime"]).strftime('%d/%m %H:%M')
        ctk.CTkLabel(f_content, text=f"📅 {mtime_str}", font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x")

        status_text = item['status']
        st_color = "gray"
        if "ĐÃ ĐĂNG" in status_text: st_color = "#2ECC71"
        elif "Lịch" in status_text: st_color = "#F1C40F"
        elif "CHƯA" in status_text: st_color = "#E67E22"
        ctk.CTkLabel(f_content, text=status_text, text_color=st_color, font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(0, 5))

        # Right-Side Buttons
        f_btns = ctk.CTkFrame(f_card, fg_color="transparent")
        f_btns.pack(side="right", padx=10, fill="y")

        f_btns.grid_columnconfigure(0, weight=1)
        f_btns.grid_rowconfigure(0, weight=1); f_btns.grid_rowconfigure(3, weight=1)

        if item.get("type") == "ORIGINAL":
            ctk.CTkButton(f_btns, text="⚡ Auto Edit", width=100, height=28, fg_color="#D35400",
                          command=lambda: self.app.process_single_video(item["path"], "quick")).grid(row=1, pady=2)
            ctk.CTkButton(f_btns, text="🛠 Tùy chỉnh", width=100, height=28, fg_color="#E67E22",
                          command=lambda: self.app.process_single_video(item["path"], "custom")).grid(row=2, pady=2)
        else:
            ctk.CTkButton(f_btns, text="👁 Review So Sánh", width=120, height=28, fg_color="#8E44AD",
                          command=lambda: self.app.open_review_for_item(item)).grid(row=1, pady=2)

        menu_type = "ORIGINAL" if item.get("type") == "ORIGINAL" else "EDITED"
        self._bind_recursive(f_card, item, menu_type)
        return f_card