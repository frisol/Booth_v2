# Pi Photobooth — Project Specification

## Overview

A Raspberry Pi powered photobooth designed for parties and events.
Guests interact via a single physical button. The booth captures
four photos per session, displays them back as polaroids, and
allows guests to browse the gallery on their own phones via a
local WiFi access point. An admin interface allows the booth
owner to customise splash screens and manage events before and
after an event.

**Audience:** Ages 5–60. Interface must be operable with zero instructions.

---

## Hardware

| Component  | Detail                             |
|------------|------------------------------------|
| Board      | Raspberry Pi 3+                    |
| Camera     | PiCamera (attached) — confirmed working. CLI tool on Bookworm is `rpicam-still`, not `libcamera-hello` |
| Display    | LCD monitor 1600×1200 (4:3 ratio)  |
| Input      | 1 physical button — GPIO 24 (physical pin 18) |
| Lighting   | LED downlight via SSR — GPIO 17 (physical pin 11) |
| Housing    | Plywood enclosure                  |

---

## Tech Stack

| Layer            | Technology                          |
|-----------------|-------------------------------------|
| OS              | Raspberry Pi OS Bookworm            |
| Language        | Python 3.11+                        |
| Backend         | Flask                               |
| Display         | Chromium browser in kiosk mode      |
| Frontend        | HTML / CSS / Vanilla JS             |
| GPIO            | gpiozero                            |
| Image processing| Pillow                              |
| Access point    | hostapd + dnsmasq                   |
| Camera          | Picamera2                           |
| QR code         | qrcode (Python library)             |

---

## File Structure

```
photobooth_v2/
├── app.py                  # Flask app — routes, GPIO, camera
├── gpio_handler.py         # Button and SSR logic
├── camera_handler.py       # Photo capture logic
├── image_processor.py      # Resize, crop, blur, overlay text
├── config.py               # All configurable values
├── generate_dev_assets.py  # One-time script: generates dummy images for dev/testing
├── static/
│   ├── css/
│   │   └── style.css       # All styles — kiosk + web UI
│   ├── js/
│   │   └── app.js          # Frontend logic
│   ├── splash/             # 8 processed splash screen images
│   └── dev/                # Dev-only assets (dummy photos, llama animation frames)
├── templates/
│   ├── kiosk.html          # Fullscreen booth display
│   ├── gallery.html        # Guest photo gallery
│   ├── admin.html          # Admin dashboard
│   ├── admin_wifi.html     # WiFi configuration
│   ├── admin_events.html   # Event management
│   └── slideshow.html      # Fullscreen slideshow
├── photos/                 # Captured photos organised by event
│   └── [event-id]/         # One folder per event
│       ├── full/           # Full resolution photos
│       └── thumbs/         # Thumbnails (generated at capture)
├── uploads/                # Raw splash uploads (pre-processing)
├── SPEC.md
└── CLAUDE.md
```

---

## Visual Style

- **8-bit arcade aesthetic** throughout all interfaces
- Pixel art typography — bitmap/monospace font
- Hard pixel edges — no rounded corners, no gradients, no smooth shadows
- Bold limited colour palette consistent with retro games
- Animations are blocky and stepped, not fluid
- Applies equally to the kiosk display and all web interfaces

---

## System Architecture

Flask serves two roles simultaneously:

1. **Kiosk display** — `kiosk.html` loaded by Chromium in fullscreen
   kiosk mode on boot. Communicates with Flask via polling to receive
   state updates (e.g. "photo taken", "session complete").

2. **Web server** — when guests connect to the Pi's access point,
   they browse to `http://photobooth.local` and see the gallery.
   Admin navigates to `http://photobooth.local/admin`.

GPIO events (button press) are handled by a background thread in
Flask, which triggers the photo sequence and pushes state updates
to the kiosk display.

---

## Photo Session Flow

### State 1 — Home Screen
- Displays splash image 1 with text overlay "Push the button"
- QR code displayed in corner pointing to `http://photobooth.local`
- 8-bit idle animation plays on screen
- Waiting for button press (GPIO 24)

### State 2 — Strike a Pose
- Button pressed — SSR remains OFF, no light during pose
- Displays splash image 2 with text overlay "Strike a pose"
- Brief pause (configurable, default 2 seconds)

### States 3–6 — Countdown & Capture (×4)
- For each of 4 photos:
  - Display splash image (3–6) with overlay "1", "2", "3", "4"
  - SSR ON — light fires as countdown splash appears
  - Brief countdown display (configurable)
  - Camera captures photo
  - SSR OFF — light off immediately after capture, before next state begins
  - Full resolution photo saved to `/photos/[event-id]/full/`
  - Thumbnail generated immediately and saved to `/photos/[event-id]/thumbs/`

### State 7 — Processing
- Displays splash image 7 with overlay "Processing"
- Polaroid borders applied to photos in background thread

