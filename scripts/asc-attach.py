#!/usr/bin/env python3
"""Uploads a file (the screen recording App Review asked for) as an App Review attachment of the
version being prepared, replacing an attachment with the same name. argv[1] = key file, argv[2] = file."""
import hashlib, json, os, sys, time, urllib.request, urllib.error
import jwt
KEY = open(sys.argv[1]).read(); PATH = sys.argv[2]
def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      KEY, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})
def api(method, path, body=None):
    req = urllib.request.Request("https://api.appstoreconnect.apple.com" + path, method=method,
        data=json.dumps(body).encode() if body else None, headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read(); return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"::error::{method} {path} → {e.code}\n{e.read().decode()[:3000]}")

app_id = api("GET", "/v1/apps?filter[bundleId]=com.listeal.rafavcisi")["data"][0]["id"]
ver = next(v for v in api("GET", f"/v1/apps/{app_id}/appStoreVersions?filter[platform]=IOS")["data"]
           if v["attributes"]["appStoreState"] in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED"))
rd = api("GET", f"/v1/appStoreVersions/{ver['id']}/appStoreReviewDetail?include=appStoreReviewAttachments")
rd_id = rd["data"]["id"]; name = os.path.basename(PATH); data = open(PATH, "rb").read()
for a in rd.get("included", []):
    if a["attributes"].get("fileName") == name:
        api("DELETE", f"/v1/appStoreReviewAttachments/{a['id']}"); print("eski ek silindi:", name)
att = api("POST", "/v1/appStoreReviewAttachments", {"data": {"type": "appStoreReviewAttachments",
    "attributes": {"fileName": name, "fileSize": len(data)},
    "relationships": {"appStoreReviewDetail": {"data": {"type": "appStoreReviewDetails", "id": rd_id}}}}})["data"]
for op in att["attributes"]["uploadOperations"]:
    r = urllib.request.Request(op["url"], method=op["method"], data=data[op["offset"]:op["offset"] + op["length"]],
                               headers={h["name"]: h["value"] for h in op.get("requestHeaders", [])})
    urllib.request.urlopen(r).read()
api("PATCH", f"/v1/appStoreReviewAttachments/{att['id']}", {"data": {"type": "appStoreReviewAttachments", "id": att["id"],
    "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
for _ in range(20):
    st = (api("GET", f"/v1/appStoreReviewAttachments/{att['id']}")["data"]["attributes"].get("assetDeliveryState") or {})
    print("ek durumu:", st.get("state"), st.get("errors") or "")
    if st.get("state") in ("COMPLETE", "FAILED"): break
    time.sleep(3)
if st.get("state") != "COMPLETE": raise SystemExit("::error::ek yüklenemedi")
print("ek yüklendi:", name, len(data), "bayt")
