import customtkinter as ctk
from tkcalendar import Calendar
from tkinter import messagebox
from datetime import datetime, timedelta

class ScheduleDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, file_names):
        super().__init__(parent)
        self.callback = callback
        self.file_names = file_names
        self.count = len(file_names)
        self.title(f"Lên Lịch ({self.count} video)")
        self.geometry("550x650") # Tăng size để chứa list
        self.attributes("-topmost", True)
        self.grab_set()

        # [FIX] Center Window
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x, y = (self.winfo_screenwidth()//2 - w//2), (self.winfo_screenheight()//2 - h//2)
        self.geometry(f"+{x}+{y}")

        # Calendar Area (Sát lề)
        self.cal = Calendar(self, selectmode='day', date_pattern='dd/mm/yyyy')
        self.cal.pack(pady=(10, 5))

        # Time Picker Row
        f_time = ctk.CTkFrame(self, fg_color="transparent")
        f_time.pack(pady=5)

        now = datetime.now()
        self.hh = ctk.CTkComboBox(f_time, values=[f"{i:02d}" for i in range(24)], width=60)
        self.hh.set(f"{now.hour:02d}"); self.hh.pack(side="left")
        ctk.CTkLabel(f_time, text=":").pack(side="left")
        self.mm = ctk.CTkComboBox(f_time, values=[f"{i:02d}" for i in range(60)], width=60)
        self.mm.set(f"{now.minute:02d}"); self.mm.pack(side="left")

        ctk.CTkButton(f_time, text="⬇ ÁP DỤNG CHO VIDEO ĐANG CHỌN", width=200,
                      command=self.apply_time_to_selected, fg_color="#E67E22").pack(side="left", padx=10)

        # List Video cần lên lịch
        ctk.CTkLabel(self, text="DANH SÁCH VIDEO & GIỜ ĐĂNG:", anchor="w").pack(fill="x", padx=20)

        self.scroll = ctk.CTkScrollableFrame(self, height=250)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.rows = []
        for fname in self.file_names:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            # Radio button để chọn dòng (để áp dụng giờ)
            var_sel = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(row, text="", variable=var_sel, width=20)
            chk.pack(side="left")

            lbl_name = ctk.CTkLabel(row, text=fname[:30]+"...", width=200, anchor="w")
            lbl_name.pack(side="left", padx=5)

            lbl_time = ctk.CTkLabel(row, text="--:--", text_color="yellow", width=100)
            lbl_time.pack(side="right", padx=5)

            self.rows.append({"chk": chk, "lbl_time": lbl_time, "time_val": None, "name": fname})

        # Confirm Button (Sát đáy, giảm padding thừa)
        ctk.CTkButton(self, text="XÁC NHẬN LÊN LỊCH", command=self.confirm, height=40, fg_color="green").pack(fill="x", padx=20, pady=10)

    def apply_time_to_selected(self):
        try:
            date_str = self.cal.get_date()
            time_str = f"{self.hh.get()}:{self.mm.get()}"
            dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")

            if dt <= datetime.now():
                messagebox.showwarning("!", "Thời gian phải ở tương lai!")
                return

            # Apply cho các dòng được check
            count = 0
            for r in self.rows:
                if r["chk"].get():
                    r["time_val"] = dt
                    r["lbl_time"].configure(text=dt.strftime("%d/%m %H:%M"))
                    r["chk"].deselect() # Auto deselect after apply
                    count += 1

            if count == 0: messagebox.showinfo("Info", "Vui lòng tick chọn video trong danh sách bên dưới để áp dụng giờ.")

        except Exception as e: messagebox.showerror("Err", str(e))

    def confirm(self):
        final_times = []
        for r in self.rows:
            if r["time_val"] is None:
                messagebox.showwarning("!", f"Video '{r['name']}' chưa có giờ đăng!")
                return
            final_times.append(r["time_val"])

        self.callback(final_times)
        self.destroy()