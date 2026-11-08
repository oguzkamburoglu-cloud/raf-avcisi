#!/usr/bin/env python3
"""Fills the App Store page of the version being prepared: name, subtitle, privacy URL,
description, keywords, support URL, promo text and iPhone 6.9" screenshots in 7 languages,
plus category and copyright. Texts come from store/MAGAZA_METINLERI*.md, screenshots from
store/screenshots/<lang>/ios/. Safe to run again. argv[1] = key file, or --check to only
print what would be sent."""
import json, os, re, sys, time, hashlib, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "store"
SUPPORT = "https://raf-avcisi.web.app/"
PRIVACY = "https://raf-avcisi.web.app/gizlilik.html"
COPYRIGHT = "2026 MoguzK"
LOCALES = {"tr": "tr", "en-US": "en", "de-DE": "de", "es-ES": "es", "fr-FR": "fr", "pt-BR": "pt", "ru": "ru"}
SHOTS = ["1-start", "2-play", "3-level", "4-win", "5-bonus"]

def blocks(section):
    out, label, val = [], None, []
    for line in section.splitlines():
        m = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", line)
        if m or line.startswith("##") or line.strip() == "---":
            if label: out.append((label, "\n".join(val).strip()))
            label, val = (m.group(1), [m.group(2)]) if m else (None, [])
        elif label is not None:
            val.append(line)
    if label: out.append((label, "\n".join(val).strip()))
    return out

def classify(bl):
    d = {}
    for label, v in bl:
        l = label.lower()
        if "(play)" in l or "play)" in l: continue
        if re.search(r"alt başlık|subtitle|untertitel|subtítulo|sous-titre|подзаголовок", l): d.setdefault("subtitle", v)
        elif re.search(r"anahtar|keywords|palabras|mots-clés|palavras|ключевые", l): d.setdefault("keywords", v)
        elif re.search(r"tanıtım", l): d.setdefault("promo", v)
        elif re.match(r"(ad|name|nombre|nom|nome|название)\b", l): d.setdefault("name", v)
        elif re.match(r"(açıklama|description|beschreibung|descripción|descrição|описание)\s*:?$", l.strip(" :")+":") or \
             re.match(r"^(açıklama|description|beschreibung|descripción|descrição|описание)\s*:?\s*$", l): d.setdefault("description", v)
    return d

main = (STORE / "MAGAZA_METINLERI.md").read_text(encoding="utf-8")
langs = (STORE / "MAGAZA_METINLERI_DILLER.md").read_text(encoding="utf-8")
def section(text, start, end_pat=r"\n## "):
    i = text.index(start); j = re.search(end_pat, text[i + len(start):])
    return text[i: i + len(start) + (j.start() if j else len(text))]
TEXT = {
    "tr": classify(blocks(section(main, "## App Store (App Store Connect)"))),
    "en-US": classify(blocks(section(main, "## İngilizce mağaza girişi"))),
}
for loc, head in [("de-DE", "## Deutsch"), ("es-ES", "## Español"), ("fr-FR", "## Français"), ("pt-BR", "## Português"), ("ru", "## Русский")]:
    TEXT[loc] = classify(blocks(section(langs, head)))
LIMITS = {"name": 30, "subtitle": 30, "keywords": 100, "promo": 170, "description": 4000}
for loc, d in TEXT.items():
    for k in ["name", "subtitle", "keywords", "description"]:
        assert d.get(k), (loc, k, d.keys())
    for k, n in LIMITS.items():
        if k in d: assert len(d[k]) <= n, (loc, k, len(d[k]))
    for s in SHOTS:
        assert (STORE / "screenshots" / LOCALES[loc] / "ios" / f"{s}.png").exists(), (loc, s)
if "--check" in sys.argv:
    for loc, d in TEXT.items():
        print(f"== {loc}: {d['name']} | {d['subtitle']} | {len(d['keywords'])} kw | {len(d['description'])} desc | promo={'promo' in d}")
        print("   ", d["description"][:70].replace("\n", " "), "…", d["description"][-50:].replace("\n", " "))
    sys.exit(0)