### State 8 — All Done / Review
- Displays splash image 8 with overlay "All done"
- All 4 polaroid photos displayed simultaneously in a 2×2 grid:
  - Classic white polaroid border (thick bottom border)
  - Phase 8 adds: stacked layout with random rotation and animated card entry
- SSR already OFF (turned off after final capture in state 6)
- After timeout (configurable `REVIEW_HOLD_DURATION`), returns to State 1

---

## Polaroid Display

- Each photo rendered with a white border in classic polaroid style
- All 4 photos displayed simultaneously in a 2×2 grid after capture
- Phase 8 adds: stacked layout with randomised rotation (±5–10 degrees),
  cards animate in one at a time — blocky stepped movement, not smooth
- Display held for `REVIEW_HOLD_DURATION` seconds before returning to home screen

---

## Splash Screen Images

There are exactly 8 splash screen slots:

| Slot | Name       | Text Overlay      |
|------|------------|-------------------|
| 1    | home       | "Push the button" |
| 2    | pose       | "Strike a pose"   |
| 3    | photo_1    | "1"               |
| 4    | photo_2    | "2"               |
| 5    | photo_3    | "3"               |
| 6    | photo_4    | "4"               |
| 7    | processing | "Processing"      |
| 8    | done       | "All done"        |

### Processing Pipeline (applied automatically on upload)

1. **Resize/crop** to 1600×1200 (4:3), preserving aspect ratio, centre-cropped
2. **Blur** applied (Gaussian blur, configurable radius, default 10px) — background depth effect
3. **Text overlay** applied — 8-bit style font, large, centred, subtle drop shadow for legibility
4. **Saved** to `/static/splash/` replacing previous image for that slot

Processing runs at upload time only — never at runtime during a session.

---

## Admin Interface

### Dashboard (`/admin`)
- Password protected (single password, set in `config.py`)
- Overview of current event, photo count, storage used
- Links to all admin sections

### Splash Screen Manager (`/admin`)
- Displays 8 upload slots with current image thumbnails
- Upload accepts JPG and PNG
- Processing pipeline runs automatically on upload
- Thumbnail updates immediately in UI

### Event Management (`/admin/events`)
- Displays all past events with name, date, photo count
- **New Event** button — enter event name, creates new event folder,
  sets as active event
- All subsequent photos save to new event folder
- Guest gallery shows active event photos only
- Previous event photos preserved but not shown to guests

### Photo Management (per event)
- **Download all** — packages all photos from active event into
  a `.zip` file, triggers browser download
- **Clear event photos** — permanently deletes all photos from
  active event after confirmation prompt

### WiFi Settings (`/admin/wifi`)
- Scan and display available WiFi networks
- Save home WiFi credentials (persistent across reboots)
- Save event WiFi credentials (venue-specific, updated per event)
- Select active network mode (Dev / Standalone / Networked)
- Current connection status displayed

---

## Guest Gallery (`/`)

- Accessible at `http://photobooth.local`
- Shows photos from active event only in reverse chronological order
- Responsive grid layout — works on phones and laptop browsers
- Tap/click any photo to view full size
- Download button per photo
- **Download all** button — downloads all active event photos as `.zip`
- **Slideshow** button — opens `/slideshow` fullscreen
- 8-bit visual style throughout
- Read-only — no deletion for guests

---

## Slideshow Mode (`/slideshow`)

- Fullscreen mode — designed for event TV or laptop browser
- Randomised sequence of all photos from active event
- Each photo shown for configurable duration (default 5 seconds)
- 8-bit style transitions between photos
- No UI chrome — photos only
- Accessible on both the Pi's AP address and venue WiFi address

---

## QR Code

- Generated at runtime using the `qrcode` Python library
- Points to `http://photobooth.local`
- Displayed in a corner of the home screen (State 1)
- Small enough not to distract from the main display
- 8-bit styled border

---

## WiFi & Network Modes

Pi supports three network modes, selected via `/admin/wifi`.

### Mode 1 — Dev/Home
- Pi connects to home WiFi as client only
- No access point broadcast
- SSH, SCP, admin portal accessible on local network
- Used for development and post-event photo transfer

### Mode 2 — Event Standalone
- Pi broadcasts its own access point only
- No external WiFi connection
- Guests connect directly to Pi's AP
- Admin and gallery at `http://photobooth.local`

### Mode 3 — Event Networked (AP + STA)
- Pi connects to venue WiFi AND broadcasts its own AP simultaneously
- Guests on phones connect to Pi's AP → access gallery
- Event TV connects to venue WiFi → opens slideshow at Pi's venue IP
- Slideshow accessible on both network addresses automatically
- **Known limitation:** Both connections must be 2.4GHz.
  5GHz-only venue networks are not supported in this mode.

### First-Time WiFi Setup
- On first boot with no WiFi configured, Pi enters AP mode
- Admin connects to Pi's AP and navigates to `/admin/wifi`
- Scans for networks, selects, enters password
- Pi saves credentials and reboots into client mode

### Network Addressing

