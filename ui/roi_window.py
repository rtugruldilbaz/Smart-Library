import tkinter as tk
from tkinter import messagebox

from core.config_manager import save_config
from ui.ui_helpers import center_toplevel
from core.roi_selector import select_roi_with_mouse


class ROISettingsWindow:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.window = None
        self.roi_enabled_var = None
        self.roi_status_label = None

    def open(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent_app.root)
        self.window.title("ROI Settings")
        self.window.configure(bg="#f7f7f7")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        center_toplevel(self.window, self.parent_app.root, 520, 320)

        container = tk.LabelFrame(
            self.window,
            text="Desk ROI Settings",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=15,
            bg="#f7f7f7"
        )
        container.pack(padx=20, pady=20, fill="both", expand=True)

        self.roi_enabled_var = tk.BooleanVar(value=self.parent_app.roi_enabled)

        tk.Checkbutton(
            container,
            text="Enable ROI for object camera logic",
            variable=self.roi_enabled_var,
            font=("Arial", 11),
            bg="#f7f7f7",
            command=self.toggle_roi_enabled
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        self.roi_status_label = tk.Label(
            container,
            text=self.get_roi_status_text(),
            font=("Arial", 10, "bold"),
            bg="#eef3f7",
            width=50,
            height=2
        )
        self.roi_status_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        tk.Label(
            container,
            text="After Set ROI: drag and release to save | Esc/X = cancel",
            font=("Arial", 10),
            bg="#f7f7f7",
            fg="#444444"
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        tk.Button(
            container,
            text="Set ROI",
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            width=16,
            command=self.set_roi_interactively
        ).grid(row=3, column=0, padx=10, pady=10)

        tk.Button(
            container,
            text="Clear ROI",
            font=("Arial", 11, "bold"),
            bg="#f0ad4e",
            fg="white",
            width=16,
            command=self.clear_roi
        ).grid(row=3, column=1, padx=10, pady=10)

        tk.Button(
            container,
            text="Close",
            font=("Arial", 11, "bold"),
            bg="#6c757d",
            fg="white",
            width=16,
            command=self.close
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=15)

    def get_roi_status_text(self):
        if self.parent_app.roi_x2 > self.parent_app.roi_x1 and self.parent_app.roi_y2 > self.parent_app.roi_y1:
            return (
                f"Saved ROI: ({self.parent_app.roi_x1}, {self.parent_app.roi_y1}) - "
                f"({self.parent_app.roi_x2}, {self.parent_app.roi_y2})"
            )
        return "Saved ROI: None"

    def toggle_roi_enabled(self):
        self.parent_app.roi_enabled = self.roi_enabled_var.get()
        self.parent_app.config["roi_enabled"] = self.parent_app.roi_enabled
        save_config(self.parent_app.config)
        self.parent_app.update_runtime_status_label()

        if self.roi_status_label is not None:
            self.roi_status_label.config(text=self.get_roi_status_text())

    def clear_roi(self):
        self.parent_app.roi_x1 = 0
        self.parent_app.roi_y1 = 0
        self.parent_app.roi_x2 = 0
        self.parent_app.roi_y2 = 0

        self.parent_app.config["roi_x1"] = 0
        self.parent_app.config["roi_y1"] = 0
        self.parent_app.config["roi_x2"] = 0
        self.parent_app.config["roi_y2"] = 0
        save_config(self.parent_app.config)

        if self.roi_status_label is not None:
            self.roi_status_label.config(text=self.get_roi_status_text())

        messagebox.showinfo("ROI Cleared", "Saved ROI coordinates were cleared.")

    def set_roi_interactively(self):
        if self.parent_app.latest_object_frame_for_roi is None:
            messagebox.showerror("ROI Error", "Object camera frame is not ready yet.")
            return

        self.close()

        messagebox.showinfo(
            "Set ROI",
            "Drag and release the mouse to save the ROI.\n\n"
            "You can cancel with Esc or the window X button."
        )

        result = select_roi_with_mouse(self.parent_app.latest_object_frame_for_roi.copy())

        if result is None:
            messagebox.showwarning("ROI Cancelled", "ROI selection cancelled.")
            return

        (
            self.parent_app.roi_x1,
            self.parent_app.roi_y1,
            self.parent_app.roi_x2,
            self.parent_app.roi_y2,
        ) = result

        self.parent_app.config["roi_x1"] = self.parent_app.roi_x1
        self.parent_app.config["roi_y1"] = self.parent_app.roi_y1
        self.parent_app.config["roi_x2"] = self.parent_app.roi_x2
        self.parent_app.config["roi_y2"] = self.parent_app.roi_y2
        save_config(self.parent_app.config)

        messagebox.showinfo("ROI Saved", "ROI saved successfully.")

    def close(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        self.window = None