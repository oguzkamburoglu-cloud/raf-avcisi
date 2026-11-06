#!/usr/bin/env python3
"""Copies the web version of the game (the claude.ai artifact's index.html) into src/index.html
and applies the store-app changes. Run after every web update:

    python3 scripts/import-web.py ../index.html && npm run sync

Each patch must match exactly once; if the web code changed so a patch no longer matches,
the script stops and names it."""
import sys, re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else root.parent / "index.html")
s = src.read_text(encoding="utf-8")

def sub(name, old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f"Yama uymadı: {name} (bulunan {n}, beklenen {count})")
    s = s.replace(old, new)

# 1. full document head, bundled fonts, native bridge
head_end = s.index("<style>")
s = '''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#FBF5EC">
<meta name="format-detection" content="telephone=no">
<title>Raf Avcısı</title>
<!-- Store build: fonts are bundled (fonts/fonts.css) so the game works offline and looks the same on iOS and Android -->
<link rel="stylesheet" href="fonts/fonts.css">
<script src="native.js"></script>
''' + s[head_end:]
sub("style end", "</style>\n", "</style>\n</head>\n<body>\n")
s = s.rstrip() + "\n</body>\n</html>\n"

# 2. touch behaviour and notch
sub("tap highlight", "-webkit-tap-highlight-color:transparent;", "-webkit-tap-highlight-color:transparent;-webkit-touch-callout:none;overscroll-behavior:none;")
sub("appbar safe area", ".appbar{display:flex;align-items:center;gap:12px;padding-block:10px}",
    ".appbar{display:flex;align-items:center;gap:12px;padding-block:10px;padding-top:max(10px, env(safe-area-inset-top,0px))}")

# 3. emoji: system Noto on Android, bundled Noto (SVG font "Raf Emoji") on iOS
sub("emoji font", '.item,.em,.shelf .back span,.navbtn .ic,.how li .e{font-family:"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif}',
    '.item,.em,.shelf .back span,.navbtn .ic,.how li .e,#mute{font-family:"Noto Color Emoji","Apple Color Emoji","Segoe UI Emoji",sans-serif}\n'
    'html.ios body{font-family:var(--f-ui),"Raf Emoji"}\n'
    'html.ios .item,html.ios .em,html.ios .shelf .back span,html.ios .navbtn .ic,html.ios .how li .e,html.ios #mute{font-family:"Raf Emoji","Apple Color Emoji",sans-serif}')

# 4. store link per platform
sub("appUrl", 'function appUrl(){const ios=/iPhone|iPad|iPod/.test(navigator.userAgent);',
    'function appUrl(){const pf=window.RAF_NATIVE?RAF_NATIVE.platform:"";const ios=pf==="ios"||(!pf&&/iPhone|iPad|iPod/.test(navigator.userAgent));')

# 5. vibration -> native haptics (navigator.vibrate does nothing on iOS)
sub("buzz", "function buzz(p){try{if(navigator.vibrate)navigator.vibrate(p)}catch(e){}}",
    "function buzz(p){try{if(window.RAF_NATIVE)RAF_NATIVE.haptic(p);else if(navigator.vibrate)navigator.vibrate(p)}catch(e){}}")

# 6. app sent to background: same as hiding the tab (pause game, stop timer/music)
m = re.search(r'document\.addEventListener\("visibilitychange",\(\)=>\{if\(document\.hidden\)\{(.*?)\}\}\);', s)
if not m: sys.exit("Yama uymadı: visibilitychange")
s = s[:m.start()] + 'window.RAF_ONPAUSE=()=>{' + m.group(1) + 'try{ac&&ac.suspend()}catch(e){}};\n' \
    'window.RAF_ONRESUME=()=>{try{ac&&ac.resume()}catch(e){}};\n' \
    'document.addEventListener("visibilitychange",()=>{if(document.hidden)RAF_ONPAUSE();else RAF_ONRESUME()});' + s[m.end():]

out = root / "src/index.html"
out.write_text(s, encoding="utf-8")
print(f"{src} → {out} ({len(s)//1024} KB)")
