import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

from core.config_manager import load_config, save_config
from core.logger import write_log
from core.state_manager import StateManager
from ui.ui_helpers import create_no_signal_frame, format_seconds, safe_crop
from core.detector import detect_filtered, contains_person, contains_item
from ui.settings_window import SettingsWindow
from ui.roi_window import ROISettingsWindow


class SmartLibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Library Graduation Project")
        self.root.geometry("1540x1020")
        self.root.configure(bg="#f2f2f2")

        self.config = load_config()

        self.camera_object_id = self.config["camera_object_id"]
        self.camera_person_id = self.config["camera_person_id"]
        self.desk_id = self.config["desk_id"]
        self.confidence_threshold = self.config["confidence_threshold"]

        self.timeout_seconds = self.config["timeout_seconds"]
        self.item_hold_time = self.config["item_hold_time"]
        self.person_hold_time = self.config["person_hold_time"]

        self.roi_enabled = self.config["roi_enabled"]
        self.roi_x1 = self.config["roi_x1"]
        self.roi_y1 = self.config["roi_y1"]
        self.roi_x2 = self.config["roi_x2"]
        self.roi_y2 = self.config["roi_y2"]

        self.cap_object = cv2.VideoCapture(self.camera_object_id)
        self.cap_person = cv2.VideoCapture(self.camera_person_id)

        self.cap_object.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap_object.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap_person.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap_person.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.alert_open = False
        self.latest_object_frame_for_roi = None

        self.state_manager = StateManager()

        self.settings_window = SettingsWindow(self)
        self.roi_window = ROISettingsWindow(self)

        self.build_ui()
        self.update_frames()

    @property
    def current_state(self):
        return self.state_manager.current_state

    @property
    def monitor_state(self):
        return self.state_manager.monitor_state

    @property
    def occupied_elapsed(self):
        return self.state_manager.occupied_elapsed

    @property
    def unattended_elapsed(self):
        return self.state_manager.unattended_elapsed

    def build_ui(self):
        title_label = tk.Label(
            self.root,
            text="Smart Library: Camera-Based Desk Occupancy Detection and Notification System",
            font=("Arial", 18, "bold"),
            bg="#f2f2f2"
        )
        title_label.pack(pady=10)

        cameras_frame = tk.Frame(self.root, bg="#f2f2f2")
        cameras_frame.pack(pady=10)

        self.left_panel = tk.Frame(cameras_frame, bg="white", bd=2, relief="groove")
        self.left_panel.pack(side="left", padx=15)

        tk.Label(
            self.left_panel,
            text="Camera 1 - Desk / Object View",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(pady=5)

        self.left_camera_label = tk.Label(self.left_panel, bg="black")
        self.left_camera_label.pack(padx=10, pady=10)

        self.object_status_label = tk.Label(
            self.left_panel,
            text="Item Status: WAITING",
            font=("Arial", 12, "bold"),
            width=42,
            height=2,
            bg="lightgray"
        )
        self.object_status_label.pack(pady=8)

        self.right_panel = tk.Frame(cameras_frame, bg="white", bd=2, relief="groove")
        self.right_panel.pack(side="left", padx=15)

        tk.Label(
            self.right_panel,
            text="Camera 2 - Person View",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(pady=5)

        self.right_camera_label = tk.Label(self.right_panel, bg="black")
        self.right_camera_label.pack(padx=10, pady=10)

        self.person_status_label = tk.Label(
            self.right_panel,
            text="Person Status: WAITING",
            font=("Arial", 12, "bold"),
            width=42,
            height=2,
            bg="lightgray"
        )
        self.person_status_label.pack(pady=8)

        info_frame = tk.Frame(self.root, bg="#f2f2f2")
        info_frame.pack(pady=15)

        self.general_state_label = tk.Label(
            info_frame,
            text="Desk State: EMPTY",
            font=("Arial", 14, "bold"),
            width=22,
            height=2,
            bg="lightgray"
        )
        self.general_state_label.grid(row=0, column=0, padx=8, pady=8)

        self.occupied_timer_label = tk.Label(
            info_frame,
            text="Occupied Time: 00:00",
            font=("Arial", 14, "bold"),
            width=22,
            height=2,
            bg="#d9edf7"
        )
        self.occupied_timer_label.grid(row=0, column=1, padx=8, pady=8)

        self.unattended_timer_label = tk.Label(
            info_frame,
            text="Unattended Time: 00:00",
            font=("Arial", 14, "bold"),
            width=22,
            height=2,
            bg="#fcf8e3"
        )
        self.unattended_timer_label.grid(row=0, column=2, padx=8, pady=8)

        self.remaining_timer_label = tk.Label(
            info_frame,
            text="Time Left to Violation: 01:00",
            font=("Arial", 14, "bold"),
            width=26,
            height=2,
            bg="#f5f5f5"
        )
        self.remaining_timer_label.grid(row=0, column=3, padx=8, pady=8)

        self.monitor_state_label = tk.Label(
            self.root,
            text="System Monitor: IDLE - NO TIMER RUNNING",
            font=("Arial", 14, "bold"),
            width=55,
            height=2,
            bg="#e2e3e5"
        )
        self.monitor_state_label.pack(pady=8)

        self.runtime_status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 11, "bold"),
            width=84,
            height=2,
            bg="#eef3f7"
        )
        self.runtime_status_label.pack(pady=6)

        self.update_runtime_status_label()

        config_frame = tk.LabelFrame(
            self.root,
            text="Break Time Configuration Panel",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=15,
            bg="#f2f2f2"
        )
        config_frame.pack(pady=10)

        tk.Label(
            config_frame,
            text="Violation Timeout (seconds):",
            font=("Arial", 12),
            bg="#f2f2f2"
        ).grid(row=0, column=0, padx=10, pady=10)

        self.timeout_entry = tk.Entry(config_frame, font=("Arial", 12), width=10)
        self.timeout_entry.grid(row=0, column=1, padx=10, pady=10)
        self.timeout_entry.insert(0, str(self.timeout_seconds))

        tk.Button(
            config_frame,
            text="Apply",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
            command=self.apply_timeout
        ).grid(row=0, column=2, padx=10, pady=10)

        tk.Button(
            config_frame,
            text="Settings",
            font=("Arial", 12, "bold"),
            bg="#5bc0de",
            fg="white",
            width=12,
            command=self.settings_window.open
        ).grid(row=0, column=3, padx=10, pady=10)

        tk.Button(
            config_frame,
            text="ROI Settings",
            font=("Arial", 12, "bold"),
            bg="#7a5af8",
            fg="white",
            width=12,
            command=self.roi_window.open
        ).grid(row=0, column=4, padx=10, pady=10)

        tk.Button(
            config_frame,
            text="Reset Timers",
            font=("Arial", 12, "bold"),
            bg="#f0ad4e",
            fg="white",
            width=12,
            command=self.reset_timers
        ).grid(row=0, column=5, padx=10, pady=10)

        tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 12, "bold"),
            bg="#d9534f",
            fg="white",
            width=14,
            command=self.close_app
        ).pack(pady=15)

    def apply_timeout(self):
        try:
            new_timeout = int(self.timeout_entry.get())
            if new_timeout <= 0:
                raise ValueError

            self.timeout_seconds = new_timeout
            self.config["timeout_seconds"] = new_timeout
            save_config(self.config)

            messagebox.showinfo(
                "Configuration Updated",
                f"Violation timeout updated to {new_timeout} seconds."
            )
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid positive integer."
            )

    def reset_timers(self):
        self.state_manager.reset()

    def update_runtime_status_label(self):
        self.runtime_status_label.config(
            text=(
                f"Runtime Detection Stability | "
                f"Item Hold: {self.item_hold_time:.1f} sec | "
                f"Person Hold: {self.person_hold_time:.1f} sec | "
                f"ROI: {'ON' if self.roi_enabled else 'OFF'}"
            )
        )

    def get_state_color(self, state):
        if state == "EMPTY":
            return "lightgray"
        if state == "OCCUPIED":
            return "lightgreen"
        if state == "UNATTENDED":
            return "yellow"
        if state == "VIOLATION":
            return "#ff4d4d"
        return "lightgray"

    def get_monitor_color(self):
        if self.monitor_state == "IDLE - NO TIMER RUNNING":
            return "#e2e3e5"
        if self.monitor_state == "MONITORING OCCUPIED DESK":
            return "#d9edf7"
        if self.monitor_state == "UNATTENDED TIMER ACTIVE":
            return "#fff3cd"
        if self.monitor_state == "VIOLATION DETECTED":
            return "#f8d7da"
        return "#e2e3e5"

    def show_alert(self, elapsed_seconds):
        if self.alert_open:
            return

        self.alert_open = True
        messagebox.showwarning(
            "Occupancy Alert",
            f"{self.desk_id} violation detected.\nElapsed unattended time: {int(elapsed_seconds)} seconds"
        )
        self.alert_open = False

    def update_frames(self):
        ret_obj, frame_obj = self.cap_object.read()
        ret_per, frame_per = self.cap_person.read()

        if not ret_obj:
            frame_obj = create_no_signal_frame("Object Camera: No Signal")
            object_logic_detections = []
        else:
            frame_obj = cv2.resize(frame_obj, (640, 480))
            self.latest_object_frame_for_roi = frame_obj.copy()

            display_frame = frame_obj.copy()
            _, display_frame = detect_filtered(
                display_frame,
                target_mode="display_non_person",
                confidence_threshold=self.confidence_threshold
            )

            object_logic_detections = []

            if self.roi_enabled and self.roi_x2 > self.roi_x1 and self.roi_y2 > self.roi_y1:
                roi_crop = safe_crop(frame_obj, self.roi_x1, self.roi_y1, self.roi_x2, self.roi_y2)
                if roi_crop is not None:
                    object_logic_detections, _ = detect_filtered(
                        roi_crop,
                        target_mode="items_only",
                        confidence_threshold=self.confidence_threshold
                    )

                cv2.rectangle(
                    display_frame,
                    (self.roi_x1, self.roi_y1),
                    (self.roi_x2, self.roi_y2),
                    (255, 0, 255),
                    2
                )
                cv2.putText(
                    display_frame,
                    "ROI",
                    (self.roi_x1, max(20, self.roi_y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 0, 255),
                    2
                )
            else:
                object_logic_detections, _ = detect_filtered(
                    frame_obj.copy(),
                    target_mode="items_only",
                    confidence_threshold=self.confidence_threshold
                )

            frame_obj = display_frame

        if not ret_per:
            frame_per = create_no_signal_frame("Person Camera: No Signal")
            person_detections = []
        else:
            frame_per = cv2.resize(frame_per, (640, 480))
            person_detections, frame_per = detect_filtered(
                frame_per,
                target_mode="person_only",
                confidence_threshold=self.confidence_threshold
            )

        raw_item_exists = contains_item(object_logic_detections)
        raw_person_exists = contains_person(person_detections)

        state_result = self.state_manager.update(
            raw_item_exists=raw_item_exists,
            raw_person_exists=raw_person_exists,
            item_hold_time=self.item_hold_time,
            person_hold_time=self.person_hold_time,
            timeout_seconds=self.timeout_seconds,
        )

        item_exists = state_result["item_exists"]
        person_exists = state_result["person_exists"]

        if state_result["violation_now"]:
            write_log(self.desk_id, self.current_state, self.unattended_elapsed)
            self.show_alert(self.unattended_elapsed)

        self.update_status_panels(item_exists, person_exists, object_logic_detections)

        frame_obj_rgb = cv2.cvtColor(frame_obj, cv2.COLOR_BGR2RGB)
        frame_per_rgb = cv2.cvtColor(frame_per, cv2.COLOR_BGR2RGB)

        img_obj = Image.fromarray(frame_obj_rgb)
        img_per = Image.fromarray(frame_per_rgb)

        imgtk_obj = ImageTk.PhotoImage(image=img_obj)
        imgtk_per = ImageTk.PhotoImage(image=img_per)

        self.left_camera_label.imgtk = imgtk_obj
        self.left_camera_label.configure(image=imgtk_obj)

        self.right_camera_label.imgtk = imgtk_per
        self.right_camera_label.configure(image=imgtk_per)

        self.root.after(30, self.update_frames)

    def update_status_panels(self, item_exists, person_exists, object_logic_detections):
        if item_exists:
            item_names = ", ".join(sorted(set([name for name, _ in object_logic_detections])))
            if not item_names.strip():
                item_names = "ITEM DETECTED"

            self.object_status_label.config(
                text=f"Item Status: {item_names.upper()}",
                bg="#ffd27f"
            )
        else:
            self.object_status_label.config(
                text="Item Status: NO ITEM",
                bg="lightgray"
            )

        if person_exists:
            self.person_status_label.config(
                text="Person Status: PERSON DETECTED",
                bg="lightgreen"
            )
        else:
            self.person_status_label.config(
                text="Person Status: NO PERSON",
                bg="#f5c6cb"
            )

        state_color = self.get_state_color(self.current_state)
        self.general_state_label.config(
            text=f"Desk State: {self.current_state}",
            bg=state_color
        )

        self.occupied_timer_label.config(
            text=f"Occupied Time: {format_seconds(self.occupied_elapsed)}"
        )

        self.unattended_timer_label.config(
            text=f"Unattended Time: {format_seconds(self.unattended_elapsed)}"
        )

        if self.current_state in ["UNATTENDED", "VIOLATION"]:
            remaining = max(0, self.timeout_seconds - int(self.unattended_elapsed))
            self.remaining_timer_label.config(
                text=f"Time Left to Violation: {format_seconds(remaining)}",
                bg="#fff3cd" if remaining > 0 else "#ffb3b3"
            )
        else:
            self.remaining_timer_label.config(
                text=f"Time Left to Violation: {format_seconds(self.timeout_seconds)}",
                bg="#f5f5f5"
            )

        self.monitor_state_label.config(
            text=f"System Monitor: {self.monitor_state}",
            bg=self.get_monitor_color()
        )

        self.update_runtime_status_label()

    def close_app(self):
        self.cap_object.release()
        self.cap_person.release()
        self.root.destroy()