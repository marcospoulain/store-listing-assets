#!/usr/bin/env python3
"""Boot and drive Android emulators / devices for Google Play screenshots.

Usage:
  android_emu.py list
  android_emu.py boot <phone|tablet|foldable|wear|tv|automotive|automotive-portrait|xr> [--headless]
                                                   -> prints the adb serial on stdout
  android_emu.py demo-on <SERIAL>                   clean status bar (SystemUI demo mode)
  android_emu.py demo-off <SERIAL>
  android_emu.py deeplink <SERIAL> <url> [application.id]
  android_emu.py ui <SERIAL>                        visible elements with tap coordinates
  android_emu.py shot <SERIAL> <out.png> [--delay SECONDS]
  android_emu.py stop <SERIAL>                      shut the emulator down

Works on macOS, Linux and Windows. Only stdlib; progress goes to stderr.
"""
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

CLASSES = {
    # class: (system image tags in order of preference, device profile ids in order of preference)
    "phone": (["google_apis", "google_apis_playstore", "default"], ["pixel_9", "pixel_8", "pixel_7", "pixel_6", "pixel_5", "pixel"]),
    "tablet": (["google_apis", "google_apis_playstore", "default"], ["pixel_tablet", "pixel_c", "Nexus 10", "Nexus 9"]),
    "foldable": (["google_apis", "google_apis_playstore"], ["pixel_9_pro_fold", "pixel_fold"]),
    "wear": (["android-wear", "android-wear-signed"], ["wearos_large_round", "wearos_small_round", "wear_round"]),
    "tv": (["google-tv", "android-tv"], ["tv_1080p", "tv_4k"]),
    "automotive": (["android-automotive", "android-automotive-playstore"], ["automotive_1024p_landscape"]),
    "automotive-portrait": (["android-automotive", "android-automotive-playstore"], ["automotive_portrait"]),
    "xr": (["android-xr", "google-xr"], ["xr_headset_device", "xr_device"]),
}
EXE = ".exe" if os.name == "nt" else ""
BAT = ".bat" if os.name == "nt" else ""


def log(*a):
    print(*a, file=sys.stderr)


def die(msg, code=1):
    log("android_emu: " + msg)
    sys.exit(code)


def sdk_root():
    cands = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
             Path.home() / "Library/Android/sdk", Path.home() / "Android/Sdk",
             Path(os.environ.get("LOCALAPPDATA", "")) / "Android/Sdk" if os.environ.get("LOCALAPPDATA") else None]
    for c in cands:
        if c and Path(c).is_dir():
            return Path(c)
    return None


def tool(name):
    """Path to an SDK tool, or None."""
    found = shutil.which(name)
    if found:
        return found
    sdk = sdk_root()
    if not sdk:
        return None
    places = {
        "adb": [sdk / "platform-tools" / f"adb{EXE}"],
        "emulator": [sdk / "emulator" / f"emulator{EXE}"],
        "avdmanager": [sdk / "cmdline-tools" / "latest" / "bin" / f"avdmanager{BAT}"] + sorted(sdk.glob(f"cmdline-tools/*/bin/avdmanager{BAT}")),
        "sdkmanager": [sdk / "cmdline-tools" / "latest" / "bin" / f"sdkmanager{BAT}"] + sorted(sdk.glob(f"cmdline-tools/*/bin/sdkmanager{BAT}")),
    }
    for p in places.get(name, []):
        if p.exists():
            return str(p)
    return None


def adb(*args, serial=None, check=True, binary=False, timeout=120):
    exe = tool("adb")
    if not exe:
        die("adb not found. Install Android platform-tools (Android Studio > SDK Manager, or "
            "`brew install android-platform-tools`) and set ANDROID_HOME.", 3)
    cmd = [exe] + (["-s", serial] if serial else []) + list(args)
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if check and p.returncode != 0:
        die(f"adb {' '.join(args)} failed: {p.stderr.decode(errors='replace').strip()}")
    return p.stdout if binary else p.stdout.decode(errors="replace")


def avd_home():
    if os.environ.get("ANDROID_AVD_HOME"):
        return Path(os.environ["ANDROID_AVD_HOME"])
    return Path.home() / ".android" / "avd"


