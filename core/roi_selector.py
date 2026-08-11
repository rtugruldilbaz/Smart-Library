import cv2


def select_roi_with_mouse(frame):
    """
    Mouse drag + release => auto save
    Esc => cancel
    Window X => cancel
    """
    window_name = "Set ROI - Object Camera"

    state = {
        "drawing": False,
        "finished": False,
        "x1": 0,
        "y1": 0,
        "x2": 0,
        "y2": 0
    }

    base_frame = frame.copy()

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            state["drawing"] = True
            state["x1"] = x
            state["y1"] = y
            state["x2"] = x
            state["y2"] = y

        elif event == cv2.EVENT_MOUSEMOVE and state["drawing"]:
            state["x2"] = x
            state["y2"] = y

        elif event == cv2.EVENT_LBUTTONUP:
            state["drawing"] = False
            state["x2"] = x
            state["y2"] = y

            x1 = min(state["x1"], state["x2"])
            y1 = min(state["y1"], state["y2"])
            x2 = max(state["x1"], state["x2"])
            y2 = max(state["y1"], state["y2"])

            if x2 > x1 and y2 > y1:
                state["finished"] = True

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, mouse_callback)

    try:
        while True:
            try:
                visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                if visible < 1:
                    return None
            except cv2.error:
                return None

            display = base_frame.copy()

            x1 = min(state["x1"], state["x2"])
            y1 = min(state["y1"], state["y2"])
            x2 = max(state["x1"], state["x2"])
            y2 = max(state["y1"], state["y2"])

            if x2 > x1 and y2 > y1:
                cv2.rectangle(display, (x1, y1), (x2, y2), (255, 0, 255), 2)

            cv2.putText(
                display,
                "Drag ROI and release mouse to save | Esc or X to cancel",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.58,
                (0, 255, 0),
                2
            )

            cv2.imshow(window_name, display)

            if state["finished"]:
                return (x1, y1, x2, y2)

            key = cv2.waitKey(20) & 0xFF
            if key == 27:
                return None
    finally:
        cv2.destroyAllWindows()
        cv2.waitKey(1)