import jwt
KEY = open(sys.argv[1]).read()
def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      KEY, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})
problems = []
def api(method, path, body=None, soft=False):
    req = urllib.request.Request("https://api.appstoreconnect.apple.com" + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read(); return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        if soft:
            try: detail = "; ".join(x.get("detail", x.get("title", "")) for x in json.loads(msg)["errors"])
            except Exception: detail = msg[:300]
            problems.append(f"{method} {path.split('?')[0]}: {detail}"); print("  ! " + problems[-1]); return None
        raise SystemExit(f"::error::{method} {path} → {e.code}\n{msg}")
def get_all(path):
    out = []
    while path:
        r = api("GET", path); out += r.get("data", [])
        nxt = r.get("links", {}).get("next")
        path = nxt.replace("https://api.appstoreconnect.apple.com", "") if nxt else None
    return out

for u in [SUPPORT, PRIVACY]:
    try: code = urllib.request.urlopen(urllib.request.Request(u, method="GET"), timeout=15).status
    except Exception as e: code = getattr(e, "code", str(e))
    print("adres", u, "→", code)
    if code != 200: problems.append(f"{u} açılmıyor ({code}); Apple bu adresi kontrol eder")

app = api("GET", "/v1/apps?filter[bundleId]=com.listeal.rafavcisi")["data"][0]
app_id = app["id"]; print("uygulama", app["attributes"]["name"], "ana dil", app["attributes"]["primaryLocale"])

# app info (name, subtitle, privacy url, category) on the editable app info
infos = get_all(f"/v1/apps/{app_id}/appInfos")
info = next((i for i in infos if i["attributes"].get("appStoreState") in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED", "WAITING_FOR_REVIEW", None) or i["attributes"].get("state") in ("PREPARE_FOR_SUBMISSION", None)), infos[0])
api("PATCH", f"/v1/appInfos/{info['id']}", {"data": {"type": "appInfos", "id": info["id"], "relationships": {
    "primaryCategory": {"data": {"type": "appCategories", "id": "GAMES"}},
    "primarySubcategoryOne": {"data": {"type": "appCategories", "id": "GAMES_PUZZLE"}},
    "primarySubcategoryTwo": {"data": {"type": "appCategories", "id": "GAMES_CASUAL"}}}}}, soft=True)
have = {l["attributes"]["locale"]: l for l in get_all(f"/v1/appInfos/{info['id']}/appInfoLocalizations")}
def put_info(loc, attrs):
    if loc in have:
        return api("PATCH", f"/v1/appInfoLocalizations/{have[loc]['id']}", {"data": {"type": "appInfoLocalizations", "id": have[loc]["id"], "attributes": attrs}}, soft=True)
    return api("POST", "/v1/appInfoLocalizations", {"data": {"type": "appInfoLocalizations", "attributes": dict(attrs, locale=loc),
               "relationships": {"appInfo": {"data": {"type": "appInfos", "id": info["id"]}}}}}, soft=True)
for loc, d in TEXT.items():
    ok = put_info(loc, {"name": d["name"], "subtitle": d["subtitle"], "privacyPolicyUrl": PRIVACY})
    if not ok and loc in have:   # usually a name already used by another app: keep the rest
        put_info(loc, {"subtitle": d["subtitle"], "privacyPolicyUrl": PRIVACY})
    print("ad/alt başlık", loc, "tamam" if ok else "sorunlu")

# version page
vers = get_all(f"/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS")
ver = next(v for v in vers if v["attributes"]["appStoreState"] in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED"))
print("sürüm", ver["attributes"]["versionString"], ver["attributes"]["appStoreState"])
api("PATCH", f"/v1/appStoreVersions/{ver['id']}", {"data": {"type": "appStoreVersions", "id": ver["id"], "attributes": {"copyright": COPYRIGHT}}}, soft=True)
vl = {l["attributes"]["locale"]: l for l in get_all(f"/v1/appStoreVersions/{ver['id']}/appStoreVersionLocalizations")}
for loc, d in TEXT.items():
    attrs = {"description": d["description"], "keywords": d["keywords"], "supportUrl": SUPPORT, "marketingUrl": SUPPORT}
    if d.get("promo"): attrs["promotionalText"] = d["promo"]
    if loc in vl:
        lid = vl[loc]["id"]
        api("PATCH", f"/v1/appStoreVersionLocalizations/{lid}", {"data": {"type": "appStoreVersionLocalizations", "id": lid, "attributes": attrs}}, soft=True)
    else:
        r = api("POST", "/v1/appStoreVersionLocalizations", {"data": {"type": "appStoreVersionLocalizations", "attributes": dict(attrs, locale=loc),
                "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": ver["id"]}}}}}, soft=True)
        if not r: continue
        lid = r["data"]["id"]
    print("açıklama", loc)

    sets = get_all(f"/v1/appStoreVersionLocalizations/{lid}/appScreenshotSets")
    st = next((s for s in sets if s["attributes"]["screenshotDisplayType"] == "APP_IPHONE_67"), None)
    if not st:
        st = api("POST", "/v1/appScreenshotSets", {"data": {"type": "appScreenshotSets", "attributes": {"screenshotDisplayType": "APP_IPHONE_67"},
                 "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": lid}}}}})["data"]
    existing = get_all(f"/v1/appScreenshotSets/{st['id']}/appScreenshots")
    if len(existing) >= len(SHOTS):
        print("  ekran görüntüleri zaten var"); continue
    for e in existing: api("DELETE", f"/v1/appScreenshots/{e['id']}", soft=True)
    for s in SHOTS:
        img = (STORE / "screenshots" / LOCALES[loc] / "ios" / f"{s}.png").read_bytes()
        r = api("POST", "/v1/appScreenshots", {"data": {"type": "appScreenshots", "attributes": {"fileName": f"{s}.png", "fileSize": len(img)},
                "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": st["id"]}}}}})["data"]
        for op in r["attributes"]["uploadOperations"]:
            urllib.request.urlopen(urllib.request.Request(op["url"], method=op["method"], data=img[op["offset"]:op["offset"] + op["length"]],
                                   headers={h["name"]: h["value"] for h in op["requestHeaders"]})).read()
        api("PATCH", f"/v1/appScreenshots/{r['id']}", {"data": {"type": "appScreenshots", "id": r["id"],
            "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(img).hexdigest()}}})
    print("  5 ekran görüntüsü yüklendi")

print("\nbitti." if not problems else "\nbitti, şunlara bak:\n- " + "\n- ".join(problems))
