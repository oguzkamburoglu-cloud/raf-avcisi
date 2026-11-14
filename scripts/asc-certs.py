#!/usr/bin/env python3
"""Lists signing certificates; with --revoke removes the throwaway development ones CI created.

Every CI archive lets Xcode create an "Apple Development: Created via API" certificate, and Apple
caps how many an account may hold. Only development certificates named "Created via API" are
revoked; distribution certificates and anything a person created are left alone.
argv[1] = key file."""
import json, os, sys, time, urllib.request
import jwt
KEY = open(sys.argv[1]).read()
REVOKE = "--revoke" in sys.argv
def api(path, method="GET"):
    now = int(time.time())
    t = jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"}, KEY, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})
    r = urllib.request.urlopen(urllib.request.Request("https://api.appstoreconnect.apple.com" + path, method=method, headers={"Authorization": "Bearer " + t})).read()
    return json.loads(r) if r else {}
n = 0
for c in api("/v1/certificates?limit=200")["data"]:
    a = c["attributes"]
    ci = a["certificateType"] in ("DEVELOPMENT", "IOS_DEVELOPMENT") and "Created via API" in (a.get("name") or "") + (a.get("displayName") or "")
    print(a["certificateType"], "|", a.get("displayName"), "|", a.get("expirationDate"), "| CI geçici" if ci else "")
    if ci and REVOKE:
        api("/v1/certificates/" + c["id"], "DELETE"); n += 1
if REVOKE: print("iptal edilen geçici geliştirme sertifikası:", n)
