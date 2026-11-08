#!/usr/bin/env python3
"""Attaches the newest processed build to the version being prepared, fills App Review
Information (no sign-in, notes, contact) and reports what the version page still lacks.
Contact phone comes from env REVIEW_PHONE (optional). argv[1] = key file."""
import json, os, sys, time, urllib.request, urllib.error
import jwt
KEY = open(sys.argv[1]).read()
NOTES = ("Raf Avcısı (Shelf Hunter) is an offline single-player puzzle game. No account or sign-in is needed; "
         "everything is available on launch. Optional rewarded ads (Google AdMob) are shown only when the player taps "
         "\"Watch an ad\" (when a helper runs out, or for +30 seconds when time is up). In-app purchases: "
         "yardim_paketi_5 (consumable help pack) and premium (non-consumable, skips ads); open them with the Shop button, "
         "which also has Restore Purchases. Languages: Turkish, English, German, Spanish, French, Portuguese, Russian. "
         "It is the companion game of our shopping list app PickyList (same developer); PickyList can open it with "
         "rafavcisi://oyun?from=pickylist to give a daily bonus, but the game works fully without it.")
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
