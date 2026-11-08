#!/usr/bin/env python3
"""Creates the two in-app purchases in App Store Connect (safe to run again: existing
products are only completed, never duplicated). Needs env ASC_KEY_ID, ASC_ISSUER_ID and
the key file path as argv[1]. Review screenshot is the one thing left to add by hand."""
import json, sys, time, os, urllib.request, urllib.error
import jwt

BUNDLE = "com.listeal.rafavcisi"
PRODUCTS = [
    {"id": "yardim_paketi_5", "type": "CONSUMABLE", "ref": "Yardım paketi", "usd": "0.99",
     "loc": {
        "tr": ("Yardım paketi", "5 Geri al, 5 İpucu, 5 Karıştır"),
        "en-US": ("Help pack", "5 Undo, 5 Hint, 5 Shuffle"),
        "de-DE": ("Hilfepaket", "5× Zurück, 5× Tipp, 5× Mischen"),
        "es-ES": ("Pack de ayudas", "5 deshacer, 5 pistas, 5 mezclar"),
        "fr-FR": ("Pack d'aides", "5 annulations, 5 indices, 5 mélanges"),
        "pt-BR": ("Pacote de ajudas", "5 desfazer, 5 dicas, 5 embaralhar"),
        "ru": ("Набор подсказок", "5 отмен, 5 подсказок, 5 перемешиваний"),
     }},
    {"id": "premium", "type": "NON_CONSUMABLE", "ref": "Premium", "usd": "2.99",
     "loc": {
        "tr": ("Premium", "Reklamsız tüm ödüller ve 10'ar yardım"),
        "en-US": ("Premium", "All rewards without ads, 10 of each help"),
        "de-DE": ("Premium", "Belohnungen ohne Werbung, je 10 Hilfen"),
        "es-ES": ("Premium", "Premios sin anuncios y 10 de cada ayuda"),
        "fr-FR": ("Premium", "Récompenses sans pub, 10 de chaque aide"),
        "pt-BR": ("Premium", "Prêmios sem anúncios e 10 de cada ajuda"),
        "ru": ("Premium", "Награды без рекламы и по 10 подсказок"),
     }},
]
REVIEW_NOTE = "Shop button on the level screen (bag icon). Purchases unlock in-game helps; Premium skips rewarded ads. Restore Purchases is in the Shop."

for p in PRODUCTS:
    for loc, (n, d) in p["loc"].items():
        assert len(n) <= 30 and len(d) <= 45, (p["id"], loc, len(n), len(d))
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
print("uygulama:", apps[0]["attributes"]["name"], app_id)
existing = {i["attributes"]["productId"]: i for i in get_all(f"/v1/apps/{app_id}/inAppPurchasesV2?limit=200")}
territories = None

for p in PRODUCTS:
    if p["id"] in existing:
        iap_id = existing[p["id"]]["id"]; print(p["id"], "zaten var", iap_id)
    else:
        r = api("POST", "/v2/inAppPurchases", {"data": {"type": "inAppPurchases",
            "attributes": {"name": p["ref"], "productId": p["id"], "inAppPurchaseType": p["type"], "reviewNote": REVIEW_NOTE},
            "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})
        iap_id = r["data"]["id"]; print(p["id"], "oluşturuldu", iap_id)

    have = {l["attributes"]["locale"] for l in get_all(f"/v2/inAppPurchases/{iap_id}/inAppPurchaseLocalizations")}
    for loc, (n, d) in p["loc"].items():
        if loc in have: continue
        api("POST", "/v1/inAppPurchaseLocalizations", {"data": {"type": "inAppPurchaseLocalizations",
            "attributes": {"locale": loc, "name": n, "description": d},
            "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap_id}}}}})
        print("  dil", loc)

    sched = api("GET", f"/v2/inAppPurchases/{iap_id}/iapPriceSchedule", ok404=True).get("data")
    has_price = sched and get_all(f"/v1/inAppPurchasePriceSchedules/{sched['id']}/manualPrices?limit=1")
    if not has_price:
        pts = get_all(f"/v2/inAppPurchases/{iap_id}/pricePoints?filter[territory]=USA&limit=200")
        pp = next(x for x in pts if x["attributes"]["customerPrice"] in (p["usd"], p["usd"] + "0"))
        api("POST", "/v1/inAppPurchasePriceSchedules", {"data": {"type": "inAppPurchasePriceSchedules",
            "relationships": {"inAppPurchase": {"data": {"type": "inAppPurchases", "id": iap_id}},
                              "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
                              "manualPrices": {"data": [{"type": "inAppPurchasePrices", "id": "${p0}"}]}}},
            "included": [{"type": "inAppPurchasePrices", "id": "${p0}", "attributes": {"startDate": None},
                          "relationships": {"inAppPurchasePricePoint": {"data": {"type": "inAppPurchasePricePoints", "id": pp["id"]}}}}]})
        print("  fiyat", p["usd"], "$ (diğer ülkeler Apple'ın eşdeğer fiyatı)")

    avail = api("GET", f"/v2/inAppPurchases/{iap_id}/inAppPurchaseAvailability", ok404=True).get("data")
    if not avail:
        if territories is None:
            territories = [{"type": "territories", "id": t["id"]} for t in get_all("/v1/territories?limit=200")]
        api("POST", "/v1/inAppPurchaseAvailabilities", {"data": {"type": "inAppPurchaseAvailabilities",
            "attributes": {"availableInNewTerritories": True},
            "relationships": {"inAppPurchase": {"data": {"type": "inAppPurchases", "id": iap_id}},
                              "availableTerritories": {"data": territories}}}})
        print("  tüm ülkelerde satışta:", len(territories))
print("bitti. Kalan: her ürüne inceleme ekran görüntüsü (Mağaza ekranı) ekle.")
