import tkinter as tk
from tkinter import messagebox

from core.config_manager import save_config
from ui.ui_helpers import center_toplevel


class SettingsWindow:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.window = None
        self.item_hold_entry = None
        self.person_hold_entry = None

    def open(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent_app.root)
        self.window.title("Advanced Detection Settings")
        self.window.configure(bg="#f7f7f7")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        center_toplevel(self.window, self.parent_app.root, 420, 220)

        container = tk.LabelFrame(
            self.window,
            text="Runtime Detection Settings",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=15,
            bg="#f7f7f7"
        )
        container.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(
            container,
            text="Item Hold Time (sec):",
            font=("Arial", 11),
            bg="#f7f7f7"
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.item_hold_entry = tk.Entry(container, font=("Arial", 11), width=10)
        self.item_hold_entry.grid(row=0, column=1, padx=10, pady=10)
        self.item_hold_entry.insert(0, str(self.parent_app.item_hold_time))

        tk.Label(
            container,
            text="Person Hold Time (sec):",
            font=("Arial", 11),
            bg="#f7f7f7"
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.person_hold_entry = tk.Entry(container, font=("Arial", 11), width=10)
        self.person_hold_entry.grid(row=1, column=1, padx=10, pady=10)
        self.person_hold_entry.insert(0, str(self.parent_app.person_hold_time))

        tk.Button(
            container,
            text="Apply",
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
            command=self.apply
        ).grid(row=2, column=0, padx=10, pady=15)

        tk.Button(
            container,
            text="Close",
            font=("Arial", 11, "bold"),
            bg="#6c757d",
            fg="white",
            width=12,
            command=self.close
        ).grid(row=2, column=1, padx=10, pady=15)

    def apply(self):
        try:
            new_item_hold = float(self.item_hold_entry.get())
            new_person_hold = float(self.person_hold_entry.get())

            if new_item_hold < 0 or new_person_hold < 0:
                raise ValueError

            self.parent_app.item_hold_time = new_item_hold
            self.parent_app.person_hold_time = new_person_hold

            self.parent_app.config["item_hold_time"] = new_item_hold
            self.parent_app.config["person_hold_time"] = new_person_hold
            save_config(self.parent_app.config)

            self.parent_app.update_runtime_status_label()

            messagebox.showinfo(
                "Runtime Settings Updated",
                "Item Hold Time and Person Hold Time updated."
            )
            self.close()

        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid non-negative numeric values."
            )

    def close(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        self.window = None