import cv2
import dlib
import numpy as np
from collections import deque

# EAR calculation
def calculate_ear(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

# Constants
LEFT_EYE_IDX = list(range(36, 42))
RIGHT_EYE_IDX = list(range(42, 48))
EAR_THRESHOLD_CLOSED = 0.15
EAR_THRESHOLD_SLIGHTLY_CLOSED = 0.22
MOVEMENT_THRESHOLD = 1.0  # Pixels
SMOOTH_FRAMES = 3         # How many frames to consider
STATIONARY_THRESHOLD = 3  # Require at least 3 low-movement frames

# Optical Flow settings
lk_params = dict(winSize=(15, 15), maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# Dlib setup
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Tracking state
prev_points = None
prev_gray = None
movement_history = deque(maxlen=SMOOTH_FRAMES)

# Add video writer setup
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('eye_tracking_output.avi', fourcc, 20.0, (640, 480))

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(frame_gray)

    if faces:
        landmarks = predictor(frame_gray, faces[0])

        left_eye_pts = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in LEFT_EYE_IDX], dtype=np.float32)
        right_eye_pts = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in RIGHT_EYE_IDX], dtype=np.float32)

        # EAR
        left_ear = calculate_ear(left_eye_pts)
        right_ear = calculate_ear(right_eye_pts)
        ear = (left_ear + right_ear) / 2.0

        if ear < EAR_THRESHOLD_CLOSED:
            eye_state = "Closed"
        elif ear < EAR_THRESHOLD_SLIGHTLY_CLOSED:
            eye_state = "Slightly Closed"
        else:
            eye_state = "Open"

        # Optical flow init
        if prev_points is None:
            points = np.vstack((left_eye_pts, right_eye_pts)).reshape(-1, 1, 2)
            prev_points = points
            prev_gray = frame_gray.copy()
            movement_status = "Initializing..."
            movement_history.clear()
        else:
            # Optical flow
            next_points, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, prev_points, None, **lk_params)
            good_prev = prev_points[status == 1]
            good_next = next_points[status == 1]

            # Draw flow points
            for (x, y) in good_next:
                cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 0), -1)

            movement = np.mean(np.linalg.norm(good_next - good_prev, axis=1))
            movement_history.append(movement)

        
            # Smoothed movement classification using average movement
            avg_movement = np.mean(movement_history)
            if avg_movement > MOVEMENT_THRESHOLD:
                movement_status = "Moving"
            else:
                movement_status = "Stationary"

            # Update for next frame
            prev_points = good_next.reshape(-1, 1, 2)
            prev_gray = frame_gray.copy()
    else:
        eye_state = "Unknown"
        movement_status = "No Face"
        prev_points = None
        movement_history.clear()

    # Ensure text overlays are added before writing the frame
    cv2.putText(frame, f"Eye Movement: {movement_status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    cv2.putText(frame, f"Eye State: {eye_state}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Write the frame to the video file
    out.write(frame)

    cv2.imshow("Eye State + Smooth Movement Detection", frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('r'):
        prev_points = None
        prev_gray = None
        movement_history.clear()

cap.release()
out.release()
cv2.destroyAllWindows()
