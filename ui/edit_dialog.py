import customtkinter as ctk
from tkinter import filedialog, Canvas
from PIL import Image, ImageTk
import os

class EditConfigDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Cấu hình & Vị trí Logo")
        self.geometry("500x700")
        self.resizable(False, False)
        
        # [FIX] Đưa form lên trên cùng để không bị che
        self.attributes("-topmost", True)
        self.grab_set() 
        self.focus_force()

        self.logo_path = None
        # Vị trí logo mặc định (tương đối 0.0 - 1.0)
        self.logo_rel_x = 0.8
        self.logo_rel_y = 0.1
        self.preview_width = 400
        self.preview_height = 225 # Tỷ lệ 16:9

        # Scroll frame
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. PREVIEW KÉO THẢ LOGO
        ctk.CTkLabel(self.scroll, text="📍 KÉO THẢ ĐIỂM ĐỎ ĐỂ CHỈNH VỊ TRÍ LOGO", text_color="orange", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Canvas mô phỏng
        self.canvas = Canvas(self.scroll, width=self.preview_width, height=self.preview_height, bg="black", highlightthickness=0)
        self.canvas.pack(pady=5)
        
        # Vẽ khung video giả lập
        self.canvas.create_text(self.preview_width/2, self.preview_height/2, text="VIDEO PREVIEW AREA", fill="#333", font=("Arial", 16))
        
        # Vẽ điểm logo (Đại diện)
        self.logo_dot = self.canvas.create_oval(0, 0, 20, 20, fill="red", outline="white", width=2)
        self.update_canvas_dot()

        # Bind sự kiện kéo thả
        self.canvas.tag_bind(self.logo_dot, "<B1-Motion>", self.on_drag_logo)

        # 2. CÁC THÔNG SỐ KHÁC
        ctk.CTkLabel(self.scroll, text="--- CÀI ĐẶT ---", font=("Arial", 14, "bold")).pack(pady=10)

        # Speed
        f_speed = ctk.CTkFrame(self.scroll, fg_color="transparent")
        f_speed.pack(fill="x", pady=2)
        ctk.CTkLabel(f_speed, text="Tốc độ:").pack(side="left")
        self.lbl_speed = ctk.CTkLabel(f_speed, text="1.05x", text_color="cyan")
        self.lbl_speed.pack(side="right")
        self.slider_speed = ctk.CTkSlider(self.scroll, from_=1.0, to=1.3, number_of_steps=30, command=lambda v: self.lbl_speed.configure(text=f"{round(v,2)}x"))
        self.slider_speed.set(1.05)
        self.slider_speed.pack(fill="x", pady=5)

        # Crop
        ctk.CTkLabel(self.scroll, text="Cắt viền (px):").pack(anchor="w")
        self.entry_crop = ctk.CTkEntry(self.scroll)
        self.entry_crop.insert(0, "10")
        self.entry_crop.pack(fill="x", pady=5)

        # Logo Select
        ctk.CTkLabel(self.scroll, text="File Logo:").pack(anchor="w")
        self.btn_logo = ctk.CTkButton(self.scroll, text="Chọn ảnh Logo...", command=self.browse_logo, fg_color="#555")
        self.btn_logo.pack(fill="x", pady=2)
        self.lbl_logo_name = ctk.CTkLabel(self.scroll, text="Chưa chọn", text_color="gray")
        self.lbl_logo_name.pack()

        # Logo Size
        ctk.CTkLabel(self.scroll, text="Kích thước Logo (% video):").pack(anchor="w")
        self.slider_logo_size = ctk.CTkSlider(self.scroll, from_=0.05, to=0.5)
        self.slider_logo_size.set(0.15)
        self.slider_logo_size.pack(fill="x", pady=5)

        # Confirm
        ctk.CTkButton(self, text="ÁP DỤNG & XỬ LÝ", command=self.on_confirm, height=40, fg_color="green").pack(fill="x", padx=10, pady=10)

    def update_canvas_dot(self):
        # Chuyển đổi tọa độ tương đối sang tuyệt đối trên canvas
        x = self.logo_rel_x * self.preview_width
        y = self.logo_rel_y * self.preview_height
        r = 10 # Bán kính điểm
        self.canvas.coords(self.logo_dot, x-r, y-r, x+r, y+r)

    def on_drag_logo(self, event):
        # Giới hạn trong khung
        cx = max(0, min(event.x, self.preview_width))
        cy = max(0, min(event.y, self.preview_height))
        
        # Cập nhật tọa độ tương đối
        self.logo_rel_x = cx / self.preview_width
        self.logo_rel_y = cy / self.preview_height
        
        self.update_canvas_dot()

    def browse_logo(self):
        p = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg")])
        if p:
            self.logo_path = p
            self.lbl_logo_name.configure(text=os.path.basename(p), text_color="white")

    def on_confirm(self):
        try:
            settings = {
                "speed": round(self.slider_speed.get(), 2),
                "crop": int(self.entry_crop.get()),
                "gamma": 1.1,
                "mirror": False,
                "logo_path": self.logo_path,
                "logo_size": round(self.slider_logo_size.get(), 2),
                # Truyền tọa độ tùy chỉnh ('custom')
                "logo_pos": "custom",
                "logo_x": self.logo_rel_x,
                "logo_y": self.logo_rel_y
            }
            self.destroy()
            self.callback(settings)
        except ValueError:
            print("Lỗi nhập liệu")