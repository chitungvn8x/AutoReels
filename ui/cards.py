import customtkinter as ctk
from PIL import Image
from datetime import datetime
import os
import webbrowser # Để mở link gốc

class VideoCardFactory:
    def __init__(self, app_ref):
        self.app = app_ref
        self.HAS_PIL = True

    def _bind_recursive(self, widget, item, menu_type):
        """Gán sự kiện chuột phải cho widget và tất cả con của nó"""
        # Bấm chuột phải (Button-3 trên Windows, Button-2 trên MacOS)
        widget.bind("<Button-3>", lambda event: self.app.show_context_menu(event, item, menu_type))
        for child in widget.winfo_children():
            self._bind_recursive(child, item, menu_type)

    def create_queue_card(self, parent, item, initial_check=False):
        """Card Chờ Tải"""
        f_card = ctk.CTkFrame(parent, height=80, fg_color="#2B2B2B")
        f_card.pack(fill="x", pady=2, padx=5)
        
        # Checkbox
        var_chk = ctk.BooleanVar(value=initial_check)
        chk = ctk.CTkCheckBox(f_card, text="", variable=var_chk, width=20, 
                              command=lambda: self.app.on_check_dl(var_chk, item["data"]))
        chk.pack(side="left", padx=10)

        # Info Area
        f_info = ctk.CTkFrame(f_card, fg_color="transparent")
        f_info.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        link = item["data"]
        short_link = link[:60] + "..." if len(link) > 60 else link
        ctk.CTkLabel(f_info, text=short_link, font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        
        scan_time = item.get("scan_time", "")
        if scan_time:
            ctk.CTkLabel(f_info, text=f"🕒 {scan_time}", font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x")
            
        # Status & Progress
        f_status = ctk.CTkFrame(f_card, fg_color="transparent")
        f_status.pack(side="right", padx=10)
        
        lbl_status = ctk.CTkLabel(f_status, text=item.get("status", "Chờ tải"), width=100, text_color="orange")
        lbl_status.pack(anchor="e")
        
        # [PHỤC HỒI] Progress Bar
        prog = ctk.CTkProgressBar(f_status, width=100, height=6)
        prog.set(0)
        # Mặc định ẩn, chỉ hiện khi đang tải
        prog.pack_forget() 

        btn_del = ctk.CTkButton(f_card, text="🗑", width=30, fg_color="#C0392B", 
                                command=lambda: self.app.remove_from_queue(link))
        btn_del.pack(side="right", padx=5)

        # [UPDATE] Bind menu chuột phải toàn cục
        self._bind_recursive(f_card, item, "PENDING")

        return {"card": f_card, "lbl": lbl_status, "prog": prog}

    def create_upload_card(self, parent, item):
        """Card Video (Gốc/Edit)"""
        # [UPDATE] Tăng chiều cao, Padding=0 cho thumbnail tràn
        f_card = ctk.CTkFrame(parent, height=130, fg_color="#2B2B2B")
        f_card.pack(fill="x", pady=4, padx=5)

        # Checkbox
        is_checked = item["path"] in self.app.upload_selected_files
        var_chk = ctk.BooleanVar(value=is_checked)
        chk = ctk.CTkCheckBox(f_card, text="", variable=var_chk, width=20,
                              command=lambda: self.app.on_check_upload(var_chk, item["path"]))
        chk.pack(side="left", padx=10, anchor="center")

        # [UPDATE] Thumbnail Tràn Viền (fill='y', pady=0)
        f_thumb = ctk.CTkFrame(f_card, width=90, fg_color="black")
        f_thumb.pack(side="left", fill="y", padx=0, pady=0) 
        f_thumb.pack_propagate(False)
        
        lbl_img = ctk.CTkLabel(f_thumb, text="No IMG")
        lbl_img.pack(expand=True, fill="both")
        
        if item["thumb"] and self.HAS_PIL and os.path.exists(item["thumb"]):
            try:
                # Load ảnh lớn hơn chút để đẹp
                img = ctk.CTkImage(Image.open(item["thumb"]), size=(90, 130))
                lbl_img.configure(image=img, text="")
            except: pass

        # Content Area
        f_content = ctk.CTkFrame(f_card, fg_color="transparent")
        f_content.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(f_content, text=item["name"], font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        mtime_str = datetime.fromtimestamp(item["mtime"]).strftime('%d/%m %H:%M')
        ctk.CTkLabel(f_content, text=f"📅 {mtime_str}", font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x")

        status_text = item['status']
        st_color = "gray"
        if "ĐÃ ĐĂNG" in status_text: st_color = "green"
        elif "Lên lịch" in status_text: st_color = "yellow"
        elif "Đã sửa" in status_text: st_color = "green"
        elif "CHƯA SỬA" in status_text: st_color = "orange"
        
        ctk.CTkLabel(f_content, text=status_text, text_color=st_color, font=("Arial", 11, "bold"), anchor="w").pack(fill="x", pady=(2,5))

        # [UPDATE] Nút bấm nằm dưới cùng
        f_btns = ctk.CTkFrame(f_content, fg_color="transparent")
        f_btns.pack(side="bottom", fill="x", pady=5)

        if item.get("type") == "ORIGINAL":
            ctk.CTkButton(f_btns, text="⚡ Auto Edit", width=90, height=25, fg_color="#D35400",
                          command=lambda: self.app.process_single_video(item["path"], "quick")).pack(side="left", padx=(0, 5))
            ctk.CTkButton(f_btns, text="🛠 Tùy chỉnh", width=90, height=25, fg_color="#E67E22",
                          command=lambda: self.app.process_single_video(item["path"], "custom")).pack(side="left")
        else:
            ctk.CTkButton(f_btns, text="👁 Review", width=100, height=25, fg_color="#8E44AD",
                          command=lambda: self.app.open_review_for_item(item)).pack(side="left")

        # [UPDATE] Bind menu chuột phải toàn cục
        menu_type = "ORIGINAL" if item.get("type") == "ORIGINAL" else "EDITED"
        self._bind_recursive(f_card, item, menu_type)

        return f_card