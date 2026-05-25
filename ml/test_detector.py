import cv2
import sys
import os

# so Python finds the ml module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.gesture_detector import GestureDetector

def main():
    detector = GestureDetector()
    cap = cv2.VideoCapture(0)  # 0 = default webcam

    print("Starting gesture detection. Press Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Could not read from webcam")
            break

        # Flip horizontally — mirror view feels natural
        frame = cv2.flip(frame, 1)


        landmarks, handedness = detector.get_landmarks(frame)

        if landmarks:
            fingers = detector.get_finger_states(landmarks, handedness)
            gesture = detector.classify_gesture(fingers=fingers, landmarks=landmarks)
            frame = detector.draw_landmarks(frame, landmarks)

            cv2.putText(frame, f"{gesture} ({handedness})",
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                1.2, (0, 255, 136), 3)

            finger_names = ['T', 'I', 'M', 'R', 'P']
            states = ' '.join([
                f"{n}:{'1' if s else '0'}"
                for n, s in zip(finger_names, fingers)
            ])
            cv2.putText(frame, states,
                (10, 100), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2)

        cv2.imshow("Gesture Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()