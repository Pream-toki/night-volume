"""After a set hour, cap system volume so a video cannot blast at 2am."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
STARTUP_NAME = "NightVolume.vbs"

stop_event = threading.Event()
state = {"last": "starting", "level": "-"}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            json.dumps(
                {"enabled": True, "start_hour": 23, "end_hour": 7, "max_percent": 25},
                indent=2,
            ),
            encoding="utf-8",
        )
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"enabled": True, "start_hour": 23, "end_hour": 7, "max_percent": 25}


def save_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def startup_path() -> Path:
    return (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs/Startup"
        / STARTUP_NAME
    )


def set_startup(icon, want: bool) -> None:
    p = startup_path()
    script = Path(__file__).resolve()
    try:
        if want:
            p.write_text(
                'Set sh = CreateObject("WScript.Shell")\n'
                f'sh.CurrentDirectory = "{script.parent}"\n'
                f'sh.Run "pythonw ""{script}""", 0, False\n',
                encoding="ascii",
            )
        elif p.exists():
            p.unlink()
        cfg = load_config()
        cfg["start_with_windows"] = want
        save_config(cfg)
        icon.update_menu()
    except OSError:
        pass


def in_night(start_h: int, end_h: int, hour: int) -> bool:
    if start_h == end_h:
        return False
    if start_h < end_h:
        return start_h <= hour < end_h
    return hour >= start_h or hour < end_h


def volume_endpoint():
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import POINTER, cast

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def get_set_volume(max_frac: float | None = None) -> float:
    vol = volume_endpoint()
    cur = float(vol.GetMasterVolumeLevelScalar())
    if max_frac is not None and cur > max_frac:
        vol.SetMasterVolumeLevelScalar(max_frac, None)
        cur = max_frac
    return cur


def worker() -> None:
    while not stop_event.is_set():
        cfg = load_config()
        if not cfg.get("enabled", True):
            state["last"] = "paused"
            stop_event.wait(20)
            continue
        try:
            hour = datetime.now().hour
            night = in_night(int(cfg.get("start_hour", 23)), int(cfg.get("end_hour", 7)), hour)
            cap = max(0.05, min(1.0, int(cfg.get("max_percent", 25)) / 100.0))
            if night:
                cur = get_set_volume(cap)
                state["last"] = "capping"
            else:
                cur = get_set_volume(None)
                state["last"] = "day, hands off"
            state["level"] = f"{int(cur * 100)}%"
        except Exception as e:
            state["last"] = "audio api fail"
            state["level"] = str(e)[:40]
        stop_event.wait(15)


def toggle(icon, on: bool) -> None:
    cfg = load_config()
    cfg["enabled"] = on
    save_config(cfg)
    try:
        icon.update_menu()
    except Exception:
        pass


def open_cfg(_i=None, _item=None) -> None:
    load_config()
    try:
        os.startfile(str(CONFIG_PATH))
    except OSError:
        pass


def quit_app(icon, _item=None) -> None:
    stop_event.set()
    icon.stop()


def menu(icon):
    cfg = load_config()
    en = bool(cfg.get("enabled", True))
    return pystray.Menu(
        pystray.MenuItem(f"{state['last']}  {state['level']}", None, enabled=False),
        pystray.MenuItem("ON", lambda i, _: toggle(i, True), checked=lambda _: en, radio=True),
        pystray.MenuItem("OFF", lambda i, _: toggle(i, False), checked=lambda _: not en, radio=True),
        pystray.MenuItem(
            "Start with Windows",
            lambda i, _: set_startup(i, not startup_path().exists()),
            checked=lambda _: startup_path().exists(),
        ),
        pystray.MenuItem("Hours / cap (json)", open_cfg),
        pystray.MenuItem("Quit", quit_app),
    )


def icon_img():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=(50, 50, 90, 255))
    d.polygon([(18, 28), (28, 28), (40, 18), (40, 46), (28, 36), (18, 36)], fill="white")
    return img


def main() -> None:
    load_config()
    threading.Thread(target=worker, daemon=True).start()
    icon = pystray.Icon("NightVolume", icon_img(), "Night volume", menu=pystray.Menu(lambda: menu(icon)))
    icon.run()


if __name__ == "__main__":
    main()
