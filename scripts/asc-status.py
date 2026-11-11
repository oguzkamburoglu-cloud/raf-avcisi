#!/usr/bin/env python3
"""Prints the App Store state of the app version and the in-app purchases. argv[1] = key file."""
import json, os, sys, time, urllib.request
import jwt
KEY = open(sys.argv[1]).read()
def api(path):
    now = int(time.time())
    t = jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"}, KEY, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})
    return json.loads(urllib.request.urlopen(urllib.request.Request("https://api.appstoreconnect.apple.com" + path, headers={"Authorization": "Bearer " + t})).read())
app = api("/v1/apps?filter[bundleId]=com.listeal.rafavcisi")["data"][0]["id"]
for v in api(f"/v1/apps/{app}/appStoreVersions?filter[platform]=IOS")["data"]: print("sürüm", v["attributes"]["versionString"], v["attributes"]["appStoreState"])
for i in api(f"/v1/apps/{app}/inAppPurchasesV2")["data"]: print("satın alma", i["attributes"]["productId"], i["attributes"]["state"])
for s in api(f"/v1/reviewSubmissions?filter[app]={app}")["data"]: print("inceleme", s["attributes"].get("state"), s["attributes"].get("submittedDate"))
for b in api(f"/v1/builds?filter[app]={app}&sort=-uploadedDate&limit=6")["data"]: print("derleme", b["attributes"]["version"], b["attributes"]["processingState"], b["attributes"].get("uploadedDate"))
for v in api(f"/v1/apps/{app}/appStoreVersions?filter[platform]=IOS")["data"]:
    b = api(f"/v1/appStoreVersions/{v['id']}/build").get("data")
    print("sürüm", v["attributes"]["versionString"], "bağlı derleme", b and b["attributes"]["version"])
    try:
        rd = api(f"/v1/appStoreVersions/{v['id']}/appStoreReviewDetail?include=appStoreReviewAttachments")
        for a in rd.get("included", []): print("inceleme eki", a["attributes"].get("fileName"), a["attributes"].get("fileSize"), (a["attributes"].get("assetDeliveryState") or {}).get("state"))
        if not rd.get("included"): print("inceleme eki YOK")
    except Exception as e: print("inceleme eki okunamadı", e)
