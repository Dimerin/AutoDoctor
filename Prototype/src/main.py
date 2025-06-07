import customtkinter
from PIL import Image, ImageTk
import cv2
from eyes import EyeTracker, CameraHandler
from heart import HeartRateSensor
import threading

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1024x800")
        self.title("Demo prototype AutoDoctor GUI")
        self.last_heart_rate_sample = None

        self.camera_frame = customtkinter.CTkFrame(self)
        self.camera_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)
        self.camera_label = customtkinter.CTkLabel(self.camera_frame, text="")
        self.camera_label.pack(padx=10, pady=10, fill="both", expand=True)

        self.eye_frame = customtkinter.CTkFrame(self)
        self.eye_frame.pack(side="top", padx=20, pady=20, fill="x")
        self.eye_status = customtkinter.CTkEntry(
            self.eye_frame,
             placeholder_text="No eye detected",
             height=40,
             font=("Pacifico", 16),
             corner_radius=10)
        self.eye_status.pack(padx=10, pady=10, fill="x")

        self.movement_frame = customtkinter.CTkFrame(self)
        self.movement_frame.pack(side="top", padx=20, pady=20, fill="x")
        self.movement_status = customtkinter.CTkEntry(
            self.movement_frame,
            placeholder_text="No movement detected",
            height=40,
            font=("Pacifico", 16),
            corner_radius=10)
        self.movement_status.pack(padx=10, pady=10, fill="x")

        self.heart_rate_frame = customtkinter.CTkFrame(self)
        self.heart_rate_frame.pack(side="top", padx=20, pady=20, fill="x")
        self.heart_rate_status = customtkinter.CTkEntry(
            self.heart_rate_frame,
            placeholder_text="Heart Rate: Waiting for data...",
            height=40,
            font=("Pacifico", 16),
            corner_radius=10)
        self.heart_rate_status.pack(padx=10, pady=10, fill="x")

        self.running = True
        self.tracker = EyeTracker("shape_predictor_68_face_landmarks.dat")
        self.camera = CameraHandler()
        self.heart_rate_sensor = HeartRateSensor(gpio_pin_hr=4, gpio_pin_led=17)
        self.heart_rate_sensor.setup()
        self.heart_rate_thread = threading.Thread(target=self.real_time_heart_rate, daemon=True)
        self.heart_rate_thread.start()

        self.video_thread = threading.Thread(target=self.update_video, daemon=True)
        self.video_thread.start()

    def update_video(self):
        while self.running:
            frame = self.camera.get_frame()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eye_state, movement_status = self.tracker.process_frame(frame, frame_gray)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480))

            ctk_img = customtkinter.CTkImage(light_image=img, size=(640, 480))

            self.after(0, self.update_gui_video, ctk_img, eye_state, movement_status)

    def real_time_heart_rate(self):
        while self.running:
            self.last_heart_rate_sample = self.heart_rate_sensor.get_heart_rate()
            self.after(1000, self.update_gui_heart_rate)


    def update_gui_video(self, ctk_img, eye_state, movement_status):
        self.camera_label.configure(image=ctk_img)
        self.camera_label.image = ctk_img
        self.eye_status.delete(0, "end")
        self.eye_status.insert(0, eye_state)
        self.movement_status.delete(0, "end")
        self.movement_status.insert(0, movement_status)
       
    def update_gui_heart_rate(self):
        if self.last_heart_rate_sample is not None:
            self.heart_rate_status.delete(0, "end")
            self.heart_rate_status.insert(0, f"Heart Rate: {self.last_heart_rate_sample:.1f} BPM")
        else:
            self.heart_rate_status.delete(0, "end")
            self.heart_rate_status.insert(0, "Heart Rate: Waiting for data...")

    def on_closing(self):
        self.running = False
        self.heart_rate_sensor.cleanup()
        self.destroy()



if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
