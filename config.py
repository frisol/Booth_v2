# config.py — all tuneable values. Change here, never in application files.

# Flask
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DEBUG = False

# Development
DEV_MODE = True    # Shorten all delays to DEV_DELAY for local testing
DEV_DELAY = 2    # Seconds — replaces all timing values when DEV_MODE = True

# Event
CURRENT_EVENT_NAME = "My Party"
CURRENT_EVENT_ID = "default"

# Timing (seconds)
POSE_DELAY            = 2
COUNTDOWN_DURATION    = 1
BETWEEN_CAPTURES_DELAY = 0.5   # seconds light stays off between captures
PROCESSING_DELAY      = 2
REVIEW_HOLD_DURATION  = 8   # Seconds state 8 (review grid) is held before returning to home
SLIDESHOW_INTERVAL    = 5

# Camera
PHOTO_RESOLUTION = (1600, 1200)

# Network
AP_SSID = "Photobooth"
AP_PASSWORD = ""             # Empty string = open network
NETWORK_MODE = "standalone"  # "dev" | "standalone" | "networked"

# Image processing
BLUR_RADIUS = 10
OVERLAY_FONT_SIZE = 120

# Admin
ADMIN_PASSWORD = "changeme"

# GPIO
BUTTON_PIN = 24 # Physical pin 18 = GPIO 24
LIGHT_PIN  = 17 # Physical pin 11 = GPIO 17
DEBOUNCE_S = 0.05   # 50 ms

# Storage
PHOTOS_DIR = "photos"
MAX_EVENTS_STORED = 10       # Oldest event auto-archived beyond this