| Network     | Pi address             |
|-------------|------------------------|
| Pi's own AP | `192.168.4.1`          |
| Venue WiFi  | Assigned by venue DHCP |
| mDNS        | `photobooth.local`     |

---

## GPIO

| Pin      | Component        | Behaviour                                         |
|----------|-----------------|---------------------------------------------------|
| GPIO 24  | Physical button | Pull-up. Button press = LOW. Triggers photo       |
| (pin 18) |                 | sequence. Debounced (50ms).                       |
| GPIO 17  | SSR / LED light | HIGH = light ON. LOW = light OFF.                 |
| (pin 11) |                 | ON when countdown splash appears (states 3–6).    |
|          |                 | OFF after each capture and at all other times.    |
|          |                 | OFF during state 2 (pose) — no light needed.      |

---

## Performance Requirements

At all times the booth must feel responsive. A 5 year old
waiting for feedback is a bad experience.

### Response time targets
- Button press to light-on: < 100ms
- State transitions: < 300ms
- Photo capture to next state: < 1 second
- Gallery page load (20 photos): < 3 seconds on device

### Mitigation strategies
- Splash screen images fully processed at upload time — never at runtime
- Photo thumbnails generated immediately after capture — gallery always
  serves thumbnails, never full-res images for the grid view
- Image processing (Pillow operations) runs in background threads —
  never blocks the session state machine
- Flask serves static files directly — no dynamic asset generation at
  request time
- Chromium launched with memory-saving flags

### Hardware note
Pi 3+ (1GB RAM) is the minimum viable hardware for this stack.
A Pi 4 (2GB+) is recommended for comfortable headroom. If
performance issues arise on Pi 3+, upgrading the board is the
first resolution path — software stack and housing unchanged.

---

## Boot Splash

- Pi boot text suppressed
- Custom 8-bit splash screen displayed during boot
- "Loading Photobooth..." text in 8-bit style
- Implemented via Plymouth theme (Bookworm standard)
- Chromium kiosk launches automatically on boot via systemd service

---

## Configuration (`config.py`)

All tuneable values in one place. No hunting through code before an event.

```python
# Development
DEV_MODE = True    # Shorten all delays to DEV_DELAY for local testing
DEV_DELAY = 0.5    # Seconds — replaces all timing values when DEV_MODE = True

# Event
CURRENT_EVENT_NAME = "My Party"

# Timing (seconds)
POSE_DELAY            = 2
COUNTDOWN_DURATION    = 1
PROCESSING_DELAY      = 2
REVIEW_HOLD_DURATION  = 8   # Seconds state 8 (review grid) is held before returning to home
SLIDESHOW_INTERVAL    = 5

# Camera
PHOTO_RESOLUTION = (1600, 1200)

# Network
AP_SSID = "Photobooth"
AP_PASSWORD = ""           # Empty string = open network
NETWORK_MODE = "standalone" # "dev" | "standalone" | "networked"

# Image processing
BLUR_RADIUS = 10
OVERLAY_FONT_SIZE = 120

# Admin
ADMIN_PASSWORD = "changeme"

# Storage
PHOTOS_DIR = "photos"
MAX_EVENTS_STORED = 10     # Oldest event auto-archived beyond this
```

---

## Development Workflow

- Frontend (HTML/CSS/JS) developed and tested locally on laptop —
  no Pi required for UI work
- Flask backend run locally with GPIO and camera stubbed out
- Pi used only for hardware testing (GPIO, camera, access point, boot)
- After any code change: verify syntax, trace logic, test in browser
- Deploy to Pi via Git pull over SSH
- All configurable values changed in `config.py` only — never
  hardcoded in application files

---

## Phase Plan

| Phase | Scope                                                    | Status    |
|-------|----------------------------------------------------------|-----------|
| 0     | OS upgrade (Buster → Bookworm), Python 3 setup,          | Complete  |
|       | hardware verification, Git repo initialised              |           |
| 1     | Flask skeleton, Chromium kiosk mode, auto-launch         | Complete  |
|       | on boot via systemd                                      |           |
| 2     | Kiosk UI — full state machine UI with dummy data,        | Complete  |
|       | developed and tested locally (no hardware required)      |           |
| 3     | GPIO — button debounce and SSR control                   | Complete  |
| 4     | Camera capture with Picamera2                            |           |
| 5     | Photo session state machine (states 1–8)                 |           |
| 6     | Splash screen upload and processing pipeline             |           |
| 7     | Admin interface (dashboard, splash manager,              |           |
|       | event management, photo download/clear)                  |           |
| 8     | Polaroid display with stacking animation                 |           |
| 9     | Guest gallery with download                              |           |
| 10    | WiFi mode management (dev / standalone / networked)      |           |
| 11    | Slideshow mode                                           |           |
| 12    | QR code on home screen                                   |           |
| 13    | 8-bit animations throughout                              |           |
| 14    | Boot splash (Plymouth theme)                             |           |
