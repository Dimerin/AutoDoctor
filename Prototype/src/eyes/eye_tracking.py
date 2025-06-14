import cv2
import dlib
import numpy as np
import time
from collections import deque
from picamera2 import Picamera2


class EyeTracker:
    LEFT_EYE_IDX = list(range(36, 42))
    RIGHT_EYE_IDX = list(range(42, 48))
    EAR_THRESHOLD_CLOSED = 0.15
    EAR_THRESHOLD_SLIGHTLY_CLOSED = 0.22
    MOVEMENT_THRESHOLD = 10.0
    SMOOTH_FRAMES = 3

    def __init__(self, predictor_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        self.prev_points = None
        self.prev_gray = None
        self.movement_history = deque(maxlen=self.SMOOTH_FRAMES)
        self.movement_status = "Initializing..."
        self.eye_state = "Unknown"

    @staticmethod
    def calculate_ear(eye):
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        return (A + B) / (2.0 * C)

    def process_frame(self, frame, frame_gray):
        faces = self.detector(frame_gray)
        if faces:
            landmarks = self.predictor(frame_gray, faces[0])
            left_eye_pts = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in self.LEFT_EYE_IDX], dtype=np.float32)
            right_eye_pts = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in self.RIGHT_EYE_IDX], dtype=np.float32)
            left_ear = self.calculate_ear(left_eye_pts)
            right_ear = self.calculate_ear(right_eye_pts)
            ear = (left_ear + right_ear) / 2.0

            if ear < self.EAR_THRESHOLD_CLOSED:
                self.eye_state = "Closed"
            elif ear < self.EAR_THRESHOLD_SLIGHTLY_CLOSED:
                self.eye_state = "Slightly Closed"
            else:
                self.eye_state = "Open"

            if self.prev_points is None:
                points = np.vstack((left_eye_pts, right_eye_pts)).reshape(-1, 1, 2)
                self.prev_points = points
                self.prev_gray = frame_gray.copy()
                self.movement_status = "Initializing..."
                self.movement_history.clear()
            else:
                next_points, status, _ = cv2.calcOpticalFlowPyrLK(
                    self.prev_gray, frame_gray, self.prev_points, None,
                    winSize=(15, 15), maxLevel=2,
                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
                )
                
                # Controllo per evitare errori se Optical Flow fallisce
                if next_points is None or status is None or len(status) == 0:
                    self.prev_points = None  # resetta per tentare di riprendere tracking nel prossimo frame
                    self.prev_gray = frame_gray.copy()
                    self.movement_status = "Tracking Failed"
                    self.eye_state = "Unknown"
                    self.movement_history.clear()
                    return self.eye_state, self.movement_status

                good_prev = self.prev_points[status == 1]
                good_next = next_points[status == 1]
                
                # Se nessun punto valido è stato tracciato
                if len(good_prev) == 0 or len(good_next) == 0:
                    self.prev_points = None
                    self.prev_gray = frame_gray.copy()
                    self.movement_status = "No Valid Points"
                    self.eye_state = "Unknown"
                    self.movement_history.clear()
                    return self.eye_state, self.movement_status

                movement = np.mean(np.linalg.norm(good_next - good_prev, axis=1))
                self.movement_history.append(movement)
                avg_movement = np.mean(self.movement_history)
                self.movement_status = "Moving" if avg_movement > self.MOVEMENT_THRESHOLD else "Stationary"

                self.prev_points = good_next.reshape(-1, 1, 2)
                self.prev_gray = frame_gray.copy()
        else:
            self.eye_state = "Unknown"
            self.movement_status = "No Face"
            self.prev_points = None
            self.movement_history.clear()

        return self.eye_state, self.movement_status

    def reset(self):
        self.prev_points = None
        self.prev_gray = None
        self.movement_history.clear()


class CameraHandler:
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.configure("preview")
        self.picam2.start()
        time.sleep(1)

    def get_frame(self):
        frame = self.picam2.capture_array()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
