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
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0]
            # Get handedness — "Left" or "Right" from MediaPipe's perspective
            handedness = results.multi_handedness[0].classification[0].label
            return landmarks, handedness
        return None, None

    def get_finger_states(self, landmarks, handedness):
        lm = landmarks.landmark
        fingers = []

        # Thumb — direction depends on which hand
        # MediaPipe labels are MIRRORED for front camera
        # so "Right" from MediaPipe = left hand in mirror = right hand in real life
        if handedness == "Right":
            thumb_extended = lm[4].x < lm[3].x
        else:
            thumb_extended = lm[4].x > lm[3].x

        fingers.append(thumb_extended)

        # Four fingers — tip y < pip y means extended
        tip_ids = [8,  12, 16, 20]
        pip_ids = [6,  10, 14, 18]

        for tip, pip in zip(tip_ids, pip_ids):
            fingers.append(lm[tip].y < lm[pip].y)

        return fingers

    def classify_gesture(self, fingers):
        thumb, index, middle, ring, pinky = fingers

        # Exact matches first
        if all(fingers):
            return "open_palm"

        if not any(fingers):
            return "fist"

        if thumb and not index and not middle and not ring and not pinky:
            return "thumbs_up"

        if not thumb and index and middle and not ring and not pinky:
            return "peace"

        if not thumb and index and not middle and not ring and not pinky:
            return "pointing"

        if not thumb and not index and not middle and not ring and pinky:
            return "pinky_up"

        # Partial matches — count extended fingers
        extended = sum(fingers)

        if extended >= 4:
            return "open_palm"

        return "unknown"

    def draw_landmarks(self, frame, landmarks):
        self.mp_draw.draw_landmarks(
            frame,
            landmarks,
            self.mp_hands.HAND_CONNECTIONS
        )
        return frame




from collections import deque

class GestureStabilizer:
    def __init__(self, window_size=10, threshold=0.6):
        """
        window_size — how many recent frames to consider
        threshold   — what fraction must agree (0.6 = 60%)
        """
        self.window = deque(maxlen=window_size)
        self.threshold = threshold
        self.last_stable = "no_hand"

    def update(self, gesture):
        """
        Feed in raw gesture each frame.
        Returns stable gesture only when confident enough.
        """
        self.window.append(gesture)

        if len(self.window) < self.window.maxlen:
            return self.last_stable  # not enough data yet

        # Count occurrences of each gesture in window
        counts = {}
        for g in self.window:
            counts[g] = counts.get(g, 0) + 1

        # Find the most common one
        top_gesture = max(counts, key=counts.get)
        top_fraction = counts[top_gesture] / len(self.window)

        if top_fraction >= self.threshold:
            self.last_stable = top_gesture

        return self.last_stable