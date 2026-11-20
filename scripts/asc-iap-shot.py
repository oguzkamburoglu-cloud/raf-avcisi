#!/usr/bin/env python3
"""Replaces the App Review screenshot of the 1.3 purchases (starter pack, 1200 and 3500 coins)
with store/iap-inceleme-1.3.png, the current shop that shows them. The older products keep theirs.
Needs env ASC_KEY_ID, ASC_ISSUER_ID and the key file path as argv[1]. Safe to run again."""
import hashlib, json, os, pathlib, sys, time, urllib.error, urllib.request
import jwt

BUNDLE = "com.listeal.rafavcisi"
IDS = ["baslangic_paketi", "para_1200", "para_3500"]
IMG = (pathlib.Path(__file__).resolve().parent.parent / "store/iap-inceleme-1.3.png").read_bytes()
SUM = hashlib.md5(IMG).hexdigest()
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

app_id = api("GET", f"/v1/apps?filter[bundleId]={BUNDLE}")["data"][0]["id"]
iaps = {i["attributes"]["productId"]: i for i in api("GET", f"/v1/apps/{app_id}/inAppPurchasesV2?limit=200")["data"]}
for pid in IDS:
    if pid not in iaps: print(pid, "yok, atlandı"); continue
    iid = iaps[pid]["id"]
    old = api("GET", f"/v2/inAppPurchases/{iid}/appStoreReviewScreenshot", ok404=True).get("data")
    if old and old["attributes"].get("sourceFileChecksum") == SUM:
        print(pid, "yeni görsel zaten yüklü"); continue
    if old:
        api("DELETE", f"/v1/inAppPurchaseAppStoreReviewScreenshots/{old['id']}")
        print(pid, "eski görsel silindi")
    r = api("POST", "/v1/inAppPurchaseAppStoreReviewScreenshots", {"data": {"type": "inAppPurchaseAppStoreReviewScreenshots",
        "attributes": {"fileName": "iap-inceleme-1.3.png", "fileSize": len(IMG)},
        "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iid}}}}})["data"]
    for op in r["attributes"]["uploadOperations"]:
        req = urllib.request.Request(op["url"], method=op["method"], data=IMG[op["offset"]:op["offset"] + op["length"]],
                                     headers={h["name"]: h["value"] for h in op["requestHeaders"]})
        urllib.request.urlopen(req).read()
    api("PATCH", f"/v1/inAppPurchaseAppStoreReviewScreenshots/{r['id']}", {"data": {"type": "inAppPurchaseAppStoreReviewScreenshots",
        "id": r["id"], "attributes": {"uploaded": True, "sourceFileChecksum": SUM}}})
    print(pid, "yeni inceleme görseli yüklendi")
time.sleep(20)
for pid in IDS:
    if pid not in iaps: continue
    iid = iaps[pid]["id"]
    s = api("GET", f"/v2/inAppPurchases/{iid}/appStoreReviewScreenshot", ok404=True).get("data")
    st = api("GET", f"/v2/inAppPurchases/{iid}")["data"]["attributes"].get("state")
    print(pid, "durum:", st, "| görsel:", s and s["attributes"].get("assetDeliveryState"))
print("bitti.")
