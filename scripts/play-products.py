#!/usr/bin/env python3
"""Creates (or updates) the two in-app products on Google Play in 7 languages.
Env PLAY_KEY = service account key file. Optional argv: currency micros-pack micros-premium."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import play_api as p
CUR = sys.argv[1] if len(sys.argv) > 1 else "USD"
PRICE = {"yardim_paketi_5": sys.argv[2] if len(sys.argv) > 2 else "990000", "premium": sys.argv[3] if len(sys.argv) > 3 else "2990000"}
L = {
 "yardim_paketi_5": {"tr-TR": ("Yardım paketi", "5 Geri al, 5 İpucu, 5 Karıştır"), "en-US": ("Help pack", "5 Undo, 5 Hint, 5 Shuffle"),
   "de-DE": ("Hilfepaket", "5× Zurück, 5× Tipp, 5× Mischen"), "es-ES": ("Pack de ayudas", "5 deshacer, 5 pistas, 5 mezclar"),
   "fr-FR": ("Pack d'aides", "5 annulations, 5 indices, 5 mélanges"), "pt-BR": ("Pacote de ajudas", "5 desfazer, 5 dicas, 5 embaralhar"),
   "ru-RU": ("Набор подсказок", "5 отмен, 5 подсказок, 5 перемешиваний")},
 "premium": {"tr-TR": ("Premium", "Reklam izlemeden tüm ödüller ve 10'ar yardım"), "en-US": ("Premium", "All rewards without ads and 10 of each help"),
   "de-DE": ("Premium", "Alle Belohnungen ohne Werbung und je 10 Hilfen"), "es-ES": ("Premium", "Todos los premios sin anuncios y 10 de cada ayuda"),
   "fr-FR": ("Premium", "Toutes les récompenses sans pub et 10 de chaque aide"), "pt-BR": ("Premium", "Todos os prêmios sem anúncios e 10 de cada ajuda"),
   "ru-RU": ("Premium", "Все награды без рекламы и по 10 подсказок")}}
RV = "regionsVersion.version=2026/01"
def regional(micros):
    m = int(micros)
    r = p.call("POST", "/pricing:convertRegionPrices", {"price": {"currencyCode": CUR, "units": str(m // 1000000), "nanos": (m % 1000000) * 1000}})
    cfg = [{"regionCode": k, "price": v["price"], "availability": "AVAILABLE"} for k, v in r["convertedRegionPrices"].items()]
    other = r.get("convertedOtherRegionsPrice")
    return cfg, other
for sku, loc in L.items():
    cfg, other = regional(PRICE[sku])
    opt = {"purchaseOptionId": "satin-al", "buyOption": {"legacyCompatible": True, "multiQuantityEnabled": False},
           "regionalPricingAndAvailabilityConfigs": cfg}
    if other:
        opt["newRegionsConfig"] = {"usdPrice": other["usdPrice"], "eurPrice": other["eurPrice"], "availability": "AVAILABLE"}
    body = {"packageName": p.PKG, "productId": sku,
            "listings": [{"languageCode": k, "title": t, "description": d} for k, (t, d) in loc.items()],
            "purchaseOptions": [opt]}
    r = p.call("PATCH", f"/onetimeproducts/{sku}?allowMissing=true&updateMask=listings,purchaseOptions&{RV}", body, soft=True)
    if not r: print(sku, "HATA"); continue
    a = p.call("POST", f"/oneTimeProducts/{sku}/purchaseOptions:batchUpdateStates", {"requests": [{"activatePurchaseOptionRequest": {
        "packageName": p.PKG, "productId": sku, "purchaseOptionId": "satin-al", "latencyTolerance": "PRODUCT_UPDATE_LATENCY_TOLERANCE_LATENCY_TOLERANT"}}]}, soft=True)
    print(sku, "oluşturuldu,", len(cfg), "ülke fiyatı,", "satışta" if a else "etkinleştirilemedi")
