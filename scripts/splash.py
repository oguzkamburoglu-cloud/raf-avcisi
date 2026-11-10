#!/usr/bin/env python3
"""Writes the native launch (splash) images from the current app icon.

The background is the same sky gradient as the in-game intro (.intro in src/index.html),
so when the native splash fades out only the icon disappears and the intro plays on.
iOS: the iOS app icon (assets/icon-only.png) in Splash.imageset (square, aspect-fill).
Android: design/icon/out/<lang>-android.png; English is the default (drawable-port-*,
drawable-land-*, drawable, +night), other languages go into drawable-<lang>-nodpi so the
splash matches the launcher icon in the phone's language (locale beats density/orientation).
"""
import pathlib
from PIL import Image, ImageDraw, ImageFilter

root = pathlib.Path(__file__).resolve().parent.parent
res = root / "android/app/src/main/res"
STOPS = [(0, (0x3D, 0xB6, 0xF5)), (.40, (0x9E, 0xDC, 0xFB)), (.85, (0xFB, 0xF5, 0xEC)), (1, (0xFB, 0xF5, 0xEC))]


def color_at(t):
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            k = (t - a) / (b - a) if b > a else 0
            return tuple(round(x + (y - x) * k) for x, y in zip(ca, cb))
    return STOPS[-1][1]


def splash(w, h, icon, icon_size):
    col = Image.new("RGB", (1, h))
    for y in range(h):
        col.putpixel((0, y), color_at(y / (h - 1)))
    im = col.resize((w, h))
    s = icon_size
    x, y = (w - s) // 2, (h - s) // 2
    r = int(s * .225)
    # soft shadow, like .intro .ilogo .gicon (0 8px 22px rgba(11,61,20,.28))
    pad = s // 4
    sh = Image.new("L", (s + 2 * pad, s + 2 * pad), 0)
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad, pad + s, pad + s], radius=r, fill=72)
    sh = sh.filter(ImageFilter.GaussianBlur(s * .06))
    im.paste(Image.new("RGB", sh.size, (11, 61, 20)), (x - pad, y - pad + int(s * .05)), sh)
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=255)
    im.paste(icon.resize((s, s), Image.LANCZOS), (x, y), m)
    return im


# iOS: one 2732x2732 image for every slot (light and dark)
ios_icon = Image.open(root / "assets/icon-only.png").convert("RGB")
ios = splash(2732, 2732, ios_icon, 600)
iset = root / "ios/App/App/Assets.xcassets/Splash.imageset"
for f in iset.glob("*.png"):
    ios.save(f)
ios.save(root / "assets/splash.png")
ios.save(root / "assets/splash-dark.png")
print("ios tamam")

# Android
def art(lang):
    return Image.open(root / f"design/icon/out/{lang}-android.png").convert("RGB")

en = art("en")
for f in res.glob("drawable*/splash.png"):
    if "-nodpi" in f.parent.name:
        continue
    w, h = Image.open(f).size
    splash(w, h, en, int(min(w, h) * .36)).save(f)
for lang in ("tr", "de", "es", "fr", "pt", "ru"):
    d = res / f"drawable-{lang}-nodpi"
    d.mkdir(exist_ok=True)
    splash(1280, 1920, art(lang), 460).save(d / "splash.png")
print("android tamam")
