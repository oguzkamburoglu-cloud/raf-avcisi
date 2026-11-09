#!/usr/bin/env python3
"""Writes the Android launcher icons per language from design/icon/out/<lang>-android.png
(render with design/icon/render.cjs). English is the default; other languages go into
mipmap-<lang>-<density> folders, so the phone shows the icon in its own language.
The adaptive icon XML insets both layers by 16.7%, so each layer image is the visible area."""
import pathlib
from PIL import Image, ImageDraw
root = pathlib.Path(__file__).resolve().parent.parent
res = root / "android/app/src/main/res"
src = root / "design/icon/out"
DENS = {"ldpi": .75, "mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
LANGS = {"en": "", "tr": "-tr", "de": "-de", "es": "-es", "fr": "-fr", "pt": "-pt", "ru": "-ru"}
for lang, suf in LANGS.items():
    art = Image.open(src / f"{lang}-android.png").convert("RGB").crop((24, 24, 1000, 1000))
    for d, k in DENS.items():
        out = res / f"mipmap{suf}-{d}"; out.mkdir(exist_ok=True)
        layer = int(72 * k)
        art.resize((layer, layer), Image.LANCZOS).save(out / "ic_launcher_background.png")
        Image.new("RGBA", (layer, layer), (0, 0, 0, 0)).save(out / "ic_launcher_foreground.png")
        s = int(48 * k); a = art.resize((s, s), Image.LANCZOS)
        sq = Image.new("L", (s, s), 0); ImageDraw.Draw(sq).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * .2), fill=255)
        ci = Image.new("L", (s, s), 0); ImageDraw.Draw(ci).ellipse([0, 0, s - 1, s - 1], fill=255)
        for name, m in (("ic_launcher.png", sq), ("ic_launcher_round.png", ci)):
            im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); im.paste(a, (0, 0), m); im.save(out / name)
    print(lang, "tamam")
