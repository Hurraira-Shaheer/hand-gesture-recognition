import cv2
import mediapipe as mp
import time

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def get_landmarks(self, frame):
        """
        Takes a BGR frame from OpenCV.
        Returns landmark list if hand detected, None otherwise.
        """
        # MediaPipe needs RGB, OpenCV gives BGR — convert
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:
            return results.multi_hand_landmarks[0]  # first hand only
        return None

    def get_finger_states(self, landmarks):
        """
        Returns a list of 5 booleans — True if finger is extended.
        Order: [thumb, index, middle, ring, pinky]
        """
        lm = landmarks.landmark  # list of 21 points

        fingers = []

        # Thumb — compare x instead of y (horizontal movement)
        # Tip is landmark 4, IP joint is landmark 3
        thumb_extended = lm[4].x < lm[3].x  # works for right hand
        fingers.append(thumb_extended)

        # Other four fingers — tip y < pip y means extended
        # (remember y=0 is top, so smaller y = higher on screen = extended)
        tip_ids =  [8,  12, 16, 20]
        pip_ids =  [6,  10, 14, 18]

        for tip, pip in zip(tip_ids, pip_ids):
            fingers.append(lm[tip].y < lm[pip].y)

        return fingers  # [thumb, index, middle, ring, pinky]

    def classify_gesture(self, fingers):
        """
        Takes finger states, returns gesture name.
        fingers = [thumb, index, middle, ring, pinky]
        """
        thumb, index, middle, ring, pinky = fingers

        if all(fingers):
            return "open_palm"

        if not any(fingers):
            return "fist"

        if thumb and not index and not middle and not ring and not pinky:
            return "thumbs_up"

        if not thumb and not index and not middle and not ring and not pinky:
            return "fist"

        if not thumb and index and middle and not ring and not pinky:
            return "peace"

        if not thumb and index and not middle and not ring and not pinky:
            return "pointing"

        return "unknown"

    def draw_landmarks(self, frame, landmarks):
        """Draw the 21 landmarks and connections on the frame."""
        self.mp_draw.draw_landmarks(
            frame,
            landmarks,
            self.mp_hands.HAND_CONNECTIONS
        )
        return frame