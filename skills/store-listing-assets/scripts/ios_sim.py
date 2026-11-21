#!/usr/bin/env python3
"""Boot and drive Apple simulators for App Store screenshots (macOS + Xcode).

Usage:
  ios_sim.py list
  ios_sim.py boot <iphone|ipad|watch|tv|vision>     -> prints the UDID on stdout
  ios_sim.py statusbar <UDID>                        9:41, full bars, full battery
  ios_sim.py statusbar-clear <UDID>
  ios_sim.py appearance <UDID> <light|dark>
  ios_sim.py openurl <UDID> <url>
  ios_sim.py shot <UDID> <out.png> [--delay SECONDS]
  ios_sim.py shutdown <UDID>

`boot` chooses a simulator whose native resolution is an accepted App Store
screenshot size, creating one if the runtime is installed but the device is not.
Only stdlib; progress goes to stderr so stdout stays machine-readable.
"""
import json
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

# class -> (runtime platform, [name patterns in order of preference])
CLASSES = {
    "iphone": ("iOS", [r"^iPhone (\d+) Pro Max$", r"^iPhone (\d+) Plus$", r"^iPhone (\d+) Pro$", r"^iPhone (\d+)$"]),
    "ipad": ("iOS", [r"^iPad Pro 13-inch \(M(\d+)\)", r"^iPad Pro \(12\.9-inch\) \((\d+)", r"^iPad Air 13-inch \(M(\d+)\)"]),
    "watch": ("watchOS", [r"^Apple Watch Ultra (\d+)", r"^Apple Watch Ultra", r"^Apple Watch Series (\d+) \(4[5-9]mm\)"]),
    "tv": ("tvOS", [r"^Apple TV 4K \((\d+)\w* generation\)$", r"^Apple TV 4K", r"^Apple TV"]),
    "vision": ("visionOS", [r"^Apple Vision Pro"]),
}
PLATFORM_ALIASES = {"visionOS": ("visionOS", "xrOS")}


def log(*a):
    print(*a, file=sys.stderr)


def die(msg, code=1):
    log("ios_sim: " + msg)
    sys.exit(code)


def simctl(*args, check=True, capture=True):
    if not shutil.which("xcrun"):
        die("xcrun not found. iOS simulators need macOS with Xcode installed "
            "(App Store, then `sudo xcode-select -s /Applications/Xcode.app`). "
            "On other systems use capture_web.mjs or ask the user for captures.", 3)
    p = subprocess.run(["xcrun", "simctl", *args], capture_output=capture, text=True)
    if check and p.returncode != 0:
        die(f"simctl {' '.join(args)} failed: {(p.stderr or p.stdout or '').strip()}")
    return p


def runtime_version(key):
    # com.apple.CoreSimulator.SimRuntime.iOS-18-2 -> ("iOS", (18, 2))
    m = re.search(r"SimRuntime\.([A-Za-z]+)-([\d-]+)$", key)
    if not m:
        return ("", (0,))
    return (m.group(1), tuple(int(x) for x in m.group(2).split("-") if x))


def platform_matches(platform, wanted):
    return platform in PLATFORM_ALIASES.get(wanted, (wanted,))


def rank(name, patterns):
    """Lower is better. Returns None when the name matches no pattern."""
    for i, pat in enumerate(patterns):
        m = re.search(pat, name)
        if m:
            gen = int(m.group(1)) if m.groups() and m.group(1) else 0
            return (i, -gen)
    return None


def candidates(cls):
    platform, patterns = CLASSES[cls]
    data = json.loads(simctl("list", "-j", "devices", "available").stdout)["devices"]
    out = []
    for key, devs in data.items():
        plat, ver = runtime_version(key)
        if not platform_matches(plat, platform):
            continue
        for d in devs:
            r = rank(d["name"], patterns)
            if r is not None:
                out.append((r, tuple(-v for v in ver), 0 if d["state"] == "Booted" else 1, d, f"{plat} {'.'.join(map(str, ver))}"))
    out.sort(key=lambda t: t[:3])
    return out


