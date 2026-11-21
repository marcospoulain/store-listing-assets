#!/usr/bin/env python3
"""First-pass detection of an app project for store listing assets.

Usage:  detect_project.py [repo_root]        -> JSON on stdout

Reports frameworks, target stores, supported device types per store, bundle /
application ids, URL schemes, existing screenshot automation, and the tools
available on this machine. Heuristic: every finding cites the file it came
from under "evidence" so it can be checked. Only stdlib.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP = {"node_modules", ".git", "Pods", "build", "dist", ".gradle", ".dart_tool", ".next", ".expo", "DerivedData",
        "vendor", ".venv", "venv", "__pycache__", ".idea", "store-assets", "appstore-assets", "playstore-assets",
        ".build", "Carthage", ".turbo", "coverage", "out", "target"}
MAX_DEPTH = 6
WEB_DEPS = ["next", "vite", "react-scripts", "nuxt", "@sveltejs/kit", "@angular/core", "astro", "@remix-run/react", "gatsby"]


def walk(root):
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts)
        dirnames[:] = [d for d in dirnames if d not in SKIP and not (d.startswith(".") and d not in (".maestro",))]
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        yield rel, dirnames, filenames


def read(p, limit=400_000):
    try:
        return Path(p).read_text(errors="replace")[:limit]
    except OSError:
        return ""


def uniq(xs):
    return sorted({x for x in xs if x})


def main(root):
    root = Path(root).resolve()
    ev = []  # evidence lines
    fw, apple_dev, google_dev = set(), set(), set()
    bundle_ids, app_ids, schemes, automation = [], [], [], []
    xcode_projects, schemes_hint, gradle_modules = [], [], []
    has = {"ios_dir": False, "android_dir": False}
    web_evidence = None

    for rel, dirs, files in walk(root):
        relp = rel.as_posix()
        for d in list(dirs):
            if d.endswith(".xcodeproj") or d.endswith(".xcworkspace"):
                xcode_projects.append((rel / d).as_posix())
            if d == ".maestro":
                automation.append(f"Maestro flows: {(rel / d).as_posix()}/")
            if d == "integration_test":
                automation.append(f"Flutter integration_test: {(rel / d).as_posix()}/")
            if d.endswith("UITests"):
                automation.append(f"XCUITest target: {(rel / d).as_posix()}/")
            if d == "androidTest":
                automation.append(f"Android instrumented tests: {(rel / d).as_posix()}/")
            if re.match(r"(layout|values)-(sw600dp|sw720dp|w840dp|large|xlarge)", d):
                google_dev.add("tablet")
                ev.append(f"{(rel / d).as_posix()}/ -> tablet layouts")
        for f in files:
            p = root / rel / f
            rp = (rel / f).as_posix()
            if f == "project.pbxproj":
                t = read(p, 3_000_000)
                has["ios_dir"] = True
                fams = set(re.findall(r'TARGETED_DEVICE_FAMILY = "?([\d,]+)"?;', t))
                nums = {n for fam in fams for n in fam.split(",")}
                for n, dev in (("1", "iphone"), ("2", "ipad"), ("3", "tv"), ("4", "watch"), ("7", "vision")):
                    if n in nums:
                        apple_dev.add(dev)
                sdks = set(re.findall(r"SDKROOT = (\w+);", t))
                for sdk, dev in (("macosx", "mac"), ("appletvos", "tv"), ("watchos", "watch"), ("xros", "vision")):
                    if sdk in sdks:
                        apple_dev.add(dev)
                if "SUPPORTS_MACCATALYST = YES" in t:
                    apple_dev.add("mac")
                ids = [i for i in re.findall(r'PRODUCT_BUNDLE_IDENTIFIER = "?([^";]+)"?;', t) if "Tests" not in i]
                bundle_ids += ids
                ev.append(f"{rp} -> device families {sorted(nums)}, SDKs {sorted(sdks)}, bundle ids {uniq(ids)[:4]}")
            elif f == "Info.plist" and "Tests" not in relp:
                t = read(p)
                m = re.search(r"CFBundleURLSchemes</key>\s*<array>(.*?)</array>", t, re.S)
                if m:
                    found = re.findall(r"<string>([^<$]+)</string>", m.group(1))
                    schemes += found
                    if found:
                        ev.append(f"{rp} -> URL schemes {found}")
            elif f == "AndroidManifest.xml" and "/build/" not in rp:
                t = read(p)
                has["android_dir"] = True
                google_dev.add("phone")
                checks = [("android.hardware.type.watch", "wear"), ("android.software.leanback", "tv"),
                          ("LEANBACK_LAUNCHER", "tv"), ("android.hardware.type.automotive", "automotive"),
                          ("androidx.car.app", "automotive"), ("android.software.xr", "xr"), ("android.hardware.xr", "xr")]
                for needle, dev in checks:
                    if needle in t:
                        google_dev.add(dev)
                        ev.append(f"{rp} -> {needle} ({dev})")
                found = [s for s in re.findall(r'android:scheme="([^"]+)"', t) if s not in ("http", "https", "content", "file")]
                schemes += found
                if found:
                    ev.append(f"{rp} -> URL schemes {uniq(found)}")
                if 'android:screenOrientation="portrait"' in t:
                    ev.append(f"{rp} -> an Activity is locked to portrait (check before assuming tablet / landscape support)")
            elif f in ("build.gradle", "build.gradle.kts"):
                t = read(p)
                ids = re.findall(r'applicationId\s*=?\s*["\']([^"\']+)["\']', t)
                if ids:
                    app_ids += ids
                    gradle_modules.append(relp or ".")
                    ev.append(f"{rp} -> applicationId {ids}")
                if "kotlin.multiplatform" in t or 'kotlin("multiplatform")' in t:
                    fw.add("kotlin-multiplatform")
                for needle, dev in (("androidx.wear", "wear"), ("androidx.car.app", "automotive"), ("androidx.xr", "xr"),
                                    ("androidx.tv", "tv"), ("androidx.leanback", "tv")):
                    if needle in t:
                        google_dev.add(dev)
                        ev.append(f"{rp} -> dependency {needle} ({dev})")
                if "material3.adaptive" in t or "material3-window-size-class" in t or "androidx.window" in t:
                    google_dev.add("tablet")
                    ev.append(f"{rp} -> adaptive layout libraries (tablet / foldable)")
            elif f == "pubspec.yaml":
                t = read(p)
                if re.search(r"^\s*flutter:\s*$", t, re.M) or "sdk: flutter" in t:
                    fw.add("flutter")
                    base = root / rel
                    plats = [d for d in ("ios", "android", "macos", "web", "windows", "linux") if (base / d).is_dir()]
                    ev.append(f"{rp} -> Flutter app, platforms {plats}")
                    if "macos" in plats:
                        apple_dev.add("mac")
            elif f == "package.json" and len(rel.parts) <= 3:
                try:
                    pkg = json.loads(read(p))
                except ValueError:
                    continue
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "expo" in deps:
                    fw.add("expo")
                if "react-native" in deps:
                    fw.add("react-native")
                if "@capacitor/core" in deps:
                    fw.add("capacitor")
                if "detox" in deps:
                    automation.append(f"Detox: {rp}")
                if "@playwright/test" in deps or "playwright" in deps:
                    automation.append(f"Playwright: {rp}")
                web = [d for d in WEB_DEPS if d in deps]
                if web and web_evidence is None:
                    web_evidence = f"{rp} -> web framework {web}; scripts {sorted(pkg.get('scripts', {}))[:8]}"
                if deps and ("expo" in deps or "react-native" in deps):
                    ev.append(f"{rp} -> {'expo' if 'expo' in deps else 'react-native'}; scripts {sorted(pkg.get('scripts', {}))[:8]}")
            elif f == "app.json" or re.match(r"app\.config\.(js|ts|mjs|cjs)$", f):
                t = read(p)
                if '"expo"' in t or "expo" in f or "ExpoConfig" in t:
                    ios_id = re.search(r'bundleIdentifier["\']?\s*:\s*["\']([^"\']+)', t)
                    and_id = re.search(r'package["\']?\s*:\s*["\']([\w.]+)["\']', t)
                    sch = re.search(r'["\']?scheme["\']?\s*:\s*["\']([^"\']+)', t)
                    if ios_id:
                        bundle_ids.append(ios_id.group(1))
                        apple_dev.add("iphone")
                    if and_id:
                        app_ids.append(and_id.group(1))
                        google_dev.add("phone")
                    if sch:
                        schemes.append(sch.group(1))
                    tablet = re.search(r"supportsTablet[\"']?\s*:\s*true", t)
                    if tablet:
                        apple_dev.add("ipad")
                    ev.append(f"{rp} -> ios {ios_id.group(1) if ios_id else '-'}, android {and_id.group(1) if and_id else '-'}, "
                              f"scheme {sch.group(1) if sch else '-'}, supportsTablet {bool(tablet)}")
            elif f in ("Snapfile", "Screengrabfile", "Fastfile", "Deliverfile"):
                automation.append(f"fastlane {f}: {rp}")
            elif re.match(r"capacitor\.config\.(ts|js|json)$", f):
                fw.add("capacitor")
                m = re.search(r'appId["\']?\s*:\s*["\']([^"\']+)', read(p))
                if m:
                    bundle_ids.append(m.group(1))
                    app_ids.append(m.group(1))
            elif f in ("manifest.json", "manifest.webmanifest", "site.webmanifest") and "extension" not in relp:
                t = read(p)
                if '"start_url"' in t or '"display"' in t:
                    ev.append(f"{rp} -> web app manifest (PWA)")
                    fw.add("pwa")
            elif f.endswith((".yaml", ".yml")) and ".maestro" in relp:
                pass
            elif f.endswith(".xcscheme"):
                schemes_hint.append(f[:-9])

    if has["ios_dir"] and not (fw & {"flutter", "expo", "react-native", "capacitor", "kotlin-multiplatform"}):
        fw.add("ios-native")
    if has["android_dir"] and not (fw & {"flutter", "expo", "react-native", "capacitor", "kotlin-multiplatform"}):
        fw.add("android-native")
    if web_evidence:
        fw.add("web")
        ev.append(web_evidence)
    if fw & {"flutter", "expo", "react-native"}:
        # cross-platform: assume both phones unless a platform folder says otherwise
        if not has["android_dir"] and not has["ios_dir"]:
            apple_dev.add("iphone")
            google_dev.add("phone")
    if has["ios_dir"] and not apple_dev:
        apple_dev.add("iphone")

    stores = []
    if apple_dev:
        stores.append("apple")
    if google_dev:
        stores.append("google-play")

    def ok(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, timeout=20).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    sdk = next((Path(c) for c in [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
                                  Path.home() / "Library/Android/sdk", Path.home() / "Android/Sdk"]
                if c and Path(c).is_dir()), None)
    emulator = shutil.which("emulator") or (sdk and (sdk / "emulator").is_dir() and str(sdk / "emulator"))
    try:
        import PIL  # noqa: F401
        pillow = True
    except ImportError:
        pillow = False
    host = {
        "os": sys.platform,
        "xcode_simctl": bool(shutil.which("xcrun")) and ok(["xcrun", "simctl", "help"]),
        "adb": bool(shutil.which("adb") or (sdk and (sdk / "platform-tools").is_dir())),
        "android_emulator": bool(emulator),
        "android_sdk": str(sdk) if sdk else None,
        "maestro": bool(shutil.which("maestro")),
        "fastlane": bool(shutil.which("fastlane")),
        "flutter": bool(shutil.which("flutter")),
        "node": bool(shutil.which("node")),
        "playwright": (root / "node_modules" / "playwright").is_dir() or (root / "node_modules" / "@playwright" / "test").is_dir(),
        "pillow": pillow,
    }

    routes = {}
    if apple_dev:
        routes["apple"] = ("simulator (ios_sim.py)" if host["xcode_simctl"] else
                           "web capture (capture_web.mjs)" if fw & {"web", "pwa", "expo", "flutter"} else
                           "no simulator on this machine: ask the user for captures")
    if google_dev:
        routes["google-play"] = ("emulator (android_emu.py)" if host["adb"] and host["android_emulator"] else
                                 "connected device over adb, or install the emulator" if host["adb"] else
                                 "web capture (capture_web.mjs)" if fw & {"web", "pwa", "expo", "flutter"} else
                                 "no Android SDK on this machine: install it or ask the user for captures")
    if not stores and fw & {"web", "pwa"}:
        routes["web"] = "web capture (capture_web.mjs); ask the user which store(s) the web app ships to"

    notes = []
    if "phone" in google_dev and "tablet" not in google_dev:
        notes.append("No explicit tablet layout signal found for Android; Play still recommends tablet screenshots if the UI adapts. Check on a tablet emulator before promising them.")
    if not stores:
        notes.append("No iOS or Android project found. If this is a web app, ask which store listing the assets are for.")

    print(json.dumps({
        "root": str(root),
        "frameworks": sorted(fw),
        "stores": stores,
        "apple": {"devices": sorted(apple_dev), "bundleIds": uniq(bundle_ids)[:8], "xcode": uniq(xcode_projects)[:8], "schemes": uniq(schemes_hint)[:8]},
        "googlePlay": {"devices": sorted(google_dev), "applicationIds": uniq(app_ids)[:8], "gradleModules": uniq(gradle_modules)[:8]},
        "urlSchemes": uniq(schemes),
        "existingAutomation": uniq(automation),
        "host": host,
        "suggestedCaptureRoute": routes,
        "notes": notes,
        "evidence": ev[:60],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