def read_ini(path):
    d = {}
    try:
        for line in Path(path).read_text(errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip()
    except OSError:
        pass
    return d


def classify(cfg):
    tag = (cfg.get("tag.id", "") + " " + cfg.get("tag.ids", "")).lower()
    name = cfg.get("hw.device.name", "").lower()
    try:
        w, h, dens = int(cfg.get("hw.lcd.width", 0)), int(cfg.get("hw.lcd.height", 0)), int(cfg.get("hw.lcd.density", 160))
    except ValueError:
        w = h = 0
        dens = 160
    if "wear" in tag:
        return "wear"
    if "tv" in tag:
        return "tv"
    if "automotive" in tag:
        return "automotive-portrait" if h > w else "automotive"
    if "xr" in tag:
        return "xr"
    if "fold" in name:
        return "foldable"
    if "tablet" in name or (w and min(w, h) * 160 / max(dens, 1) >= 600):
        return "tablet"
    return "phone"


def avds():
    """{avd name: class}"""
    out = {}
    home = avd_home()
    if home.is_dir():
        for ini in sorted(home.glob("*.ini")):
            path = read_ini(ini).get("path") or str(home / (ini.stem + ".avd"))
            out[ini.stem] = classify(read_ini(Path(path) / "config.ini"))
    return out


def running():
    """{serial: avd name or None for physical devices}"""
    out = {}
    for line in adb("devices").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serial = parts[0]
            name = None
            if serial.startswith("emulator-"):
                r = adb("emu", "avd", "name", serial=serial, check=False).splitlines()
                name = r[0].strip() if r else None
            out[serial] = name
    return out


def host_abi():
    return "arm64-v8a" if platform.machine().lower() in ("arm64", "aarch64") else "x86_64"


def best_image(cls):
    sdk = sdk_root()
    tags, _ = CLASSES[cls]
    best = None
    if sdk and (sdk / "system-images").is_dir():
        for api_dir in (sdk / "system-images").iterdir():
            m = re.match(r"android-(\d+)", api_dir.name)
            api = int(m.group(1)) if m else 0
            for tag_dir in api_dir.iterdir() if api_dir.is_dir() else []:
                if tag_dir.name not in tags:
                    continue
                for abi_dir in tag_dir.iterdir():
                    if not abi_dir.is_dir():
                        continue
                    score = (abi_dir.name == host_abi(), api, -tags.index(tag_dir.name))
                    if not best or score > best[0]:
                        best = (score, f"system-images;{api_dir.name};{tag_dir.name};{abi_dir.name}")
    return best[1] if best else None


def create_avd(cls):
    tags, profiles = CLASSES[cls]
    image = best_image(cls)
    avdmanager = tool("avdmanager")
    sdkmanager = tool("sdkmanager") or "sdkmanager"
    if not image:
        die(f"no system image for class '{cls}' is installed. Find one and install it (1-2 GB, ask the user first):\n"
            f"  {sdkmanager} --list | grep \"system-images;.*;{tags[0]};{host_abi()}\"\n"
            f"  {sdkmanager} \"system-images;android-<API>;{tags[0]};{host_abi()}\" emulator platform-tools\n"
            f"Android Studio > Device Manager > Create Device does the same with a UI.", 3)
    if not avdmanager:
        die("avdmanager not found. Install 'Android SDK Command-line Tools' (Android Studio > SDK Manager > SDK Tools), "
            "or create the device in Android Studio > Device Manager.", 3)
    known = subprocess.run([avdmanager, "list", "device", "-c"], capture_output=True, text=True).stdout.split("\n")
    known = [k.strip() for k in known if k.strip()]
    profile = next((p for p in profiles if p in known), None)
    if not profile and cls == "xr":
        profile = next((k for k in known if "xr" in k.lower()), None)
    if not profile:
        die(f"no device profile for '{cls}' (looked for {', '.join(profiles)}). Create the AVD in Android Studio > Device Manager.", 3)
    name = f"store_assets_{cls.replace('-', '_')}"
    log(f"creating AVD {name}: {profile} on {image}")
    p = subprocess.run([avdmanager, "create", "avd", "-n", name, "-k", image, "-d", profile, "--force"],
                       input="no\n", capture_output=True, text=True)
    if p.returncode != 0:
        die(f"avdmanager failed: {(p.stderr or p.stdout).strip()}")
    return name


def cmd_boot(cls, headless):
    if cls not in CLASSES:
        die(f"unknown class '{cls}'. Options: {', '.join(CLASSES)}", 2)
    all_avds = avds()
    live = running()
    for serial, name in live.items():
        if name and all_avds.get(name) == cls:
            log(f"already running: {name}")
            print(serial)
            return
    name = next((n for n, c in all_avds.items() if c == cls), None) or create_avd(cls)
    emulator = tool("emulator")
    if not emulator:
        die("the Android Emulator is not installed. Install it (ask the user first) with:\n"
            f"  {tool('sdkmanager') or 'sdkmanager'} emulator\n"
            "or Android Studio > SDK Manager > SDK Tools > Android Emulator. "
            "A device connected over USB with debugging enabled also works: pass its serial from `adb devices`.", 3)
    used = {int(s.split("-")[1]) for s in live if s.startswith("emulator-")}
    port = next(p for p in range(5554, 5600, 2) if p not in used)
    logfile = Path(tempfile.gettempdir()) / f"store-assets-emulator-{port}.log"
    args = [emulator, "-avd", name, "-port", str(port), "-no-snapshot-save", "-no-boot-anim"]
    if headless:
        args += ["-no-window"]
    log(f"starting {name} on port {port} (log: {logfile}) ...")
    kwargs = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen(args, stdout=open(logfile, "w"), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kwargs)
    serial = f"emulator-{port}"
    deadline = time.time() + 420
    while time.time() < deadline:
        time.sleep(3)
        try:
            if adb("shell", "getprop", "sys.boot_completed", serial=serial, check=False, timeout=15).strip() == "1":
                time.sleep(3)
                log(f"ready: {name}")
                print(serial)
                return
        except subprocess.TimeoutExpired:
            pass
    die(f"{name} did not finish booting in 7 minutes. See {logfile}.")


def cmd_list():
    sdk = sdk_root()
    print(f"SDK: {sdk or 'not found (set ANDROID_HOME)'}")
    for t in ("adb", "emulator", "avdmanager", "sdkmanager"):
        print(f"  {t}: {tool(t) or 'missing'}")
    all_avds = avds()
    print("AVDs:")
    for n, c in all_avds.items():
        print(f"  {c:20} {n}")
    if not all_avds:
        print("  (none; `boot <class>` creates one if a system image is installed)")
    if tool("adb"):
        print("Connected:")
        for s, n in running().items():
            print(f"  {s}  {('emulator ' + n + ' [' + all_avds.get(n, '?') + ']') if n else 'physical device'}")


def demo(serial, on):
    b = lambda *x: adb("shell", "am", "broadcast", "-a", "com.android.systemui.demo", *x, serial=serial, check=False)
    if not on:
        b("-e", "command", "exit")
        return
    adb("shell", "settings", "put", "global", "sysui_demo_allowed", "1", serial=serial, check=False)
    b("-e", "command", "enter")
    b("-e", "command", "clock", "-e", "hhmm", "1200")
    b("-e", "command", "battery", "-e", "level", "100", "-e", "plugged", "false")
    b("-e", "command", "network", "-e", "wifi", "show", "-e", "level", "4")
    b("-e", "command", "network", "-e", "mobile", "show", "-e", "level", "4", "-e", "datatype", "none")
    b("-e", "command", "notifications", "-e", "visible", "false")
    log("demo mode on: 12:00, full Wi-Fi and signal, full battery, no notifications")


def cmd_ui(serial):
    raw = adb("exec-out", "uiautomator", "dump", "/dev/tty", serial=serial, check=False)
    start, end = raw.find("<?xml"), raw.rfind("</hierarchy>")
    if start < 0 or end < 0:
        die("could not dump the UI hierarchy (the screen may be animating or secure). Try again.")
    root = ET.fromstring(raw[start:end + len("</hierarchy>")])
    for n in root.iter("node"):
        label = n.get("text") or n.get("content-desc") or ""
        rid = n.get("resource-id", "")
        if not (label or rid) or not (n.get("clickable") == "true" or label):
            continue
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
        if not m:
            continue
        x1, y1, x2, y2 = map(int, m.groups())
        flags = "tap " if n.get("clickable") == "true" else "    "
        print(f"{flags}{(x1 + x2) // 2:5},{(y1 + y2) // 2:<5} {label!r:40} {rid.split('/')[-1]}  <{n.get('class', '').split('.')[-1]}>")


def cmd_shot(serial, out, delay):
    time.sleep(delay)
    data = adb("exec-out", "screencap", "-p", serial=serial, binary=True)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        die("screencap did not return a PNG (secure window or device locked?).")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    w, h = struct.unpack(">II", data[16:24])
    print(f"{out} {w}x{h}")


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    headless = "--headless" in a
    a = [x for x in a if x != "--headless"]
    delay = 1.0
    if "--delay" in a:
        i = a.index("--delay")
        delay = float(a[i + 1])
        a = a[:i] + a[i + 2:]
    cmd, rest = a[0], a[1:]
    try:
        if cmd == "list":
            cmd_list()
        elif cmd == "boot":
            cmd_boot(rest[0], headless)
        elif cmd == "demo-on":
            demo(rest[0], True)
        elif cmd == "demo-off":
            demo(rest[0], False)
        elif cmd == "deeplink":
            print(adb("shell", "am", "start", "-W", "-a", "android.intent.action.VIEW", "-d", rest[1], *rest[2:3], serial=rest[0]).strip())
        elif cmd == "ui":
            cmd_ui(rest[0])
        elif cmd == "shot":
            cmd_shot(rest[0], rest[1], delay)
        elif cmd == "stop":
            adb("emu", "kill", serial=rest[0], check=False)
        else:
            die(f"unknown command '{cmd}'. Run with --help.", 2)
    except IndexError:
        die("missing argument. Run with --help.", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
