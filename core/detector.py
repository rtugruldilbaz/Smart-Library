import os
import sys
import cv2
from ultralytics import YOLO


def resource_path(relative_path):
    """Normal Python ve PyInstaller EXE için dosya yolunu bulur."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


MODEL_PATH = resource_path("yolov8n.pt")

model = YOLO(MODEL_PATH)


PERSON_CLASS = "person"

ITEM_CLASSES = {
    "laptop",
    "mouse",
    "keyboard",
    "cell phone",
    "backpack",
    "handbag",
    "suitcase",
    "bottle",
    "cup",
    "book"
}


def detect_filtered(frame, target_mode="all", confidence_threshold=0.4):
    detected = []

    results = model(frame, verbose=False)

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            class_name = model.names[class_id]

            if confidence < confidence_threshold:
                continue

            should_use = False
            color = (255, 0, 0)

            if target_mode == "items_only" and class_name in ITEM_CLASSES:
                should_use = True
                color = (0, 165, 255)

            elif target_mode == "person_only" and class_name == PERSON_CLASS:
                should_use = True
                color = (0, 255, 0)

            elif target_mode == "display_non_person":
                if class_name != PERSON_CLASS:
                    should_use = True
                    color = (255, 191, 0)

            elif target_mode == "all":
                should_use = True

            if should_use:
                detected.append((class_name, confidence))

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                label = f"{class_name} {confidence:.2f}"

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )

    return detected, frame


def contains_person(detected_list):
    for class_name, confidence in detected_list:
        if class_name == PERSON_CLASS:
            return True

    return False


def contains_item(detected_list):
    for class_name, confidence in detected_list:
        if class_name in ITEM_CLASSES:
            return True

    return False