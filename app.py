import tkinter as tk
from ui.main_window import SmartLibraryApp


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartLibraryApp(root)
    root.mainloop()