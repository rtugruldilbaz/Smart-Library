import time


class StateManager:
    def __init__(self):
        self.current_state = "EMPTY"
        self.monitor_state = "IDLE - NO TIMER RUNNING"

        self.unattended_start_time = None
        self.occupied_start_time = None

        self.unattended_elapsed = 0
        self.occupied_elapsed = 0

        self.violation_triggered = False

        self.last_item_seen_time = None
        self.last_person_seen_time = None

    def reset(self):
        self.current_state = "EMPTY"
        self.monitor_state = "IDLE - NO TIMER RUNNING"

        self.unattended_start_time = None
        self.occupied_start_time = None

        self.unattended_elapsed = 0
        self.occupied_elapsed = 0

        self.violation_triggered = False

        self.last_item_seen_time = None
        self.last_person_seen_time = None

    def update(
        self,
        raw_item_exists: bool,
        raw_person_exists: bool,
        item_hold_time: float,
        person_hold_time: float,
        timeout_seconds: int,
    ):
        now = time.time()

        if raw_item_exists:
            self.last_item_seen_time = now

        if raw_person_exists:
            self.last_person_seen_time = now

        item_exists = (
            self.last_item_seen_time is not None and
            (now - self.last_item_seen_time) <= item_hold_time
        )

        person_exists = (
            self.last_person_seen_time is not None and
            (now - self.last_person_seen_time) <= person_hold_time
        )

        violation_now = False

        if person_exists:
            self.current_state = "OCCUPIED"
            self.monitor_state = "MONITORING OCCUPIED DESK"

            if self.occupied_start_time is None:
                self.occupied_start_time = now

            self.occupied_elapsed = now - self.occupied_start_time

            self.unattended_start_time = None
            self.unattended_elapsed = 0
            self.violation_triggered = False

        elif item_exists and not person_exists:
            self.current_state = "UNATTENDED"
            self.monitor_state = "UNATTENDED TIMER ACTIVE"

            if self.unattended_start_time is None:
                self.unattended_start_time = now

            self.unattended_elapsed = now - self.unattended_start_time

            self.occupied_start_time = None
            self.occupied_elapsed = 0

            if self.unattended_elapsed >= timeout_seconds and not self.violation_triggered:
                self.current_state = "VIOLATION"
                self.monitor_state = "VIOLATION DETECTED"
                self.violation_triggered = True
                violation_now = True

        else:
            self.current_state = "EMPTY"
            self.monitor_state = "IDLE - NO TIMER RUNNING"

            self.unattended_start_time = None
            self.occupied_start_time = None
            self.unattended_elapsed = 0
            self.occupied_elapsed = 0
            self.violation_triggered = False

        return {
            "item_exists": item_exists,
            "person_exists": person_exists,
            "current_state": self.current_state,
            "monitor_state": self.monitor_state,
            "occupied_elapsed": self.occupied_elapsed,
            "unattended_elapsed": self.unattended_elapsed,
            "violation_now": violation_now,
            "violation_triggered": self.violation_triggered,
        }