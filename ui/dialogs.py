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
        self.geometry("700x650") # [UPDATED] Rộng hơn để chứa 3 cột giờ
        self.attributes("-topmost", True)
        self.grab_set()

        # Center Window
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x, y = (self.winfo_screenwidth()//2 - w//2), (self.winfo_screenheight()//2 - h//2)
        self.geometry(f"+{x}+{y}")

        # Calendar
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

        # [UPDATED] Nút Áp dụng chuyển xuống dưới
        ctk.CTkButton(self, text="⬇ ÁP DỤNG GIỜ MẶC ĐỊNH CHO MỤC ĐÃ CHỌN", width=300,
                      command=self.apply_time_to_selected, fg_color="#E67E22").pack(pady=5)

        # List Video (3 Slots Header)
        f_head = ctk.CTkFrame(self, fg_color="transparent")
        f_head.pack(fill="x", padx=20, pady=(10,0))
        ctk.CTkLabel(f_head, text="Tên Video", anchor="w").pack(side="left", padx=30)
        ctk.CTkLabel(f_head, text="Giờ 1 | Giờ 2 | Giờ 3", anchor="e").pack(side="right", padx=30)

        self.scroll = ctk.CTkScrollableFrame(self, height=250)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

        self.rows = []
        for fname in self.file_names:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            var_sel = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(row, text="", variable=var_sel, width=20)
            chk.pack(side="left")

            lbl_name = ctk.CTkLabel(row, text=fname[:25]+"...", width=180, anchor="w")
            lbl_name.pack(side="left", padx=5)

            # [NEW] 3 Slots
            f_slots = ctk.CTkFrame(row, fg_color="transparent")
            f_slots.pack(side="right")

            slots_ui = []
            for i in range(3):
                lbl = ctk.CTkLabel(f_slots, text="--:--", text_color="gray", width=50)
                lbl.pack(side="left", padx=2)
                slots_ui.append(lbl)

            self.rows.append({"chk": chk, "slots": slots_ui, "times": [], "name": fname})

        ctk.CTkButton(self, text="XÁC NHẬN LÊN LỊCH", command=self.confirm, height=40, fg_color="green").pack(fill="x", padx=20, pady=10)

    def apply_time_to_selected(self):
        try:
            date_str = self.cal.get_date()
            time_str = f"{self.hh.get()}:{self.mm.get()}"
            dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")

            if dt <= datetime.now(): messagebox.showwarning("!", "Thời gian phải ở tương lai!"); return

            count = 0
            for r in self.rows:
                if r["chk"].get():
                    # Logic thêm vào slot trống tiếp theo
                    if len(r["times"]) < 3:
                        r["times"].append(dt)
                        idx = len(r["times"]) - 1
                        r["slots"][idx].configure(text=dt.strftime("%H:%M"), text_color="yellow")
                        count += 1

            if count == 0: messagebox.showinfo("Info", "Chọn video hoặc video đã đầy 3 slot!")
            else:
                # Deselect all for UX
                for r in self.rows: r["chk"].set(False)

        except Exception as e: messagebox.showerror("Err", str(e))

    def confirm(self):
        # Flatten list times
        final_times = []
        for r in self.rows:
            if not r["times"]:
                messagebox.showwarning("!", f"Video '{r['name']}' chưa có giờ nào!"); return
            final_times.extend(r["times"])

        self.callback(final_times)
        self.destroy()