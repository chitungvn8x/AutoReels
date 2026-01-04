import customtkinter as ctk
import os
from ui.player import SimpleVideoPlayer

class ReviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, original_path, edited_path):
        super().__init__(parent)
        self.title("REVIEW SO SÁNH: TRƯỚC VÀ SAU KHI EDIT")
        self.geometry("900x600")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.update_idletasks()
        w, h = 900, 600
        x = (self.winfo_screenwidth()//2 - w//2)
        y = (self.winfo_screenheight()//2 - h//2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.original_path = original_path
        self.edited_path = edited_path

        f_head = ctk.CTkFrame(self, fg_color="transparent")
        f_head.pack(fill="x", pady=5)
        ctk.CTkLabel(f_head, text="VIDEO GỐC", font=("Arial", 14, "bold"), text_color="#ccc").pack(side="left", expand=True)
        ctk.CTkLabel(f_head, text="VIDEO ĐÃ SỬA", font=("Arial", 14, "bold"), text_color="#00FF00").pack(side="right", expand=True)

        f_main = ctk.CTkFrame(self)
        f_main.pack(fill="both", expand=True, padx=10)

        self.p_orig = SimpleVideoPlayer(f_main, width=420, height=450)
        self.p_orig.pack(side="left", padx=5, pady=5)

        self.p_edit = SimpleVideoPlayer(f_main, width=420, height=450)
        self.p_edit.pack(side="right", padx=5, pady=5)

        f_ctrl = ctk.CTkFrame(self)
        f_ctrl.pack(fill="x", pady=10)

        ctk.CTkButton(f_ctrl, text="▶ PHÁT CẢ HAI", command=self.play_both, fg_color="green", width=200).pack(side="left", padx=20, expand=True)
        ctk.CTkButton(f_ctrl, text="⏹ DỪNG", command=self.stop_both, fg_color="red", width=100).pack(side="left", padx=20, expand=True)
        ctk.CTkButton(f_ctrl, text="ĐÓNG", command=self.on_close, fg_color="gray").pack(side="right", padx=20)

        self.after(200, self.load_videos)

    def load_videos(self):
        if self.original_path and os.path.exists(self.original_path):
            self.p_orig.load_video(self.original_path)
        if self.edited_path and os.path.exists(self.edited_path):
            self.p_edit.load_video(self.edited_path)

    def play_both(self):
        self.p_orig.play()
        self.p_edit.play()

    def stop_both(self):
        self.p_orig.stop()
        self.p_edit.stop()

    def on_close(self):
        self.stop_both()
        self.destroy()