
---

# App Usage Timer (Android / Termux)

A simple Python script that monitors foreground Android apps and limits their usage time.
When an app exceeds the allowed time, it is automatically killed and temporarily banned.

> **Root access required**

---

## Features

* Detects the currently foreground app
* Tracks active usage time per app
* Automatically kills apps after time limit
* Temporary ban system (cooldown)
* Live monitoring using `dumpsys`
* Works in **Termux** with root access

---

## Requirements

* Android device (rooted)
* Termux installed
* Python 3
* `su` (root access)
* `termux-api` (for notifications)

Install Termux API:

```bash
pkg install termux-api
```

---

## block.txt Format

Add **one package name per line**:

```
com.facebook.katana
com.instagram.android
com.google.android.youtube
```

---

## How It Works

1. The script constantly checks which app is in the foreground.
2. If the app is listed in `block.txt`, it starts tracking time.
3. When the time limit is reached:

   * The app is killed
   * A toast notification appears
   * The app is banned for a short period
4. After the ban expires, the app can be used again.

---

## Current Limits (Hardcoded)

| Feature       | Value      |
| ------------- | ---------- |
| Allowed usage | 30 minutes |
| Ban duration  | 10 minutes |
| Idle reset    | 5 minutes  |

You can change these inside `main.py`:

```python
banned_stop_time = '00:10:00'
idle_treshold = '00:05:00'
```

---

## Run the Script

```bash
su
python main.py
```

Stop with:

```
CTRL + C
```

---

## Notes

* Uses `dumpsys activity` requires root.
* Killing apps uses `pkill`.
* Designed for **personal usage control**, not system enforcement.
* May behave differently depending on Android version.

---

## TODO / Improvements

* User-configurable time limits (via dialog)

---