#!/usr/bin/env python3
"""Puts the real AdMob ids into the app (replaces Google's test ids).

    python3 scripts/set-admob-ids.py \
        --android-app ca-app-pub-XXXX~YYYY --android-unit ca-app-pub-XXXX/ZZZZ \
        --ios-app ca-app-pub-XXXX~YYYY --ios-unit ca-app-pub-XXXX/ZZZZ
    npm run sync

App ids contain "~", ad unit ids contain "/". Ids can be given for one platform only."""
import argparse, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
for k in ["android-app", "android-unit", "ios-app", "ios-unit"]:
    ap.add_argument("--" + k)
a = ap.parse_args()

APP = re.compile(r"^ca-app-pub-\d{16}~\d{10}$")
UNIT = re.compile(r"^ca-app-pub-\d{16}/\d{10}$")
for name, val, rx in [("android-app", a.android_app, APP), ("ios-app", a.ios_app, APP),
                      ("android-unit", a.android_unit, UNIT), ("ios-unit", a.ios_unit, UNIT)]:
    if val is not None and not rx.match(val):
        sys.exit(f"--{name} biçimi yanlış: {val}")

def edit(rel, pattern, value):
    p = root / rel
    s = p.read_text(encoding="utf-8")
    s2, n = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), s)
    if n != 1:
        sys.exit(f"{rel}: yer bulunamadı ({n})")
    p.write_text(s2, encoding="utf-8")
    print(f"{rel}: {value}")

if a.android_app:
    edit("android/app/src/main/AndroidManifest.xml",
         r'(android:name="com\.google\.android\.gms\.ads\.APPLICATION_ID"\s+android:value=")[^"]+(")', a.android_app)
if a.ios_app:
    edit("ios/App/App/Info.plist", r"(<key>GADApplicationIdentifier</key>\s*<string>)[^<]+(</string>)", a.ios_app)
if a.android_unit:
    edit("src/native.js", r'(android: ")[^"]+(")', a.android_unit)
if a.ios_unit:
    edit("src/native.js", r'(ios: ")[^"]+(")', a.ios_unit)
