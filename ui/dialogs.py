import customtkinter as ctk
from tkcalendar import Calendar
from tkinter import messagebox
from datetime import datetime, timedelta

class CookieNameDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Lưu Cookie")
        self.geometry("400x200")
        self.attributes("-topmost", True)
        ctk.CTkLabel(self, text="Nhập tên Profile:").pack(pady=10)
        self.entry = ctk.CTkEntry(self, width=250); self.entry.pack(pady=5)
        ctk.CTkButton(self, text="LƯU", command=self.confirm).pack(pady=15)
    def confirm(self):
        if self.entry.get().strip(): self.callback(self.entry.get().strip()); self.destroy()

class ScheduleDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, count=1):
        super().__init__(parent)
        self.callback = callback; self.req = count
        self.title(f"Lên Lịch ({count} video)"); self.geometry("500x500")
        self.times = []
        self.cal = Calendar(self, selectmode='day', date_pattern='dd/mm/yyyy'); self.cal.pack(pady=10)
        
        f = ctk.CTkFrame(self); f.pack()
        self.hh = ctk.CTkComboBox(f, values=[f"{i:02d}" for i in range(24)], width=60); self.hh.pack(side="left")
        ctk.CTkLabel(f, text=":").pack(side="left")
        self.mm = ctk.CTkComboBox(f, values=[f"{i:02d}" for i in range(0, 60, 5)], width=60); self.mm.pack(side="left")
        ctk.CTkButton(f, text="Thêm", width=60, command=self.add).pack(side="left", padx=5)
        
        self.lst = ctk.CTkTextbox(self, height=150); self.lst.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self, text="XÁC NHẬN", command=self.confirm, fg_color="green").pack(pady=5)

    def add(self):
        try:
            dt = datetime.strptime(f"{self.cal.get_date()} {self.hh.get()}:{self.mm.get()}", "%d/%m/%Y %H:%M")
            if dt <= datetime.now() + timedelta(minutes=15): messagebox.showwarning("Lỗi", "Thời gian phải > 15 phút!"); return
            self.times.append(dt); self.lst.insert("end", f"⏰ {dt.strftime('%d/%m %H:%M')}\n")
        except: pass

    def confirm(self):
        if len(self.times) != self.req: messagebox.showwarning("Lỗi", f"Cần chọn đúng {self.req} mốc!"); return
        self.callback(self.times); self.destroy()