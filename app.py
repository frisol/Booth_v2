import config
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Hardware detection — imports are attempted but never fatal on non-Pi hardware.
# GPIO_AVAILABLE and CAMERA_AVAILABLE are used by later phases to guard hardware calls.
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

# Session state — single integer matching the state machine (1–8).
# Mutated by the GPIO/session logic added in later phases.
current_state = 1


@app.route("/")
def kiosk():
    return render_template("kiosk.html")


@app.route("/status")
def status():
    return jsonify({
        "state": current_state,
        "event_name": config.CURRENT_EVENT_NAME,
    })


if __name__ == "__main__":
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.DEBUG,
    )
