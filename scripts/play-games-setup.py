#!/usr/bin/env python3
"""Play Games setup helper for Raf Avcısı (runs on a GitHub runner with the Play service account).
1) Finds the SHA-1 of Google's app signing key (from a Play-generated universal APK) and of the upload key.
2) Registers the Android app com.listeal.rafavcisi in Firebase project ailiste with that SHA-1, which makes
   Google create the Android OAuth client Play Games needs.
3) With env GAMES_APP_ID set, creates the two leaderboards through the Games Configuration API.
Env: PLAY_KEY (service account json path), optional APKSIGNER, UPLOAD_SHA1, GAMES_APP_ID."""
import json, os, subprocess, sys, time, urllib.request, urllib.error
import jwt
sys.path.insert(0, os.path.dirname(__file__))
import play_api as P

SA = json.load(open(os.environ["PLAY_KEY"]))
def tok(scope):
    now = int(time.time())
    a = jwt.encode({"iss": SA["client_email"], "scope": scope, "aud": "https://oauth2.googleapis.com/token",
                    "iat": now, "exp": now + 3600}, SA["private_key"], algorithm="RS256")
    return json.loads(urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token",
        data=f"grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion={a}".encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"})).read())["access_token"]
def req(method, url, token, body=None):
    r = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        t = urllib.request.urlopen(r).read(); return json.loads(t) if t.strip() else {}
    except urllib.error.HTTPError as e:
        print(f"  ! {method} {url} -> {e.code}: {e.read().decode()[:600]}"); return None

print("service account:", SA["client_email"], "project:", SA.get("project_id"))
# 1) app signing key SHA-1
sha1 = None
for vc in (16, 9, 5):
    lst = P.call("GET", f"/generatedApks/{vc}", soft=True)
    if not lst: continue
    for g in lst.get("generatedApks", []):
        print("versionCode", vc, "signing key sha256:", g.get("certificateSha256Hash"))
        uni = g.get("generatedUniversalApk")
        if not uni: continue
        url = P.B + f"/generatedApks/{vc}/downloads/{uni['downloadId']}:download?alt=media"
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + P.token()})).read()
        open("/tmp/universal.apk", "wb").write(data)
        out = subprocess.run([os.environ.get("APKSIGNER", "apksigner"), "verify", "--print-certs", "/tmp/universal.apk"],
                             capture_output=True, text=True).stdout
        print(out)
        for line in out.splitlines():
            if "SHA-1 digest" in line: sha1 = line.split(":")[-1].strip()
        break
    if sha1: break
def colon(h): h = h.replace(":", "").upper(); return ":".join(h[i:i+2] for i in range(0, len(h), 2))
print("APP SIGNING SHA-1:", colon(sha1) if sha1 else "bulunamadı")
if os.environ.get("UPLOAD_SHA1"): print("UPLOAD KEY SHA-1:", os.environ["UPLOAD_SHA1"])

# 2) Firebase Android app + SHA-1 (auto-creates the Android OAuth client)
proj = "ailiste"
ft = tok("https://www.googleapis.com/auth/cloud-platform")
apps = req("GET", f"https://firebase.googleapis.com/v1beta1/projects/{proj}/androidApps?pageSize=100", ft) or {}
app = next((a for a in apps.get("apps", []) if a.get("packageName") == P.PKG), None)
if app is None and apps is not None:
    op = req("POST", f"https://firebase.googleapis.com/v1beta1/projects/{proj}/androidApps", ft,
             {"packageName": P.PKG, "displayName": "Raf Avcısı"})
    if op and op.get("name"):
        for _ in range(30):
            o = req("GET", f"https://firebase.googleapis.com/v1beta1/{op['name']}", ft)
            if o and o.get("done"): app = o.get("response"); break
            time.sleep(2)
print("firebase android app:", app and app.get("name"))
if app and sha1:
    have = req("GET", f"https://firebase.googleapis.com/v1beta1/{app['name']}/sha", ft) or {}
    hashes = {c.get("shaHash", "").lower() for c in have.get("certificates", [])}
    for h in [sha1] + ([os.environ["UPLOAD_SHA1"]] if os.environ.get("UPLOAD_SHA1") else []):
        h = h.replace(":", "").lower()
        if h in hashes: print("sha zaten var:", h); continue
        print("sha eklendi:" if req("POST", f"https://firebase.googleapis.com/v1beta1/{app['name']}/sha", ft,
              {"shaHash": h, "certType": "SHA_1"}) is not None else "sha eklenemedi:", h)

# 3) leaderboards (needs the Play Games project id)
gid = os.environ.get("GAMES_APP_ID", "").strip()
if gid:
    gt = P.token()
    base = f"https://gamesconfiguration.googleapis.com/games/v1configuration/applications/{gid}/leaderboards"
    have = req("GET", base, gt) or {}
    names = {(i.get("published") or i.get("draft") or {}).get("name", {}).get("translations", [{}])[0].get("value") for i in have.get("items", [])}
    for i in have.get("items", []): print("tablo var:", i.get("id"), json.dumps(i.get("draft", {}).get("name", {}))[:120])
    def loc(d): return {"kind": "gamesConfiguration#localizedStringBundle",
                        "translations": [{"kind": "gamesConfiguration#localizedString", "locale": k, "value": v} for k, v in d.items()]}
    for key, nm in [("raf_toplam_puan", {"en-US": "Total score", "tr-TR": "Toplam puan"}),
                    ("raf_gunun_listesi", {"en-US": "Daily list", "tr-TR": "Günün listesi"})]:
        if nm["en-US"] in names: continue
        r = req("POST", base, gt, {"kind": "gamesConfiguration#leaderboardConfiguration", "token": key, "scoreOrder": "LARGER_IS_BETTER",
                "draft": {"kind": "gamesConfiguration#leaderboardConfigurationDetail", "name": loc(nm),
                          "scoreFormat": {"numberFormatType": "NUMERIC", "numDecimalPlaces": 0}}})
        print("tablo oluşturuldu:" if r else "tablo oluşturulamadı:", key, r and r.get("id"))
