#!/usr/bin/env python3
"""Fills the Google Play store listing in 7 languages: title, short and full description,
icon, feature graphic and 5 phone screenshots each, plus contact details.
Env PLAY_KEY = service account key file. --check only prints the texts."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
ROOT = pathlib.Path(__file__).resolve().parent.parent; STORE = ROOT / "store"
LANGS = {"tr-TR": "tr", "en-US": "en", "de-DE": "de", "es-ES": "es", "fr-FR": "fr", "pt-BR": "pt", "ru-RU": "ru"}
SHOTS = ["1-start", "2-play", "3-level", "4-win", "5-bonus"]

def blocks(section):
    out, label, val = [], None, []
    for line in section.splitlines():
        m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", line)
        if m or line.startswith("##") or line.strip() == "---":
            if label: out.append((label, "\n".join(val).strip()))
            label, val = (m.group(1), [m.group(2)]) if m else (None, [])
        elif label is not None: val.append(line)
    if label: out.append((label, "\n".join(val).strip()))
    return out
def section(text, start):
    i = text.index(start); j = re.search(r"\n## ", text[i + len(start):])
    return text[i: i + len(start) + (j.start() if j else len(text))]
def pick(bl):
    d = {}
    for label, v in bl:
        l = label.lower().strip(" :")
        if re.search(r"kısa açıklama|short description|kurzbeschreibung|descripción breve|description courte|descrição curta|краткое описание", l): d.setdefault("short", v)
        elif re.match(r"(ad|name|nombre|nom|nome|название|uygulama adı)\b", l): d.setdefault("title", v)
        elif re.match(r"^(açıklama|description|beschreibung|descripción|descrição|описание)\s*:?$", l): d.setdefault("full", v)
    return d
main = (STORE / "MAGAZA_METINLERI.md").read_text(encoding="utf-8"); oth = (STORE / "MAGAZA_METINLERI_DILLER.md").read_text(encoding="utf-8")
T = {"tr-TR": pick(blocks(section(main, "## App Store (App Store Connect)")) + blocks(section(main, "## Google Play (Play Console)"))),
     "en-US": pick(blocks(section(main, "## İngilizce mağaza girişi")))}
for loc, h in [("de-DE", "## Deutsch"), ("es-ES", "## Español"), ("fr-FR", "## Français"), ("pt-BR", "## Português"), ("ru-RU", "## Русский")]:
    T[loc] = pick(blocks(section(oth, h)))
for loc, d in T.items():
    for k, n in (("title", 30), ("short", 80), ("full", 4000)):
        assert d.get(k) and len(d[k]) <= n, (loc, k, len(d.get(k) or ""))
    l = LANGS[loc]
    for f in [STORE / f"icons/play-icon-512-{l}.png", STORE / f"feature/{l}.png"] + [STORE / f"screenshots/{l}/android/{s}.png" for s in SHOTS]:
        assert f.exists(), f
if "--check" in sys.argv:
    for loc, d in T.items(): print(loc, "|", d["title"], "|", d["short"], "|", len(d["full"]))
    sys.exit(0)

import play_api as p
e = p.call("POST", "/edits", {})["id"]
p.call("PUT", f"/edits/{e}/details", {"defaultLanguage": "tr-TR", "contactEmail": "oguz.kamburoglu@gmail.com", "contactWebsite": "https://raf-avcisi.web.app/"})
for loc, d in T.items():
    p.call("PUT", f"/edits/{e}/listings/{loc}", {"language": loc, "title": d["title"], "shortDescription": d["short"], "fullDescription": d["full"]})
    l = LANGS[loc]
    for typ, files in (("icon", [STORE / f"icons/play-icon-512-{l}.png"]), ("featureGraphic", [STORE / f"feature/{l}.png"]),
                       ("phoneScreenshots", [STORE / f"screenshots/{l}/android/{s}.png" for s in SHOTS])):
        p.call("DELETE", f"/edits/{e}/listings/{loc}/{typ}")
        for f in files:
            p.call("POST", f"{p.U}/edits/{e}/listings/{loc}/{typ}?uploadType=media", raw=f.read_bytes(), ct="image/png")
    print("mağaza sayfası", loc, "tamam")
r = p.call("POST", f"/edits/{e}:commit", soft=True)
if r is None:
    r = p.call("POST", f"/edits/{e}:commit?changesNotSentForReview=true")
print("kaydedildi", r.get("id"))
