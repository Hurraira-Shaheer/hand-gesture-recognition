import cv2
import mediapipe as mp
import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.gesture_detector import GestureDetector

GESTURES = [
    "open_palm",
    "fist",
    "thumbs_up",
    "thumbs_down",
    "peace",
    "pointing",
]

SAMPLES_PER_GESTURE = 300
DATA_FILE = "ml/gesture_data.csv"

def get_landmark_features(landmarks):
    lm = landmarks.landmark
    wrist_x = lm[0].x
    wrist_y = lm[0].y

    # Calculate hand scale — distance from wrist to middle finger base
    scale = ((lm[9].x - wrist_x)**2 + (lm[9].y - wrist_y)**2) ** 0.5
    if scale == 0:
        scale = 1  # avoid division by zero

    features = []
    for i, point in enumerate(lm):
        if i == 0:
            continue
        features.append((point.x - wrist_x) / scale)  # normalized by scale
        features.append((point.y - wrist_y) / scale)

    return features  # 40 features, scale-invariant

def main():
    detector = GestureDetector()
    cap = cv2.VideoCapture(0)

    file_exists = os.path.exists(DATA_FILE)
    csv_file = open(DATA_FILE, 'a', newline='')
    writer = csv.writer(csv_file)

    if not file_exists:
        header = [f"f{i}" for i in range(40)] + ["label"]  # exactly 41 columns
        writer.writerow(header)
        print(f"Created {DATA_FILE}")

    print("\n=== GESTURE DATA COLLECTION ===")
    print("Controls:")
    print("  SPACE — start/stop collecting for current gesture")
    print("  N     — next gesture")
    print("  Q     — quit\n")

    gesture_idx = 0
    collecting = False
    sample_count = 0

    while gesture_idx < len(GESTURES):
        current_gesture = GESTURES[gesture_idx]

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        landmarks, handedness = detector.get_landmarks(frame)

        if landmarks:
            frame = detector.draw_landmarks(frame, landmarks)

            if collecting:
                features = get_landmark_features(landmarks)
                writer.writerow(features + [current_gesture])
                csv_file.flush()
                sample_count += 1

        status = "COLLECTING" if collecting else "READY"
        color = (0, 255, 136) if collecting else (255, 255, 255)

        cv2.putText(frame, f"Gesture: {current_gesture}",
            (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, f"Status: {status}",
            (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.putText(frame, f"Samples: {sample_count}/{SAMPLES_PER_GESTURE}",
            (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(frame, "SPACE=collect  N=next  Q=quit",
            (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (150, 150, 150), 1)

        if sample_count >= SAMPLES_PER_GESTURE:
            cv2.putText(frame, "DONE! Press N for next gesture",
                (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 136), 2)
            collecting = False

        cv2.imshow("Data Collection", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord(' '):
            if sample_count < SAMPLES_PER_GESTURE:
                collecting = not collecting
                if collecting:
                    print(f"Collecting {current_gesture}...")
                else:
                    print(f"Paused at {sample_count} samples")
        elif key == ord('n'):
            print(f"Saved {sample_count} samples for {current_gesture}")
            gesture_idx += 1
            sample_count = 0
            collecting = False

    csv_file.close()
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone. Data saved to {DATA_FILE}")

if __name__ == "__main__":
    main()