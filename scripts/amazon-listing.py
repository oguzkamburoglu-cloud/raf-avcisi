#!/usr/bin/env python3
"""Writes store/amazon/AMAZON_METINLERI.md: the Amazon Appstore listing in 7 languages (title,
short and long description from the Play texts, plus feature bullets and keywords), and the
5 in-app items. Also writes store/amazon/amazon.sdktester.json for testing with Amazon App Tester."""
import json, sys, pathlib, importlib.util
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parent; OUT = ROOT / "store/amazon"
sys.argv = [sys.argv[0], "--check-quiet"]
spec = importlib.util.spec_from_file_location("pl", HERE / "play-listing.py"); src = (HERE / "play-listing.py").read_text(encoding="utf-8")
src = src.split('if "--check" in sys.argv:')[0]  # only the parsing part
ns = {"__file__": str(HERE / "play-listing.py")}; exec(compile(src, "play-listing.py", "exec"), ns)
T = ns["T"]
sys.path.insert(0, str(HERE)); from iap_new import NEW

BUL = {
 "tr-TR": ["Market raflarında aynı üç ürünü eşleştir, alışveriş listeni süre bitmeden tamamla",
           "Yüzlerce reyon: buzlu raflar, kayan bant, sallanan raflar, son kullanma tarihi ve patron sandıkları",
           "Mıknatıs, Sihirli değnek, Buz, Büyüteç gibi eğlenceli jokerler",
           "Her gün yeni Günün listesi, günlük çark ve reyon ustalığı madalyaları",
           "İnternetsiz oynanır; 7 dilde"],
 "en-US": ["Match three of a kind on supermarket shelves and finish your shopping list before time runs out",
           "Hundreds of aisles: frozen shelves, conveyor belts, wobbly shelves, expiry dates and boss chests",
           "Fun jokers like Magnet, Magic wand, Freeze and Magnifier",
           "A new Daily list every day, a daily wheel and aisle mastery medals",
           "Plays offline; in 7 languages"],
 "de-DE": ["Finde drei gleiche Produkte im Supermarktregal und erledige deine Einkaufsliste, bevor die Zeit abläuft",
           "Hunderte Gänge: Tiefkühlregale, Förderbänder, wackelnde Regale, Ablaufdaten und Boss-Truhen",
           "Lustige Joker wie Magnet, Zauberstab, Eis und Lupe",
           "Jeden Tag eine neue Tagesliste, ein tägliches Glücksrad und Meister-Medaillen",
           "Offline spielbar; in 7 Sprachen"],
 "es-ES": ["Junta tres productos iguales en los estantes del súper y completa tu lista antes de que se acabe el tiempo",
           "Cientos de pasillos: estantes congelados, cintas transportadoras, estantes que se tambalean, caducidades y cofres del jefe",
           "Comodines divertidos como Imán, Varita mágica, Hielo y Lupa",
           "Una nueva lista del día cada día, ruleta diaria y medallas de maestría",
           "Se juega sin conexión; en 7 idiomas"],
 "fr-FR": ["Aligne trois produits identiques en rayon et termine ta liste de courses avant la fin du temps",
           "Des centaines de rayons : surgelés, tapis roulants, étagères bancales, dates de péremption et coffres du patron",
           "Des jokers amusants : Aimant, Baguette magique, Glace et Loupe",
           "Une nouvelle liste du jour chaque jour, une roue quotidienne et des médailles de maîtrise",
           "Jouable hors ligne ; en 7 langues"],
 "pt-BR": ["Junte três produtos iguais nas prateleiras do mercado e complete sua lista antes que o tempo acabe",
           "Centenas de corredores: prateleiras congeladas, esteiras, prateleiras balançando, validade e baús do chefe",
           "Coringas divertidos como Ímã, Varinha mágica, Gelo e Lupa",
           "Uma nova lista do dia todos os dias, roleta diária e medalhas de maestria",
           "Funciona offline; em 7 idiomas"],
 "ru-RU": ["Собирай по три одинаковых товара на полках и успей закрыть список покупок",
           "Сотни рядов: замороженные полки, конвейер, шатающиеся полки, сроки годности и сундуки босса",
           "Весёлые джокеры: Магнит, Волшебная палочка, Лёд и Лупа",
           "Новый список дня каждый день, ежедневное колесо и медали мастерства",
           "Играй без интернета; 7 языков"],
}
KEY = {
 "tr-TR": "market, bulmaca, eşleştirme, üçlü, alışveriş listesi, raf, sıralama, zeka oyunu, PickyList",
 "en-US": "grocery, puzzle, match 3, triple match, sort, shelf, supermarket, shopping list, brain game, PickyList",
 "de-DE": "Supermarkt, Puzzle, Match 3, Sortieren, Regal, Einkaufsliste, Denkspiel, PickyList",
 "es-ES": "supermercado, puzle, tres en raya, ordenar, estantes, lista de la compra, juego mental, PickyList",
 "fr-FR": "supermarché, puzzle, match 3, trier, rayon, liste de courses, jeu de réflexion, PickyList",
 "pt-BR": "supermercado, quebra-cabeça, combinar 3, organizar, prateleira, lista de compras, PickyList",
 "ru-RU": "супермаркет, головоломка, три в ряд, сортировка, полки, список покупок, PickyList",
}
OLD = {
 "yardim_paketi_5": ("CONSUMABLE", "0.99", {"tr-TR": ("Yardım paketi", "Her jokerden 5 tane"), "en-US": ("Help pack", "5 of every joker")}),
 "premium": ("ENTITLED", "2.99", {"tr-TR": ("Premium", "Reklam izlemeden tüm ödüller ve 10'ar yardım"), "en-US": ("Premium", "All rewards without ads and 10 of each help")}),
}
items = [(k, *v) for k, v in OLD.items()] + [(p["id"], "CONSUMABLE", p["usd"], {"tr-TR": tuple(p["loc"]["tr"]), "en-US": tuple(p["loc"]["en-US"])}) for p in NEW]

