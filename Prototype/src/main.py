import customtkinter
import os
import time 
import csv
from PIL import Image
import psutil

DEMO_MODE = False
customtkinter.set_appearance_mode("dark")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1024x512")
        self.title("Demo prototype AutoDoctor GUI")
        self.resizable(False, False)
        self.last_heart_rate_sample = None
        self.prev_time = None
        self.fps = 0
        self.eyes_status_list = []
        self.movement_status_list = []
        self.heart_rate_status_list = []
        self.fps_list = []
        self.cpu_list = []
        self.ram_list = []

        self.eye_icons = {
            "open": customtkinter.CTkImage(light_image=Image.open("assets/eye_open.png"), size=(50, 50)),
            "closed": customtkinter.CTkImage(light_image=Image.open("assets/eye_closed.png"), size=(50, 50)),
            "slightly_closed": customtkinter.CTkImage(light_image=Image.open("assets/slightly_closed.png"), size=(50, 50)),
            "hidden": customtkinter.CTkImage(light_image=Image.open("assets/hidden.png"), size=(50, 50)),
        }
        self.movement_icons = {
            "moving": customtkinter.CTkImage(light_image=Image.open("assets/eye_movement.png"), size=(50, 50)),
            "stationary": customtkinter.CTkImage(light_image=Image.open("assets/eye_stationary.png"), size=(50, 50)),
            "hidden": customtkinter.CTkImage(light_image=Image.open("assets/hidden.png"), size=(50, 50)),
        }


        # FRAME CONTENITORE RIGA 1
        self.top_frame = customtkinter.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10,5))

        # FRAME CONTENITORE RIGA 2
        self.bottom_frame = customtkinter.CTkFrame(self)
        self.bottom_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        # CONFIGURAZIONE PESI PER RIDIMENSIONAMENTO AUTOMATICO
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # FRAME SINISTRO (CAMERA) NELLA PRIMA RIGA
        self.camera_frame = customtkinter.CTkFrame(self.top_frame, width=640, height=480)
        self.camera_frame.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        self.camera_label = customtkinter.CTkLabel(self.camera_frame, text="")
        self.camera_label.pack(padx=10, pady=10)

        # FRAME DESTRO (DATI) NELLA PRIMA RIGA
        self.data_frame = customtkinter.CTkFrame(self.top_frame)
        self.data_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        # EYE FRAME
        self.eye_frame = customtkinter.CTkFrame(self.data_frame)
        self.eye_frame.pack(padx=10, pady=(20, 10), fill="x")
        self.eye_status = customtkinter.CTkLabel(
            self.eye_frame,
            text="  No eye detected",
            height=50,
            image=self.eye_icons["hidden"],
            font=("Arial", 20),
            compound="left", 
            corner_radius=10
        )
        self.eye_status.pack(padx=10, pady=10, fill="x")

        # MOVEMENT FRAME
        self.movement_frame = customtkinter.CTkFrame(self.data_frame)
        self.movement_frame.pack(padx=10, pady=10, fill="x")
        self.movement_status = customtkinter.CTkLabel(
            self.movement_frame,
            text="  No movement detected",
            height=50,
            font=("Arial", 20),
            image=self.movement_icons["hidden"],
            compound="left", 
            corner_radius=10
        )
        self.movement_status.pack(padx=10, pady=10, fill="x")
        # HR ICON LOADING
        heart_img = Image.open("assets/heart-rate.png")
        self.heart_photo = customtkinter.CTkImage(light_image=heart_img, size=(50, 50))

        # HEART RATE FRAME
        self.heart_rate_frame = customtkinter.CTkFrame(self.data_frame)
        self.heart_rate_frame.pack(padx=10, pady=(20, 10), fill="x")
        self.heart_rate_status = customtkinter.CTkLabel(
            self.heart_rate_frame,
            text="  Heart Rate: Waiting for data...",
            image=self.heart_photo,
            compound="left", 
            text_color="green",
            height=50,
            font=("Arial", 20),
            corner_radius=10,
            anchor="center",
            justify="center"
        )
        self.heart_rate_status.pack(padx=10, pady=10, fill="x")

        # FPS ICON LOADING
        fps_img = Image.open("assets/fps.png")
        self.fps_photo = customtkinter.CTkImage(light_image=fps_img, size=(50, 50))
        # FPS FRAME
        self.fps_frame = customtkinter.CTkFrame(self.data_frame)
        self.fps_frame.pack(padx=10, pady=10, fill="x")
        self.fps_label = customtkinter.CTkLabel(
            self.fps_frame,
            text="  FPS: 0",
            image=self.fps_photo,
            compound="left",
            height=50,
            font=("Arial", 20),
            corner_radius=10,
        )
        self.fps_label.pack(padx=10, pady=10, fill="x")

        # RIGA 2: RISPOSTA E BOTTONE
        self.answer_label = customtkinter.CTkLabel(
            self.bottom_frame,
            text="User Answer: Waiting for interaction...",
            font=("Arial", 20),
            anchor="w"
        )
        self.answer_label.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.voice_button = customtkinter.CTkButton(
            self.bottom_frame,
            text="Start Voice Interaction",
            command=self.voice_agent
        )
        self.voice_button.pack(side="right", padx=10, pady=10)
        if not DEMO_MODE:
            import cv2
            from eyes import EyeTracker, CameraHandler
            from heart import HeartRateSensor
            from voice import VoiceAgent
            import threading
   
            self.running = True
            self.tracker = EyeTracker("eyes/shape_predictor_68_face_landmarks.dat")
            self.camera = CameraHandler()
            self.heart_rate_sensor = HeartRateSensor(gpio_pin_hr=4, gpio_pin_led=17)
            self.heart_rate_sensor.setup()
            self.video_thread = threading.Thread(target=self.update_window, daemon=True)
            self.video_thread.start()
            self.monitor_resources()
        else:
            self.running = False

    def update_window(self):
        self.prev_time = time.time()
        while self.running:
            frame = self.camera.get_frame()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            eye_state, movement_status = self.tracker.process_frame(frame, frame_gray)
            self.eyes_status_list.append(eye_state)
            self.movement_status_list.append(movement_status)
            current_time = time.time()

            fps = 1 / (current_time - self.prev_time) if self.prev_time else 0
            self.prev_time = current_time
            self.fps_list.append(fps)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480))

            ctk_img = customtkinter.CTkImage(light_image=img, size=(640, 480))
            self.last_heart_rate_sample = self.heart_rate_sensor.get_heart_rate()
            self.heart_rate_status_list.append(self.last_heart_rate_sample)
            self.after(1000, self.update_gui_heart_rate)
            self.after(0, self.update_gui_video, ctk_img, eye_state, movement_status,fps)


    def update_gui_video(self, ctk_img, eye_state, movement_status, fps):
        self.camera_label.configure(image=ctk_img)
        self.camera_label.image = ctk_img

        # Eye status
        if eye_state == "Open":
            icon = self.eye_icons["open"]
            color = "green"
        elif eye_state == "Closed":
            icon = self.eye_icons["closed"]
            color = "red"
        elif eye_state == "Slightly Closed":
            icon = self.eye_icons["slightly_closed"]
            color = "orange"
        else:
            icon = None
            color = "gray"
        self.eye_status.configure(text=eye_state, image=icon, compound="left", text_color=color)

        # Movement status
        if movement_status == "Moving":
            icon = self.movement_icons["moving"]
            color = "blue"
        elif movement_status == "Stationary":
            icon = self.movement_icons["stationary"]
            color = "green"
        else:
            icon = None
            color = "gray"
        self.movement_status.configure(text=movement_status, image=icon, compound="left", text_color=color)

        self.fps_label.configure(text=f"FPS: {fps:.2f}")

    def update_gui_heart_rate(self):
        if self.last_heart_rate_sample is not None:
            self.heart_rate_status.configure(text=f"Heart Rate: {self.last_heart_rate_sample:.1f} BPM")
        else:
            self.heart_rate_status.configure(text="Heart Rate: Waiting for data...")
            
    def voice_agent(self):
        self.voice_agent = VoiceAgent()
        self.user_answer = self.voice_agent.start_protocol(duration=5)
        if self.user_answer == -1:
            self.answer_label.configure(text="User Answer: Not recognized")
        else:
            self.answer_label.configure(text=f"User Answer: {'Yes' if self.user_answer == 1 else 'No'}")

    def monitor_resources(self):
        self.cpu_list.append(psutil.cpu_percent(interval=None))
        self.ram_list.append(psutil.virtual_memory().percent)
        self.after(1000, self.monitor_resources)

    def dump_data(self):
        if not os.path.exists("../dump"):
            os.makedirs("../dump")
        
        time_stamp = time.strftime("%Y%m%d_%H%M%S")
    
        with open(f"../dump/fps_status_{time_stamp}.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID","FPS"])
            for i, fps in enumerate(self.fps_list):
                writer.writerow([i, fps])
        with open(f"../dump/cpu_ram_{time_stamp}.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["ID", "CPU_percent", "RAM_percent"])
            for i, (cpu, ram) in enumerate(zip(self.cpu_list, self.ram_list)):
                writer.writerow([i, cpu, ram])

    def on_closing(self):
        print("Closing application...")
        self.running = False
        print("Dumping data...")
        self.dump_data()
        self.heart_rate_sensor.cleanup()
        self.destroy()



if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
