# Night volume

At night it **caps** Windows master volume (default 25% from 23:00 to 07:00). Daytime it does not touch volume.

## Setup

1. Python 3.
2. `START.bat` (installs `pycaw` the first time).
3. Tray → **Hours / cap (json)** if 23–07 / 25% is wrong for you.

```
start_hour: 23
end_hour: 7
max_percent: 25
```

Hours wrap midnight. `23` → `7` means late night through morning.

## Use

Leave **ON** overnight. If you *want* loud at 1am, set **OFF** or raise `max_percent`.

**Careful**

- It will pull the volume back down if you drag it above the cap during night hours. That’s the point.
- Headphones vs speakers: it uses the current default playback device.
- If the tray says `audio api fail`, the first `START.bat` probably didn’t finish installing. Run it again.
- **Start with Windows** is useful for this one if you actually sleep with the PC on.
