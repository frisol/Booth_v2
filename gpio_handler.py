# gpio_handler.py — Button (GPIO 24, physical pin 18) and SSR/light (GPIO 17, physical pin 11) control.
# Safe to import on non-Pi hardware; all hardware calls are no-ops when
# gpiozero is unavailable.

from config import BUTTON_PIN, LIGHT_PIN, DEBOUNCE_S

try:
    from gpiozero import Button, OutputDevice
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False

_button = None
_light  = None


def setup(on_press_callback):
    """
    Initialise GPIO devices and register the button callback.
    on_press_callback is invoked from gpiozero's internal thread each time
    the button is pressed. No-op if gpiozero is unavailable.
    """
    global _button, _light
    if not _GPIO_AVAILABLE:
        return
    _light  = OutputDevice(LIGHT_PIN, initial_value=False)
    _button = Button(BUTTON_PIN, pull_up=True, bounce_time=DEBOUNCE_S)
    _button.when_pressed = on_press_callback


def set_light(on: bool):
    """Turn the SSR/light on (True) or off (False). No-op if GPIO unavailable."""
    if _light is None:
        return
    if on:
        _light.on()
    else:
        _light.off()


def cleanup():
    """
    Release GPIO resources. Ensures light is off before closing.
    Call this on application shutdown (e.g. via atexit).
    """
    global _button, _light
    if _button is not None:
        _button.close()
        _button = None
    if _light is not None:
        _light.off()
        _light.close()
        _light = None
