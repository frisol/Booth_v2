import threading
import time

import config
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Hardware detection — imports attempted but never fatal on non-Pi hardware.
# GPIO_AVAILABLE / CAMERA_AVAILABLE guard hardware calls in later phases.
# ---------------------------------------------------------------------------
try:
    import gpiozero  # noqa: F401
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    from picamera2 import Picamera2  # noqa: F401
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
# State 1–8 matching the spec state machine.
# Mutated only inside state_lock.
state_lock     = threading.Lock()
current_state  = 1
session_photos = []   # URL strings populated as each capture occurs (states 3–6)


def t(real_val):
    """Return DEV_DELAY when DEV_MODE is on, otherwise the real value."""
    return config.DEV_DELAY if config.DEV_MODE else real_val


def run_session():
    """
    Drive states 2–8 in a background thread.
    Called once per session, spawned by /trigger.
    Each state sleeps for its configured duration then advances.
    """
    global current_state, session_photos

    # --- State 2: Pose ---
    time.sleep(t(config.POSE_DELAY))
    with state_lock:
        current_state = 3

    # --- States 3–6: Countdown & capture ---
    for photo_num in range(1, 5):
        time.sleep(t(config.COUNTDOWN_DURATION))
        with state_lock:
            session_photos.append("/static/dev/llama_{}.png".format(photo_num))
            # 3→4, 4→5, 5→6, 6→7
            current_state = 3 + photo_num

    # --- State 7: Processing ---
    time.sleep(t(config.PROCESSING_DELAY))
    with state_lock:
        current_state = 8

    # --- State 8: Review ---
    # Hold long enough for guests to see all 4 photos in the grid.
    hold = t(config.REVIEW_HOLD_DURATION)
    time.sleep(hold)
    with state_lock:
        current_state = 1
        session_photos = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def kiosk():
    return render_template("kiosk.html")


@app.route("/status")
def status():
    with state_lock:
        state  = current_state
        photos = list(session_photos)
    return jsonify({
        "state":      state,
        "event_name": config.CURRENT_EVENT_NAME,
        "photos":     photos,
        "dev_mode":   config.DEV_MODE,
    })


@app.route("/trigger", methods=["POST"])
def trigger():
    """Start a photo session. Only accepted when in state 1 (Home)."""
    global current_state
    with state_lock:
        if current_state != 1:
            return jsonify({"error": "session already in progress"}), 409
        current_state = 2

    thread = threading.Thread(target=run_session, daemon=True)
    thread.start()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.DEBUG,
    )
