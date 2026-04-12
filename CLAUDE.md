# CLAUDE.md — Pi Photobooth v2

## Project summary

Raspberry Pi photobooth for parties. Single physical button triggers a 4-photo session. Flask serves both the kiosk display (Chromium fullscreen on the Pi) and the guest gallery / admin web UI over a local WiFi AP. See `SPEC.md` for full detail.

---

## Tech stack

- **Python 3.11+** / Flask
- **Frontend:** HTML + CSS + Vanilla JS (no framework)
- **Camera:** Picamera2
- **GPIO:** gpiozero (button on GPIO 18, SSR/light on GPIO 11)
- **Image processing:** Pillow
- **QR code:** qrcode
- **Network:** hostapd + dnsmasq (AP mode), mDNS `photobooth.local`

---

## File layout

```
app.py                # Flask app — routes, GPIO wiring, camera, state machine
gpio_handler.py       # Button debounce, SSR control
camera_handler.py     # Photo capture via Picamera2
image_processor.py    # Resize/crop/blur/text-overlay pipeline
config.py             # All tuneable values — change here, never hardcode
static/css/style.css  # All styles — kiosk + web
static/js/app.js      # Frontend polling + UI logic
static/splash/        # 8 processed splash images (written at upload time)
templates/            # kiosk.html, gallery.html, admin.html, slideshow.html, …
photos/[event-id]/    # full/ and thumbs/ per event
uploads/              # Raw splash uploads (pre-processing only)
```

---

## Key conventions

- **All config in `config.py`** — never hardcode values in application files.
- **No processing at runtime.** Splash images are processed once at upload. Thumbnails are generated immediately after capture. Nothing CPU-heavy happens during a session.
- **Background threads** for image processing — never block the state machine.
- **8-bit arcade aesthetic** everywhere — pixel fonts, hard edges, no gradients, no rounded corners, stepped animations. This applies to every UI surface.

---

## Development workflow

- Frontend (HTML/CSS/JS) is developed locally on a laptop — no Pi needed for UI work.
- Flask runs locally with GPIO and camera **stubbed out** (no Pi required).
- Hardware testing (GPIO, camera, AP, boot) happens on the Pi.
- Deploy to Pi via `git pull` over SSH.
- After any change: verify Python syntax, trace logic, test in browser.

---

## Photo session state machine

| State | Name        | Light | Notes                                      |
|-------|-------------|-------|--------------------------------------------|
| 1     | Home        | OFF   | Idle, QR code shown, waiting for button    |
| 2     | Pose        | ON    | SSR fires, 2 s pause                       |
| 3–6   | Countdown   | ON    | 4 captures, thumbnails generated inline    |
| 7     | Processing  | ON    | Polaroid borders applied in bg thread      |
| 8     | Done/Review | OFF   | Polaroids displayed, timeout → State 1     |

---

## Performance targets

| Event                          | Target  |
|-------------------------------|---------|
| Button press → light on       | < 100 ms |
| State transitions             | < 300 ms |
| Photo capture → next state    | < 1 s   |
| Gallery page load (20 photos) | < 3 s   |

---

## GPIO

| Pin     | Component | Behaviour                                    |
|---------|-----------|----------------------------------------------|
| GPIO 18 | Button    | Pull-up, active LOW, 50 ms debounce          |
| GPIO 11 | SSR/light | HIGH = ON (states 2–6), LOW = OFF otherwise  |

---

## Network modes

- **dev** — Pi joins home WiFi as client, no AP. Used for development.
- **standalone** — Pi broadcasts AP only. Guests connect directly.
- **networked** — Pi joins venue WiFi AND broadcasts AP simultaneously (2.4 GHz only).

---

## Things to watch out for

- Pi 3+ has 1 GB RAM — avoid loading full-res images into memory at request time. Always serve thumbs in the gallery grid.
- `hostapd`/`dnsmasq` config changes require a service restart — changes via `/admin/wifi` must handle this.
- Chromium kiosk launches via systemd on boot — any Flask startup error will leave the screen blank. Keep startup path lean.
- GPIO operations must never block the Flask main thread.

---

## Working rules

- **Phase-gated.** Build one phase at a time (see `SPEC.md` Phase Plan). Do not begin the next phase without explicit permission.
- **No unsolicited changes.** Do not modify or delete files outside this project directory.
- **Suggest, don't implement.** Raise suggestions during development, but wait for confirmation before making any change that wasn't part of the agreed phase scope.
- **No assumptions.** If something is unclear, ask rather than guess.
- **Optimise by default.** All code written for Pi 3 constraints: 1 GB RAM, ARMv8 single-core performance. Prefer low memory footprint, minimal blocking, and fast startup over convenience abstractions.
- **Hardware awareness.** GPIO, Picamera2, and AP/networking code must account for Pi 3 hardware limits. Test paths on Pi before marking hardware phases complete.
- **Deployment path.** Changes are deployed to the Pi via `git pull` over SSH. Do not attempt to deploy directly — never SCP, rsync, or push directly to the Pi.
- **Python compatibility.** All Python must be compatible with Python 3.11 on Raspberry Pi OS Bookworm. Verify before using any library or language feature.
- **No compiled dependencies.** Do not use libraries that require compilation unless they are confirmed available via `apt` or `pip` on Bookworm. Prefer pure-Python packages or packages with pre-built ARM wheels.
