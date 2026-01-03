import customtkinter as ctk
from tkinter import messagebox

class EditConfigDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Cấu hình & Anti-Fingerprint")
        self.geometry("450x600")
        self.resizable(False, False)

        # [FIX] Center Window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        self.attributes("-topmost", True)
        self.grab_set()

        # --- UI ---
        ctk.CTkLabel(self, text="CẤU HÌNH CHỈNH SỬA", font=("Arial", 16, "bold")).pack(pady=10)

        # 1. Speed
        f1 = ctk.CTkFrame(self, fg_color="transparent"); f1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f1, text="Tốc độ (Speed):").pack(side="left")
        self.lbl_speed = ctk.CTkLabel(f1, text="1.05x", text_color="cyan")
        self.lbl_speed.pack(side="right")
        self.slider_speed = ctk.CTkSlider(self, from_=1.0, to=1.3, number_of_steps=30,
                                          command=lambda v: self.lbl_speed.configure(text=f"{round(v,2)}x"))
        self.slider_speed.set(1.05); self.slider_speed.pack(fill="x", padx=20)

        # 2. Crop
        f2 = ctk.CTkFrame(self, fg_color="transparent"); f2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f2, text="Cắt viền (px):").pack(side="left")
        self.entry_crop = ctk.CTkEntry(f2, width=60); self.entry_crop.pack(side="right")
        self.entry_crop.insert(0, "10")

        # 3. Anti-Fingerprint Group
        ctk.CTkLabel(self, text="--- ANTI-FINGERPRINT ---", font=("Arial", 13, "bold"), text_color="orange").pack(pady=(20, 5))

        # Cut Start/End
        f3 = ctk.CTkFrame(self, fg_color="transparent"); f3.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(f3, text="Cắt đầu (giây):").pack(side="left")
        self.e_cut_start = ctk.CTkEntry(f3, width=50); self.e_cut_start.pack(side="right"); self.e_cut_start.insert(0, "0.5")

        f4 = ctk.CTkFrame(self, fg_color="transparent"); f4.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(f4, text="Cắt đuôi (giây):").pack(side="left")
        self.e_cut_end = ctk.CTkEntry(f4, width=50); self.e_cut_end.pack(side="right"); self.e_cut_end.insert(0, "0.5")

        # Mirror Checkbox
        self.chk_mirror = ctk.CTkCheckBox(self, text="Lật Video (Mirror X)")
        self.chk_mirror.pack(pady=10)

        # Confirm
        ctk.CTkButton(self, text="ÁP DỤNG & XỬ LÝ", command=self.on_confirm, height=40, fg_color="green").pack(fill="x", padx=20, pady=20)

    def on_confirm(self):
        try:
            settings = {
                "speed": round(self.slider_speed.get(), 2),
                "crop": int(self.entry_crop.get()),
                "gamma": 1.1,
                "mirror": self.chk_mirror.get(),
                "cut_start": float(self.e_cut_start.get()),
                "cut_end": float(self.e_cut_end.get())
            }
            self.destroy()
            self.callback(settings)
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ!")