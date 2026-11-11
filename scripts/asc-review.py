#!/usr/bin/env python3
"""Attaches the newest processed build to the version being prepared, fills App Review
Information (no sign-in, notes, contact) and reports what the version page still lacks.
Contact phone comes from env REVIEW_PHONE (optional). argv[1] = key file."""
import json, os, sys, time, urllib.request, urllib.error
import jwt
KEY = open(sys.argv[1]).read()
NOTES = """1) SCREEN RECORDING: attached to this App Review Information section (recorded on a physical iPhone with the latest iOS, starting from app launch: home screen, playing a level, shop with in-app purchases and Restore Purchases, rewarded ad).

2) PURPOSE AND AUDIENCE: Raf Avcisi (Shelf Hunter) is a casual, offline, single-player puzzle game for everyone (rated 4+). The player sorts groceries on supermarket shelves: tap an item, tap a shelf, three identical items on a shelf clear it. Each level shows a shopping list; finishing the list before the timer ends wins the level. It offers a short, relaxing brain-teaser and is the companion game of our shopping list app PickyList (same developer).

3) HOW TO USE: No account, login, sign-in or sample files are needed; everything works right after launch. Tap Start shopping to play aisle 1. Helpers (undo, hint, shuffle) are at the bottom. The Shop link (bottom of the home screen, also in the pause menu) shows the in-app purchases: yardim_paketi_5 (consumable, +5 of each helper) and premium (non-consumable, removes ads and adds helpers), plus Restore Purchases. When a helper runs out, or when time is up, the player may optionally tap Watch an ad for a reward. There is no user-generated content and no account, so no account deletion or reporting is needed.

4) EXTERNAL SERVICES: Apple StoreKit (in-app purchases); Google AdMob (optional rewarded ads) with Google User Messaging Platform (consent). No backend server, no AI services, no authentication service. PickyList can optionally open the game with rafavcisi://oyun?from=pickylist for a daily bonus; the game works fully without it.

5) REGIONS: The app works the same in all regions. Only the interface language follows the device (Turkish, English, German, Spanish, French, Portuguese, Russian; others get English).

6) REGULATED / THIRD-PARTY MATERIAL: Not applicable. All graphics are our own; product pictures are the device's built-in emoji.

7) GAME CENTER: Optional. The Leaderboard screen (trophy button on the home screen) shows the player's own records and two Game Center leaderboards: raf_toplam_puan (total score) and raf_gunun_listesi (daily list, resets every day). The game is fully playable without signing in to Game Center."""
def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      KEY, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})
def api(method, path, body=None, soft=False):
    req = urllib.request.Request("https://api.appstoreconnect.apple.com" + path, method=method,
        data=json.dumps(body).encode() if body else None, headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read(); return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        if soft: print("  ! ", method, path.split("?")[0], e.code, msg[:400]); return None
        raise SystemExit(f"::error::{method} {path} → {e.code}\n{msg}")

app = api("GET", "/v1/apps?filter[bundleId]=com.listeal.rafavcisi")["data"][0]; app_id = app["id"]
ver = next(v for v in api("GET", f"/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS")["data"]
           if v["attributes"]["appStoreState"] in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED"))
print("sürüm", ver["attributes"]["versionString"])
builds = api("GET", f"/v1/builds?filter[app]={app_id}&sort=-uploadedDate&limit=10")["data"]
for b in builds: print("derleme", b["attributes"]["version"], b["attributes"]["processingState"], b["attributes"].get("usesNonExemptEncryption"))
ok = [b for b in builds if b["attributes"]["processingState"] == "VALID"]
if ok:
    b = ok[0]
    api("PATCH", f"/v1/appStoreVersions/{ver['id']}/relationships/build", {"data": {"type": "builds", "id": b["id"]}}, soft=True)
    print("sürüme bağlanan derleme:", b["attributes"]["version"])
else:
    print("işlenmiş derleme yok")

attrs = {"demoAccountRequired": False, "notes": NOTES, "contactFirstName": "Oguz", "contactLastName": "Kamburoglu",
         "contactEmail": "oguz.kamburoglu@gmail.com"}
if os.environ.get("REVIEW_PHONE"): attrs["contactPhone"] = os.environ["REVIEW_PHONE"]
rd = api("GET", f"/v1/appStoreVersions/{ver['id']}/appStoreReviewDetail", soft=True)
print("mevcut inceleme bilgisi:", json.dumps({k: v for k, v in ((rd or {}).get("data") or {}).get("attributes", {}).items() if k in ("contactFirstName","demoAccountRequired","notes")}, ensure_ascii=False)[:200], "telefon var" if ((rd or {}).get("data") or {}).get("attributes", {}).get("contactPhone") else "telefon yok")
if rd and rd.get("data"):
    api("PATCH", f"/v1/appStoreReviewDetails/{rd['data']['id']}", {"data": {"type": "appStoreReviewDetails", "id": rd["data"]["id"], "attributes": attrs}}, soft=True)
else:
    api("POST", "/v1/appStoreReviewDetails", {"data": {"type": "appStoreReviewDetails", "attributes": attrs,
        "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": ver["id"]}}}}}, soft=True)