def create(cls):
    platform, patterns = CLASSES[cls]
    types = json.loads(simctl("list", "-j", "devicetypes").stdout)["devicetypes"]
    runtimes = [r for r in json.loads(simctl("list", "-j", "runtimes").stdout)["runtimes"]
                if r.get("isAvailable") and platform_matches(runtime_version(r["identifier"])[0], platform)]
    if not runtimes:
        die(f"no {platform} simulator runtime is installed. Install it (several GB, ask the user first) with:\n"
            f"  xcodebuild -downloadPlatform {platform}", 3)
    runtimes.sort(key=lambda r: runtime_version(r["identifier"])[1], reverse=True)
    ranked = sorted((rank(t["name"], patterns), t) for t in types if rank(t["name"], patterns) is not None)
    for rt in runtimes:
        for _, t in ranked:
            name = f"{t['name']} (store-assets)"
            p = simctl("create", name, t["identifier"], rt["identifier"], check=False)
            if p.returncode == 0:
                log(f"created simulator '{name}' on {rt['name']}")
                return {"name": name, "udid": p.stdout.strip(), "state": "Shutdown"}
    die(f"could not create a {cls} simulator from the installed device types and runtimes.", 3)


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else (0, 0)


def cmd_list():
    for cls in CLASSES:
        c = candidates(cls)
        print(f"{cls}:")
        if not c:
            print("  (none installed; `boot` will try to create one)")
        for i, (_, _, _, d, rt) in enumerate(c[:6]):
            print(f"  {'*' if i == 0 else ' '} {d['name']}  [{rt}]  {d['state']}  {d['udid']}")
    print("\n* = what `boot <class>` would use")


def cmd_boot(cls):
    if cls not in CLASSES:
        die(f"unknown class '{cls}'. Options: {', '.join(CLASSES)}", 2)
    c = candidates(cls)
    dev = c[0][3] if c else create(cls)
    if dev["state"] != "Booted":
        log(f"booting {dev['name']} ({dev['udid']}) ...")
        p = simctl("boot", dev["udid"], check=False)
        if p.returncode != 0 and "current state: Booted" not in (p.stderr or ""):
            die(f"boot failed: {p.stderr.strip()}")
    simctl("bootstatus", dev["udid"], "-b")
    log(f"ready: {dev['name']}")
    print(dev["udid"])


def cmd_statusbar(udid):
    p = simctl("status_bar", udid, "override", "--time", "9:41", "--dataNetwork", "wifi",
               "--wifiMode", "active", "--wifiBars", "3", "--cellularMode", "active",
               "--cellularBars", "4", "--batteryState", "charged", "--batteryLevel", "100", check=False)
    if p.returncode != 0:
        log(f"status bar override not applied ({p.stderr.strip()}); fine on watch / TV / Vision.")
    else:
        log("status bar: 9:41, full signal, 100 % battery")


def cmd_shot(udid, out, delay):
    time.sleep(delay)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    simctl("io", udid, "screenshot", "--type=png", str(out))
    w, h = png_size(out)
    print(f"{out} {w}x{h}")


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, rest = a[0], a[1:]
    delay = 1.0
    if "--delay" in rest:
        i = rest.index("--delay")
        delay = float(rest[i + 1])
        rest = rest[:i] + rest[i + 2:]
    try:
        if cmd == "list":
            cmd_list()
        elif cmd == "boot":
            cmd_boot(rest[0])
        elif cmd == "statusbar":
            cmd_statusbar(rest[0])
        elif cmd == "statusbar-clear":
            simctl("status_bar", rest[0], "clear", check=False)
        elif cmd == "appearance":
            simctl("ui", rest[0], "appearance", rest[1])
        elif cmd == "openurl":
            # The first openurl right after boot often times out while the system finishes loading.
            for attempt in range(3):
                p = simctl("openurl", rest[0], rest[1], check=attempt == 2)
                if p.returncode == 0:
                    break
                time.sleep(5)
        elif cmd == "shot":
            cmd_shot(rest[0], rest[1], delay)
        elif cmd == "shutdown":
            simctl("shutdown", rest[0], check=False)
        else:
            die(f"unknown command '{cmd}'. Run with --help.", 2)
    except IndexError:
        die("missing argument. Run with --help.", 2)


if __name__ == "__main__":
    main(sys.argv[1:])
