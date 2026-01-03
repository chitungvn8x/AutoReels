import customtkinter as ctk
import cv2
from PIL import Image
import threading
import time

class SimpleVideoPlayer(ctk.CTkLabel):
    def __init__(self, master, width=300, height=500):
        super().__init__(master, text="", width=width, height=height, fg_color="black")
        self.width = width
        self.height = height
        self.cap = None
        self.is_playing = False
        self.thread = None
        self.stop_event = threading.Event()

    def load_video(self, video_path):
        self.stop() 
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            self.configure(text="Lỗi File")
            return
        
        # Hiện frame đầu
        ret, frame = self.cap.read()
        if ret: self.display_image(frame)

    def play(self):
        if not self.cap or self.is_playing: return
        self.is_playing = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._play_loop, daemon=True)
        self.thread.start()

    def _play_loop(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps == 0: fps = 30
        interval = 1.0 / fps

        while self.is_playing and not self.stop_event.is_set():
            start_time = time.time()
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # [FIX] Không gọi configure trực tiếp từ thread -> dùng after
                    # Resize ảnh trước trong thread để giảm tải cho main loop
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, _ = frame_rgb.shape
                    ratio = min(self.width/w, self.height/h)
                    new_w = int(w * ratio)
                    new_h = int(h * ratio)
                    frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
                    
                    img = Image.fromarray(frame_resized)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                    
                    # Đẩy việc cập nhật UI sang luồng chính
                    self.after(0, self.update_ui_image, ctk_img)
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop
            
            elapsed = time.time() - start_time
            wait = interval - elapsed
            if wait > 0: time.sleep(wait)

    def update_ui_image(self, ctk_img):
        # Hàm này chạy ở main thread -> Không bị flickering
        self.configure(image=ctk_img)

    def display_image(self, frame):
        # Helper hiển thị 1 frame tĩnh
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        ratio = min(self.width/w, self.height/h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        frame = cv2.resize(frame, (new_w, new_h))
        img = Image.fromarray(frame)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
        self.configure(image=ctk_img)

    def stop(self):
        self.is_playing = False
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)
        if self.cap:
            self.cap.release()
            self.cap = None