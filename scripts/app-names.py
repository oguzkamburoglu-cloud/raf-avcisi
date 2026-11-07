#!/usr/bin/env python3
"""Writes the localized home-screen app name for Android (res/values-xx) and iOS (xx.lproj),
and registers the iOS files in the Xcode project. Edit NAMES and run: python3 scripts/app-names.py"""
import pathlib, hashlib, re

NAMES = {  # language code: name under the icon (keep short; iOS cuts after ~12-14 characters)
    "en": "Shelf Hunter",
    "tr": "Raf Avcısı",
    "az": "Rəf Ovçusu",
    "de": "Regaljäger",
    "fr": "Chasse Rayon",
    "es": "Caza Estantes",
    "it": "Caccia Scaffali",
    "pt": "Caça Prateleira",
    "nl": "Schappenjager",
    "pl": "Łowca Półek",
    "ru": "Охотник за полками",
    "uk": "Мисливець полиць",
    "ar": "صياد الرفوف",
    "el": "Κυνηγός Ραφιών",
    "ja": "棚ハンター",
    "ko": "선반 헌터",
    "zh-Hans": "货架猎人",
}
DEFAULT = "en"
root = pathlib.Path(__file__).resolve().parent.parent

# Android: values/ = default (English), values-xx/ for the rest
res = root / "android/app/src/main/res"
android_code = {"zh-Hans": "b+zh+Hans"}
for code, name in NAMES.items():
    d = res / ("values" if code == DEFAULT else "values-" + android_code.get(code, code))
    d.mkdir(parents=True, exist_ok=True)
    f = d / "strings.xml"
    esc = name.replace("'", "\\'")
    if code == DEFAULT:
        s = f.read_text(encoding="utf-8")
        s = re.sub(r'<string name="app_name">.*?</string>', f'<string name="app_name">{esc}</string>', s)
        s = re.sub(r'<string name="title_activity_main">.*?</string>', f'<string name="title_activity_main">{esc}</string>', s)
        f.write_text(s, encoding="utf-8")
    else:
        f.write_text(f"<?xml version='1.0' encoding='utf-8'?>\n<resources>\n    <string name=\"app_name\">{esc}</string>\n"
                     f"    <string name=\"title_activity_main\">{esc}</string>\n</resources>\n", encoding="utf-8")

# iOS: xx.lproj/InfoPlist.strings, all in one PBXVariantGroup
app = root / "ios/App/App"
for code, name in NAMES.items():
    d = app / f"{code}.lproj"; d.mkdir(exist_ok=True)
    (d / "InfoPlist.strings").write_text(f'"CFBundleDisplayName" = "{name}";\n"CFBundleName" = "{name}";\n', encoding="utf-8")

pbx = root / "ios/App/App.xcodeproj/project.pbxproj"
s = pbx.read_text(encoding="utf-8")
GROUP = "7A1F00022FF0000000A1B001"
def oid(code): return "7A1F" + hashlib.md5(code.encode()).hexdigest()[:20].upper()
refs = {c: ("7A1F00032FF0000000A1B001" if c == "en" else "7A1F00042FF0000000A1B001" if c == "tr" else oid(c)) for c in NAMES}
for code, r in refs.items():
    if r not in s:
        s = s.replace("/* End PBXFileReference section */",
            f'\t\t{r} /* {code} */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.strings; name = {code}; path = {code}.lproj/InfoPlist.strings; sourceTree = "<group>"; }};\n/* End PBXFileReference section */', 1)
m = re.search(GROUP + r' /\* InfoPlist.strings \*/ = \{\n\t\t\tisa = PBXVariantGroup;\n\t\t\tchildren = \(\n(.*?)\t\t\t\);', s, re.S)
children = "".join(f"\t\t\t\t{r} /* {c} */,\n" for c, r in refs.items())
s = s[:m.start(1)] + children + s[m.end(1):]
m = re.search(r"knownRegions = \(\n(.*?)\t\t\t\);", s, re.S)
regions = "".join(f'\t\t\t\t{c if re.fullmatch(r"[a-z]+", c) else chr(34)+c+chr(34)},\n' for c in NAMES) + "\t\t\t\tBase,\n"
s = s[:m.start(1)] + regions + s[m.end(1):]
pbx.write_text(s, encoding="utf-8")
print(f"{len(NAMES)} dil yazıldı")
