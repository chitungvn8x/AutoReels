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
        self.geometry("800x650")
        self.attributes("-topmost", True)
        self.grab_set()

        self.update_idletasks()
        w, h = 800, 650
        x = (self.winfo_screenwidth()//2 - w//2)
        y = (self.winfo_screenheight()//2 - h//2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.cal = Calendar(self, selectmode='day', date_pattern='dd/mm/yyyy')
        self.cal.pack(pady=(10, 5))

        f_time = ctk.CTkFrame(self, fg_color="transparent")
        f_time.pack(pady=5)

        now = datetime.now()
        self.hh = ctk.CTkComboBox(f_time, values=[f"{i:02d}" for i in range(24)], width=60)
        self.hh.set(f"{now.hour:02d}"); self.hh.pack(side="left")
        ctk.CTkLabel(f_time, text=":").pack(side="left")
        self.mm = ctk.CTkComboBox(f_time, values=[f"{i:02d}" for i in range(60)], width=60)
        self.mm.set(f"{now.minute:02d}"); self.mm.pack(side="left")

        ctk.CTkButton(self, text="⬇ ÁP DỤNG CHO VIDEO ĐÃ CHỌN", width=300,
                      command=self.apply_time_to_selected, fg_color="#E67E22").pack(pady=5)

        # Header
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

            f_slots = ctk.CTkFrame(row, fg_color="transparent")
            f_slots.pack(side="right")

            slots_ui = []
            for i in range(3):
                lbl = ctk.CTkLabel(f_slots, text="--:--", text_color="gray", width=60)
                lbl.pack(side="left", padx=2)
                slots_ui.append(lbl)

            self.rows.append({"chk_var": var_sel, "chk_widget": chk, "slots": slots_ui, "times": [], "name": fname})

        ctk.CTkButton(self, text="XÁC NHẬN LÊN LỊCH", command=self.confirm, height=40, fg_color="green").pack(fill="x", padx=20, pady=10)

    def show_modal_info(self, msg):
        # Helper to show modal dialog on top of this Toplevel
        top = ctk.CTkToplevel(self)
        top.geometry("300x150")
        top.attributes("-topmost", True)
        top.title("Thông báo")
        # Center relative to parent
        x = self.winfo_x() + (self.winfo_width()//2) - 150
        y = self.winfo_y() + (self.winfo_height()//2) - 75
        top.geometry(f"+{x}+{y}")
        ctk.CTkLabel(top, text=msg, wraplength=250).pack(pady=20)
        ctk.CTkButton(top, text="OK", command=top.destroy).pack(pady=10)
        top.grab_set()

    def apply_time_to_selected(self):
        try:
            date_str = self.cal.get_date()
            time_str = f"{self.hh.get()}:{self.mm.get()}"
            dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")

            if dt <= datetime.now():
                self.show_modal_info("Thời gian phải ở tương lai!")
                return

            count = 0
            for r in self.rows:
                if r["chk_var"].get():
                    if len(r["times"]) < 3:
                        r["times"].append(dt)
                        idx = len(r["times"]) - 1
                        r["slots"][idx].configure(text=dt.strftime("%H:%M"), text_color="yellow")
                        count += 1

            if count == 0:
                self.show_modal_info("Vui lòng tick chọn video bên dưới (Tối đa 3 giờ/video)!")
            else:
                # [FIX] Deselect using widget methods
                for r in self.rows:
                    r["chk_widget"].deselect()

        except Exception as e: self.show_modal_info(str(e))

    def confirm(self):
        final_times = []
        for r in self.rows:
            if not r["times"]:
                self.show_modal_info(f"Video '{r['name']}' chưa có giờ nào!")
                return
            final_times.extend(r["times"])

        self.callback(final_times)
        self.destroy()