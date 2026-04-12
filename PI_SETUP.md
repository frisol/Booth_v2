# PI_SETUP.md — Pi Photobooth Setup Runbook

Step-by-step record of every configuration performed on the Pi during
Phase 0 and Phase 1. Follow these steps in order on a fresh Pi to
reproduce the working state.

---

## Hardware reference

| Component | Detail                            |
|-----------|-----------------------------------|
| Board     | Raspberry Pi 3+                   |
| Camera    | PiCamera (ribbon cable attached)  |
| Display   | LCD monitor 1600×1200 (4:3)       |
| Button    | Physical button — GPIO 18         |
| Light     | LED via SSR — GPIO 11             |

---

## Phase 0 — OS, Python, camera verification

### Step 1 — Flash the OS

Use **Raspberry Pi Imager** to flash **Raspberry Pi OS Bookworm Lite (64-bit)**
to the SD card.

In the Imager advanced options (gear icon) before writing:

- Set hostname: `photobooth`
- Enable SSH: yes (use password authentication)
- Set username: `pi`, choose a password
- Configure WiFi: enter home network credentials so the Pi is reachable on
  the local network immediately after first boot

Boot the Pi. Find its IP on the network and connect:

```bash
ssh pi@photobooth.local
# or ssh pi@<ip-address> if mDNS isn't resolving yet
```

### Step 2 — Update the OS

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3 — Verify Python version

Bookworm ships Python 3.11. Confirm before proceeding:

```bash
python3 --version
# Expected: Python 3.11.x
```

Do not use `python` (no unversioned alias). Always use `python3`.

### Step 4 — Enable the camera interface

```bash
sudo raspi-config nonint do_camera 0
```

Reboot to apply:

```bash
sudo reboot
```

### Step 5 — Verify the camera

Reconnect over SSH after reboot, then take a test shot:

```bash
rpicam-still -o /tmp/test.jpg
```

Expected: captures a JPEG with no errors.

> **Bookworm note:** The camera CLI is `rpicam-still`. The older commands
> `raspistill` and `libcamera-hello` are not available on Bookworm — do not
> use them. If `rpicam-still` fails, check that the ribbon cable is fully
> seated in both the Pi and camera connectors.

Inspect the test image to confirm focus and framing:

```bash
# Copy to local machine for inspection
scp pi@photobooth.local:/tmp/test.jpg ~/Desktop/test.jpg
```

### Step 6 — Set boot to console (no desktop)

The kiosk launches Chromium directly via `xinit` managed by systemd — no
desktop environment is needed or wanted.

```bash
sudo raspi-config nonint do_boot_behaviour B2
```

`B2` = Boot to console, auto-login as user `pi`. This is required so that
the `photobooth-kiosk.service` can acquire VT7 cleanly on boot without
conflicting with a running desktop session.

Reboot:

```bash
sudo reboot
```

---

## Phase 1 — Flask skeleton, kiosk display, systemd services

### Step 7 — Install xinit and xserver-xorg-legacy

The kiosk service runs `xinit` as user `pi` from a systemd unit (not from a
login shell). By default, X server restricts this. `xserver-xorg-legacy`
provides the compatibility layer that allows it.

```bash
sudo apt install -y xinit xserver-xorg-legacy
```

### Step 8 — Configure Xwrapper.config

Allow non-root users to start an X server (required for the systemd service
to launch Chromium via `xinit`):

Edit `/etc/X11/Xwrapper.config`:

```bash
sudo nano /etc/X11/Xwrapper.config
```

Set the file contents to:

```
allowed_users=anybody
needs_root_rights=no
```

> **Why `anybody`:** The kiosk service starts as user `pi` outside of a
> PAM login session. The default `allowed_users=console` only permits users
> with an active console login session, which systemd services do not have.
> `anybody` removes that restriction safely on a single-user embedded system.

### Step 9 — Generate an SSH key for GitHub authentication

The Pi clones the repo over SSH. Generate a dedicated key:

```bash
ssh-keygen -t ed25519 -C "pi@photobooth" -f ~/.ssh/id_ed25519
# Press Enter twice to use no passphrase
```

Display the public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

Add this key to the GitHub repository:
1. Go to the repository → **Settings** → **Deploy keys**
2. Click **Add deploy key**
3. Title: `pi@photobooth`, paste the public key
4. Leave "Allow write access" unchecked (read-only is sufficient)

Verify the key works:

```bash
ssh -T git@github.com
# Expected: Hi <user>/<repo>! You've successfully authenticated...
```

### Step 10 — Clone the repository

