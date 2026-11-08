"""Tiny Google Play Developer API client using a service account key file (env PLAY_KEY)."""
import json, os, time, urllib.request, urllib.error
import jwt
PKG = "com.listeal.rafavcisi"
B = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/" + PKG
U = "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/" + PKG
_tok = {}
def token():
    if _tok.get("exp", 0) > time.time() + 60: return _tok["t"]
    sa = json.load(open(os.environ["PLAY_KEY"])); now = int(time.time())
    a = jwt.encode({"iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/androidpublisher",
                    "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}, sa["private_key"], algorithm="RS256")
    r = json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token",
        data=f"grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion={a}".encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"})).read())
    _tok.update(t=r["access_token"], exp=now + r["expires_in"]); return _tok["t"]
def call(method, url, body=None, raw=None, ct="application/json", soft=False):
    if not url.startswith("http"): url = B + url
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url, method=method, data=data, headers={"Authorization": "Bearer " + token(), "Content-Type": ct})
    try:
        t = urllib.request.urlopen(req).read(); return json.loads(t) if t.strip() else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        if soft: print(f"  ! {method} {url.split(PKG)[-1].split('?')[0]} {e.code}: {msg[:400]}"); return None
        raise SystemExit(f"{method} {url} -> {e.code}\n{msg[:2000]}")
