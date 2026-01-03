import sys
import os

# Đảm bảo Python tìm thấy các thư mục con (backend, ui)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from ui.main_window import App

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print("---------------------------------------------------")
        print("❌ CHUONG TRINH GAP LOI KHOI DONG:")
        print(e)
        import traceback
        traceback.print_exc()
        print("---------------------------------------------------")
        input("Nhan Enter de thoat...")