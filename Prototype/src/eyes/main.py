import customtkinter
from PIL import Image, ImageTk
import cv2
from eye_tracking import EyeTracker, CameraHandler
import threading

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1024x800")
        self.title("Eye Tracking GUI")

        self.camera_frame = customtkinter.CTkFrame(self)
        self.camera_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)
        self.camera_label = customtkinter.CTkLabel(self.camera_frame, text="")
        self.camera_label.pack(padx=10, pady=10, fill="both", expand=True)

        self.text_frame1 = customtkinter.CTkFrame(self)
        self.text_frame1.pack(side="top", padx=20, pady=20, fill="x")
        self.text_field1 = customtkinter.CTkEntry(self.text_frame1, placeholder_text="Text Field 1")
        self.text_field1.pack(padx=10, pady=10, fill="x")

        self.text_frame2 = customtkinter.CTkFrame(self)
        self.text_frame2.pack(side="top", padx=20, pady=20, fill="x")
        self.text_field2 = customtkinter.CTkEntry(self.text_frame2, placeholder_text="Text Field 2")
        self.text_field2.pack(padx=10, pady=10, fill="x")

        self.running = True
        self.tracker = EyeTracker("shape_predictor_68_face_landmarks.dat")
        self.camera = CameraHandler()

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

            self.after(0, self.update_gui, ctk_img, eye_state, movement_status)

    def update_gui(self, ctk_img, eye_state, movement_status):
        self.camera_label.configure(image=ctk_img)
        self.camera_label.image = ctk_img
        self.text_field1.delete(0, "end")
        self.text_field1.insert(0, eye_state)
        self.text_field2.delete(0, "end")
        self.text_field2.insert(0, movement_status)

    def on_closing(self):
        self.running = False
        self.destroy()



if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
