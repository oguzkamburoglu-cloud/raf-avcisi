#!/usr/bin/env python3
"""Turns on Game Center for Raf Avcısı in App Store Connect and creates the two leaderboards the
game uses (safe to run again: only what is missing is added). Needs env ASC_KEY_ID, ASC_ISSUER_ID
and the key file path as argv[1]. The ids must match LB in the game (src/index.html).
After this, the leaderboards go live with the next app version sent to review."""
import json, sys, time, os, urllib.request, urllib.error
import jwt

BUNDLE = "com.listeal.rafavcisi"
BOARDS = [
    {"id": "raf_toplam_puan", "ref": "Toplam puan", "daily": False,
     "loc": {"tr": ("Toplam puan", "puan"), "en-US": ("Total score", "points"), "de-DE": ("Gesamtpunkte", "Punkte"),
             "es-ES": ("Puntuación total", "puntos"), "fr-FR": ("Score total", "points"), "pt-BR": ("Pontuação total", "pontos"),
             "ru": ("Общий счёт", "очков")}},
    {"id": "raf_gunun_listesi", "ref": "Günün listesi", "daily": True,
     "loc": {"tr": ("Günün listesi", "puan"), "en-US": ("Daily list", "points"), "de-DE": ("Tagesliste", "Punkte"),
             "es-ES": ("Lista del día", "puntos"), "fr-FR": ("Liste du jour", "points"), "pt-BR": ("Lista do dia", "pontos"),
             "ru": ("Список дня", "очков")}},
]
for b in BOARDS:
    for loc, (n, suf) in b["loc"].items():
        assert len(n) <= 32, (b["id"], loc)
if "--check" in sys.argv:
    print("metin uzunlukları uygun"); sys.exit(0)

KEY = open(sys.argv[1]).read()
def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      KEY, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})

def api(method, path, body=None, ok404=False):
    req = urllib.request.Request("https://api.appstoreconnect.apple.com" + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        if ok404 and e.code == 404: return {}
        raise SystemExit(f"::error::{method} {path} → {e.code}\n{msg}")

def get_all(path):
    out = []
    while path:
        r = api("GET", path)
        out += r.get("data", [])
        nxt = r.get("links", {}).get("next")
        path = nxt.replace("https://api.appstoreconnect.apple.com", "") if nxt else None
    return out

apps = api("GET", f"/v1/apps?filter[bundleId]={BUNDLE}")["data"]
if not apps: raise SystemExit(f"::error::{BUNDLE} App Store Connect'te yok")
app_id = apps[0]["id"]
apps = api("GET", f"/v1/apps?filter[bundleId]={BUNDLE}")["data"]
if not apps: raise SystemExit(f"::error::{BUNDLE} App Store Connect'te yok")
app_id = apps[0]["id"]
print("uygulama:", apps[0]["attributes"]["name"], app_id)

det = api("GET", f"/v1/apps/{app_id}/gameCenterDetail", ok404=True).get("data")
if not det:
    det = api("POST", "/v1/gameCenterDetails", {"data": {"type": "gameCenterDetails",
        "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})["data"]
    print("Game Center açıldı")
det_id = det["id"]
have = {x["attributes"]["vendorIdentifier"]: x for x in get_all(f"/v1/gameCenterDetails/{det_id}/gameCenterLeaderboards?limit=200")}

for b in BOARDS:
    lb = have.get(b["id"])
    if not lb:
        attrs = {"referenceName": b["ref"], "vendorIdentifier": b["id"], "defaultFormatter": "INTEGER",
                 "submissionType": "BEST_SCORE", "scoreSortType": "DESC"}
        if b["daily"]:
            attrs.update({"recurrenceStartDate": "2026-11-10T00:00:00Z", "recurrenceDuration": "P1D",
                          "recurrenceRule": "FREQ=DAILY;INTERVAL=1"})
        lb = api("POST", "/v1/gameCenterLeaderboards", {"data": {"type": "gameCenterLeaderboards", "attributes": attrs,
            "relationships": {"gameCenterDetail": {"data": {"type": "gameCenterDetails", "id": det_id}}}}})["data"]
        print("liderlik tablosu oluşturuldu:", b["id"])
    else:
        print("liderlik tablosu var:", b["id"])
    locs = {x["attributes"]["locale"] for x in get_all(f"/v1/gameCenterLeaderboards/{lb['id']}/localizations")}
    for loc, (name, suf) in b["loc"].items():
        if loc in locs: continue
        api("POST", "/v1/gameCenterLeaderboardLocalizations", {"data": {"type": "gameCenterLeaderboardLocalizations",
            "attributes": {"locale": loc, "name": name, "formatterSuffix": " " + suf, "formatterSuffixSingular": " " + suf},
            "relationships": {"gameCenterLeaderboard": {"data": {"type": "gameCenterLeaderboards", "id": lb["id"]}}}}})
        print("  dil eklendi:", loc)
print("Game Center hazır")