```bash
cd /home/pi
git clone git@github.com:<user>/photobooth_v2.git photobooth_v2
cd photobooth_v2
```

Confirm the checkout:

```bash
ls
# Should show: app.py  config.py  CLAUDE.md  SPEC.md  photobooth.service  ...
```

### Step 11 — Install Python dependencies

On Bookworm, `pip` operates in "externally managed" mode by default.
Use `--break-system-packages` to install into the system Python environment.
This is intentional and appropriate for a dedicated single-purpose device.

```bash
pip3 install --break-system-packages flask
```

Verify Flask is importable:

```bash
python3 -c "import flask; print(flask.__version__)"
```

> `picamera2` and `gpiozero` are installed separately via `apt` (see Phase 3
> and Phase 2 respectively) — never install them via pip, as the apt packages
> carry pre-built ARM binaries and system integration.

### Step 12 — Create required runtime directories

```bash
mkdir -p /home/pi/photobooth_v2/photos/default/{full,thumbs}
mkdir -p /home/pi/photobooth_v2/uploads
mkdir -p /home/pi/photobooth_v2/static/splash
```

### Step 13 — Deploy the systemd services

The photobooth runs as two services. Both unit files are checked into the
repo and copied to `/etc/systemd/system/`.

```bash
sudo cp /home/pi/photobooth_v2/photobooth.service /etc/systemd/system/
sudo cp /home/pi/photobooth_v2/photobooth-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable photobooth.service
sudo systemctl enable photobooth-kiosk.service
```

#### `photobooth.service`

Runs the Flask backend. Starts on boot after the network is up.
Restarts automatically on failure with a 5 s delay.

```
User=pi
WorkingDirectory=/home/pi/photobooth_v2
ExecStart=/usr/bin/python3 /home/pi/photobooth_v2/app.py
```

#### `photobooth-kiosk.service`

Starts after `photobooth.service`. Launches Chromium in kiosk mode via
`xinit` on display `:0`, VT7. Key Chromium flags:

- `--kiosk` — fullscreen, no chrome, no exit gesture
- `--noerrdialogs` — suppresses crash dialogs that would obscure the screen
- `--disable-infobars` — hides "Chrome is being controlled" banner
- `--no-first-run` — skips first-launch wizard
- `--disable-extensions` — no extension prompts
- `--disable-background-networking` — reduces idle network chatter
- `--check-for-update-interval=31536000` — disables effective auto-update

Points to `http://localhost:5000`.

### Step 14 — Start and verify

Start both services and confirm they are running:

```bash
sudo systemctl start photobooth.service
sudo systemctl status photobooth.service
# Expected: active (running)

curl http://localhost:5000/status
# Expected: {"event_name": "My Party", "state": 1}

sudo systemctl start photobooth-kiosk.service
sudo systemctl status photobooth-kiosk.service
# Expected: active (running)
```

Chromium should appear fullscreen on the attached display showing the kiosk
home screen.

Check logs if anything is wrong:

```bash
journalctl -u photobooth.service -n 50
journalctl -u photobooth-kiosk.service -n 50
```

### Step 15 — Reboot and confirm auto-start

```bash
sudo reboot
```

After reboot, wait ~15 seconds, then verify both services came up without
manual intervention:

```bash
ssh pi@photobooth.local
systemctl is-active photobooth.service      # active
systemctl is-active photobooth-kiosk.service # active
curl http://localhost:5000/status
```

Chromium should be showing the kiosk screen on the display without any
manual action.

---

## Deploying updates

All code changes are deployed via `git pull` over SSH. Never SCP or rsync
directly to the Pi.

```bash
ssh pi@photobooth.local
cd /home/pi/photobooth_v2
git pull
sudo systemctl restart photobooth.service
# Chromium reconnects automatically once Flask is back up
```

---

## Quick-reference troubleshooting

| Symptom                          | First check                                                         |
|----------------------------------|---------------------------------------------------------------------|
| Blank screen on boot             | `journalctl -u photobooth.service -n 50` — Flask startup error      |
| Chromium shows connection error  | `systemctl is-active photobooth.service` — Flask not running        |
| `xinit` fails in kiosk service   | Check `/etc/X11/Xwrapper.config` — `allowed_users=anybody` set?    |
| `rpicam-still` fails             | Ribbon cable seated? Camera enabled? (`raspi-config nonint do_camera 0`) |
| `git clone` permission denied    | SSH key added to GitHub deploy keys? (`ssh -T git@github.com`)      |
| `import flask` fails             | `pip3 install --break-system-packages flask`                        |
| Services don't start on boot     | `sudo systemctl enable photobooth.service photobooth-kiosk.service` |
