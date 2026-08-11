import json

DEFAULT_CONFIG = {
    "camera_object_id": 1,
    "camera_person_id": 0,
    "timeout_seconds": 60,
    "desk_id": "Desk_1",
    "confidence_threshold": 0.4,
    "item_hold_time": 2.0,
    "person_hold_time": 2.0,
    "roi_enabled": False,
    "roi_x1": 0,
    "roi_y1": 0,
    "roi_x2": 0,
    "roi_y2": 0
}


def save_config(config_data, path="config.json"):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(config_data, file, indent=4)


def load_config(path="config.json"):
    try:
        with open(path, "r", encoding="utf-8") as file:
            loaded = json.load(file)
    except FileNotFoundError:
        loaded = {}

    merged = DEFAULT_CONFIG.copy()
    merged.update(loaded)
    save_config(merged, path)
    return merged