print("inceleme bilgileri yazıldı (telefon:", "var" if "contactPhone" in attrs else "YOK", ")")

# Game Center: switch it on for this version and release the leaderboards with it
gv = (api("GET", f"/v1/appStoreVersions/{ver['id']}/gameCenterAppVersion", soft=True) or {}).get("data")
if not gv:
    gv = (api("POST", "/v1/gameCenterAppVersions", {"data": {"type": "gameCenterAppVersions",
          "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": ver["id"]}}}}}, soft=True) or {}).get("data")
if gv:
    if not gv["attributes"].get("enabled"):
        api("PATCH", f"/v1/gameCenterAppVersions/{gv['id']}", {"data": {"type": "gameCenterAppVersions", "id": gv["id"], "attributes": {"enabled": True}}}, soft=True)
    print("Game Center bu sürümde açık")
det = (api("GET", f"/v1/apps/{app_id}/gameCenterDetail", soft=True) or {}).get("data")
if det:
    rel = api("GET", f"/v1/gameCenterDetails/{det['id']}/leaderboardReleases?include=gameCenterLeaderboard&limit=50", soft=True) or {}
    done = {(r.get("relationships", {}).get("gameCenterLeaderboard", {}).get("data") or {}).get("id") for r in rel.get("data", [])}
    for lb in (api("GET", f"/v1/gameCenterDetails/{det['id']}/gameCenterLeaderboards?limit=50", soft=True) or {}).get("data", []):
        if lb["id"] in done: print("tablo sürümde:", lb["attributes"]["vendorIdentifier"]); continue
        r = api("POST", "/v1/gameCenterLeaderboardReleases", {"data": {"type": "gameCenterLeaderboardReleases", "relationships": {
            "gameCenterDetail": {"data": {"type": "gameCenterDetails", "id": det["id"]}},
            "gameCenterLeaderboard": {"data": {"type": "gameCenterLeaderboards", "id": lb["id"]}}}}}, soft=True)
        print("tablo sürüme eklendi:" if r else "tablo eklenemedi:", lb["attributes"]["vendorIdentifier"])

for l in api("GET", f"/v1/appStoreVersions/{ver['id']}/appStoreVersionLocalizations")["data"]:
    sets = api("GET", f"/v1/appStoreVersionLocalizations/{l['id']}/appScreenshotSets?include=appScreenshots")
    desc = ", ".join(f"{s['attributes']['screenshotDisplayType']}={len(s['relationships']['appScreenshots']['data'])}" for s in sets["data"])
    print("ekran görüntüleri", l["attributes"]["locale"], desc or "YOK")

# in-app purchase readiness
for i in api("GET", f"/v1/apps/{app_id}/inAppPurchasesV2?limit=50")["data"]:
    a = i["attributes"]; iid = i["id"]
    print("ürün", a["productId"], a.get("state"), "| familySharable", a.get("familySharable"), "| reviewNote", bool(a.get("reviewNote")))
    sh = api("GET", f"/v2/inAppPurchases/{iid}/appStoreReviewScreenshot", soft=True)
    if sh and sh.get("data"):
        s = sh["data"]["attributes"]; print("   görsel", s.get("fileName"), s.get("assetDeliveryState"), s.get("imageAsset") and (s["imageAsset"].get("width"), s["imageAsset"].get("height")))
    else: print("   görsel YOK")
    ps = api("GET", f"/v2/inAppPurchases/{iid}/iapPriceSchedule", soft=True); print("   fiyat planı", bool(ps and ps.get("data")))
    av = api("GET", f"/v2/inAppPurchases/{iid}/inAppPurchaseAvailability", soft=True); print("   satış ülkeleri", bool(av and av.get("data")))
    locs = api("GET", f"/v2/inAppPurchases/{iid}/inAppPurchaseLocalizations")["data"]
    print("   diller", [(l["attributes"]["locale"], l["attributes"].get("state")) for l in locs])