md = ["# Raf Avcısı · Amazon Appstore metinleri", "",
      "_`scripts/amazon-listing.py` üretir; Play metinlerinden (store/MAGAZA_METINLERI*.md) alınır. Görseller: proje dosyalarında `raf-avcisi/amazon/<dil>/`._", "",
      "## Genel bilgiler (Amazon Developer Console › App › General Information / Availability)", "",
      "- **Paket adı:** com.listeal.rafavcisi (Play ile aynı)",
      "- **Kategori:** Games › Puzzles & Trivia (alt kategori yoksa Puzzle)",
      "- **İletişim / destek sitesi:** https://raf-avcisi.web.app/",
      "- **Gizlilik politikası:** https://raf-avcisi.web.app/gizlilik.html",
      "- **Fiyat:** Ücretsiz · **Uygulama içi satın alma:** Evet · **Reklam:** Evet (Google AdMob ödüllü reklam)",
      "- **Cihazlar:** Fire tabletler (Fire TV kapalı: oyun dokunmatik ve dikey). Yön: dikey.",
      "- **Amazon DRM / Appstore lisansı:** Hayır.",
      "- **İçerik derecelendirmesi (Content Rating):** şiddet, korku, kumar, cinsellik, küfür vb. hepsi Hayır/None. "
      "Reklam içerir: Evet. Uygulama içi satın alma: Evet. Kullanıcı konumunu toplar: Hayır (AdMob kaba IP konumu kullanır). "
      "Hedef kitle çocuklar değil (13+), \"Is this app directed at children under 13?\" → No.", ""]
for loc, d in T.items():
    b = BUL[loc]; k = KEY[loc]
    assert 3 <= len(b) <= 5 and len(d["full"]) <= 4000 and len(d["short"]) <= 1200
    md += [f"## {loc}", "", f"**Title:** {d['title']}", "", f"**Short description:** {d['short']}", "",
           "**Product feature bullets:**", *[f"- {x}" for x in b], "", f"**Keywords:** {k}", "",
           "**Long description:**", "", d["full"], ""]
md += ["## Uygulama içi ürünler (In-App Items)", "",
       "Amazon'da SKU'lar Play ve App Store ile **birebir aynı** olmalı (oyun kodu bu adları kullanıyor). "
       "Simgeler: `store/amazon/iap/<sku>-114.png` (küçük) ve `-512.png` (büyük).", "",
       "| SKU | Amazon türü | Fiyat (USD, temel) | Başlık (tr / en) | Açıklama (tr / en) |", "| --- | --- | --- | --- | --- |"]
tester = {}
for sku, typ, usd, loc in items:
    tr, en = loc["tr-TR"], loc["en-US"]
    md.append(f"| `{sku}` | {'Consumable' if typ == 'CONSUMABLE' else 'Entitlement'} | {usd} | {tr[0]} / {en[0]} | {tr[1]} / {en[1]} |")
    tester[sku] = {"itemType": typ, "price": float(usd), "title": en[0], "description": en[1], "smallIconUrl": f"http://localhost/{sku}-114.png"}
md += ["", "Amazon App Tester ile denemek için `store/amazon/amazon.sdktester.json` dosyasını Fire tabletin `/sdcard/` klasörüne kopyala.", ""]
(OUT / "AMAZON_METINLERI.md").write_text("\n".join(md), encoding="utf-8")
(OUT / "amazon.sdktester.json").write_text(json.dumps(tester, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("store/amazon/AMAZON_METINLERI.md ve amazon.sdktester.json yazıldı.")
