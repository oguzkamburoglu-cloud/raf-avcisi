#!/usr/bin/env python3
"""Submits the version being prepared to App Review together with the first in-app purchases.
argv[1] = key file."""
import json, os, sys, time, urllib.request, urllib.error
import jwt
KEY = open(sys.argv[1]).read()
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
        try: det = "; ".join(x.get("detail") or x.get("title", "") for x in json.loads(msg)["errors"])
        except Exception: det = msg[:500]
        if soft: print(f"  ! {method} {path.split('?')[0]} {e.code}: {det}"); return None
        raise SystemExit(f"::error::{method} {path} → {e.code}: {det}\n{msg[:4000]}")

app_id = api("GET", "/v1/apps?filter[bundleId]=com.listeal.rafavcisi")["data"][0]["id"]
ver = next(v for v in api("GET", f"/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS")["data"]
           if v["attributes"]["appStoreState"] in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED"))
# "Content rights": the game shows ads (third-party content) and open-licensed fonts/emoji, which we may use
api("PATCH", f"/v1/apps/{app_id}", {"data": {"type": "apps", "id": app_id, "attributes": {"contentRightsDeclaration": "USES_THIRD_PARTY_CONTENT"}}}, soft=True)
b = api("GET", f"/v1/appStoreVersions/{ver['id']}/build").get("data")
print("sürüm", ver["attributes"]["versionString"], "derleme", b and b["attributes"]["version"])

subs = api("GET", f"/v1/reviewSubmissions?filter[app]={app_id}&filter[platform]=IOS&filter[state]=READY_FOR_REVIEW").get("data", [])
sub = subs[0] if subs else api("POST", "/v1/reviewSubmissions", {"data": {"type": "reviewSubmissions",
        "attributes": {"platform": "IOS"}, "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})["data"]
items = api("GET", f"/v1/reviewSubmissions/{sub['id']}/items?include=appStoreVersion").get("data", [])
print("paketteki öğeler:", [(it["id"], it["attributes"].get("state"), bool((it.get("relationships", {}).get("appStoreVersion") or {}).get("data"))) for it in items])
if not any((it.get("relationships", {}).get("appStoreVersion") or {}).get("data") for it in items):
    api("POST", "/v1/reviewSubmissionItems", {"data": {"type": "reviewSubmissionItems",
        "relationships": {"reviewSubmission": {"data": {"type": "reviewSubmissions", "id": sub["id"]}},
                          "appStoreVersion": {"data": {"type": "appStoreVersions", "id": ver["id"]}}}}})
print("inceleme paketi", sub["id"], "hazır")
for i in api("GET", f"/v1/apps/{app_id}/inAppPurchasesV2?limit=50")["data"]:
    if i["attributes"]["state"] == "READY_TO_SUBMIT":
        r = api("POST", "/v1/inAppPurchaseSubmissions", {"data": {"type": "inAppPurchaseSubmissions",
            "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": i["id"]}}}}}, soft=True)
        print("satın alma sürüme eklendi:" if r else "satın alma eklenemedi:", i["attributes"]["productId"])
    else:
        print("satın alma", i["attributes"]["productId"], i["attributes"]["state"])

r = api("PATCH", f"/v1/reviewSubmissions/{sub['id']}", {"data": {"type": "reviewSubmissions", "id": sub["id"], "attributes": {"submitted": True}}})
print("GÖNDERİLDİ:", r["data"]["attributes"].get("state"))
