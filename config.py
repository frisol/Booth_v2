# config.py — all tuneable values. Change here, never in application files.

# Flask
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DEBUG = False

# Event
CURRENT_EVENT_NAME = "My Party"
CURRENT_EVENT_ID = "default"

# Timing (seconds)
POSE_DELAY = 2
COUNTDOWN_DURATION = 1
REVIEW_HOLD_DURATION = 10
SLIDESHOW_INTERVAL = 5

# Camera
PHOTO_RESOLUTION = (1600, 1200)

# Network
AP_SSID = "Photobooth"
AP_PASSWORD = ""            # Empty string = open network
NETWORK_MODE = "standalone"  # "dev" | "standalone" | "networked"

# Image processing
BLUR_RADIUS = 10
OVERLAY_FONT_SIZE = 120

# Admin
ADMIN_PASSWORD = "changeme"

# Storage
PHOTOS_DIR = "photos"
MAX_EVENTS_STORED = 10      # Oldest event auto-archived beyond this
