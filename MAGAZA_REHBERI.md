# Raf Avcısı'nı App Store ve Google Play'e yükleme rehberi

Bu klasör, oyunu iki mağazaya da gönderilebilir hale getiren mobil uygulama projesidir. Senin yapacakların: geliştirici hesapları, imzalama, derleme ve yükleme. Hepsi aşağıda sırayla.

## Neden Capacitor?

Oyun tek bir HTML/JavaScript dosyası. Capacitor bu dosyayı hiç değiştirmeden gerçek bir Android ve iOS uygulamasının içine koyuyor. Flutter seçseydik oyunu Dart ile baştan yazmak gerekirdi; görünüm de PickyList'teki gibi kalmazdı, çünkü renkler, yazı tipleri ve Noto emoji ürünleri şu an zaten web sürümünde birebir ayarlı. Capacitor ile web sürümü (ailiste.web.app/oyun) ve mağaza sürümü aynı kodla güncellenir.

Uygulamaya eklenenler:
- Yazı tipleri (Roboto, Fraunces) ve ürün emojileri pakete gömülü: oyun internetsiz açılır, iPhone'da da Android'deki Noto ürün görselleri çıkar.
- Uygulama simgesi, açılış ekranı (krem zemin, PickyList yeşili), dikey ekran kilidi, çentik/Dynamic Island boşluğu.
- Raf temizlenince, kazanınca ve hatalı hamlede titreşim.
- PickyList bağlantısı: `rafavcisi://oyun?from=pickylist&list=Domates,Kahve` oyunu açar ve bonusu verir.
- PickyList butonları Play Store / App Store uygulamasını açar.

## Kimlikler

| | Değer |
| --- | --- |
| Uygulama adı (ana ekranda) | Türkçe telefonlarda "Raf Avcısı", diğer dillerde "Shelf Hunter" |
| Android applicationId / iOS Bundle ID | `com.listeal.rafavcisi` |
| Sürüm | 1.0 (derleme 1) |
| URL şeması | `rafavcisi://` |
| Android | minSdk 24 (Android 7), targetSdk 36 |
| iOS | iOS 15+, yalnızca iPhone, yalnızca dikey |

## 0. Bilgisayarı hazırla (bir kez)

Mac'te:
1. Node.js 22 veya üstü: https://nodejs.org
2. Android Studio (güncel sürüm): https://developer.android.com/studio . İlk açılışta SDK'yı kurmasına izin ver.
3. Xcode (App Store'dan, güncel sürüm). Bir kez açıp ek bileşenleri kur.
4. Proje klasöründe:
   ```
   npm install
   npm run sync
   ```
   `npm run sync` oyunu `www/` içine derler ve Android/iOS projelerine kopyalar. Oyunda (`src/index.html`) her değişiklikten sonra bunu tekrar çalıştır.

**Web sürümü güncellenince:** Oyunun asıl kodu claude.ai'deki web sürümü (`raf-avcisi/index.html`). Onu mobil projeye mağaza eklentileriyle birlikte aktarmak için:
```
python3 scripts/import-web.py ../index.html
npm run sync
```

## 1. Google Play

### 1a. Hesap
PickyList'i yayınladığın Play Console hesabı (MoguzK) yeterli, yeni hesap gerekmez. https://play.google.com/console

> Not: 2023 sonrası açılmış **kişisel** hesaplarda Google, yeni uygulamayı üretime almadan önce **en az 12 test kullanıcısıyla 14 gün kapalı test** istiyor. Play Console uygulama panelinde "Üretime erişim" bölümü bunu sana gösterir. Gerekiyorsa aşağıdaki 1d adımını "Kapalı test" kanalında yap, 14 gün sonra üretime başvur.

### 1b. Yükleme anahtarı oluştur (bir kez, çok önemli)
Terminalde proje klasöründeyken:
```
keytool -genkey -v -keystore raf-avcisi-upload.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```
Şifreleri bir şifre yöneticisine kaydet. Sonra `android/keystore.properties` dosyasını oluştur:
```
storeFile=../../raf-avcisi-upload.jks
storePassword=BURAYA_SIFRE
keyAlias=upload
keyPassword=BURAYA_SIFRE
```
(`storeFile`, `android/app` klasörüne göre yoldur.) `.jks` ve `keystore.properties` dosyaları `.gitignore`'da, GitHub'a gitmez. `.jks` dosyasının bir yedeğini güvenli bir yere koy.

Play App Signing açık olacağı için asıl imza anahtarını Google saklar; bu yükleme anahtarını kaybedersen Play Console'dan sıfırlatabilirsin.

### 1c. AAB derle
```
npm run sync
cd android
./gradlew bundleRelease
```
Çıktı: `android/app/build/outputs/bundle/release/app-release.aab`

Alternatif: `npm run android` ile Android Studio'yu aç → Build › Generate Signed App Bundle.

Önce telefonda denemek için: Android Studio'da telefonu USB ile bağla, yeşil ▶ Run.

### 1d. Play Console'da uygulamayı oluştur
1. **Uygulama oluştur**: ad "Raf Avcısı: Market Bulmacası", dil Türkçe, **Oyun**, **Ücretsiz**.
2. **Kurulum › Uygulama içeriği** bölümündeki her kartı doldur. Cevaplar `store/MAGAZA_METINLERI.md` içinde:
   gizlilik politikası adresi, uygulama erişimi, reklamlar (yok), içerik derecelendirmesi, hedef kitle, veri güvenliği, devlet uygulaması (hayır), finansal özellikler (yok), sağlık (yok).
3. **Mağaza varlığı › Ana mağaza girişi**: kısa/tam açıklama, simge (`store/play-icon-512.png`), öne çıkan grafik (`store/play-feature-graphic-1024x500.png`), telefon ekran görüntüleri (`store/screenshots/android/1-…5-`).
4. **Test › Kapalı test** (ya da doğrudan **Üretim**) → Yeni sürüm → `app-release.aab` yükle → sürüm notu: "İlk sürüm." → İncelemeye gönder.
5. İlk incelemede **Play App Signing**'i kabul et.

## 2. App Store

### 2a. Hesap
Apple Developer Program üyeliği gerekir (yıllık 99 USD): https://developer.apple.com/programs/enroll/ . PickyList App Store'da yoksa bu hesabı yeni açman gerekir; onay 1-2 gün sürebilir.

### 2b. Bundle ID ve uygulama kaydı
1. https://developer.apple.com/account/resources/identifiers → **+** → App IDs → App → Bundle ID: `com.listeal.rafavcisi` (Explicit). Ek yetenek seçme.
2. https://appstoreconnect.apple.com → Uygulamalar → **+** Yeni Uygulama → iOS, ad "Raf Avcısı: Market Bulmacası", birincil dil Türkçe, Bundle ID yukarıdaki, SKU `rafavcisi`.

### 2c. Xcode'da imzala ve yükle
```
npm run ios
```
Xcode açılınca:
1. Sol üstte **App** projesi › **App** hedefi › **Signing & Capabilities**: "Automatically manage signing" açık, **Team** olarak geliştirici hesabını seç. Xcode sertifikayı ve profili kendisi oluşturur.
2. Önce iPhone'u bağlayıp ▶ ile dene.
3. Cihaz olarak **Any iOS Device (arm64)** seç → menü **Product › Archive**.
4. Organizer açılır → **Distribute App** → **App Store Connect** → Upload.
5. Birkaç dakika sonra derleme App Store Connect'te **TestFlight** sekmesinde görünür; istersen önce TestFlight ile kendi telefonunda dene.

### 2d. App Store Connect formları
`store/MAGAZA_METINLERI.md`'deki metinleri gir:
- Uygulama Bilgileri: alt başlık, kategori (Oyunlar › Bulmaca), yaş sınırı anketi (hepsi "Yok" → 4+), gizlilik politikası adresi.
- Uygulama Gizliliği: "Veri toplamıyoruz".
- Sürüm sayfası: tanıtım metni, açıklama, anahtar kelimeler, destek adresi, ekran görüntüleri (`store/screenshots/ios/1-…5-`, 6.9" alanına), derlemeyi seç, inceleme notunu yapıştır.
- **İncelemeye Gönder**.

## 3. Gizlilik politikasını yayınla (iki mağaza da adres ister)
`store/gizlilik.html` dosyasını PickyList'in Firebase Hosting `public/oyun/` klasörüne koy ve `firebase deploy --only hosting` çalıştır. Adres: `https://ailiste.web.app/oyun/gizlilik.html`. Oyunun web sürümü (`index.html`) de aynı klasöre gidebilir (bkz. PICKYLIST_BAGLANTI.md).

## 4. Yayından sonra

- **App Store bağlantısı:** PickyList'in App Store adresi belli olunca `src/index.html` içindeki `APPSTORE_URL` sabitine yaz, `npm run sync`, yeni sürüm çıkar.
- **PickyList'ten oyuna geçiş:** PickyList'in Flutter kodunda önce uygulamayı, yoksa web sürümünü açan buton:
  ```dart
  import 'package:url_launcher/url_launcher.dart';

  Future<void> openRafAvcisi(List<String> unchecked) async {
    final q = {'from': 'pickylist', if (unchecked.isNotEmpty) 'list': unchecked.take(6).join(',')};
    final app = Uri(scheme: 'rafavcisi', host: 'oyun', queryParameters: q);
    final web = Uri.https('ailiste.web.app', '/oyun/', q);
    if (!await launchUrl(app, mode: LaunchMode.externalApplication)) {
      await launchUrl(web, mode: LaunchMode.externalApplication);
    }
  }
  ```
  iOS'ta PickyList'in `Info.plist` dosyasına `LSApplicationQueriesSchemes` altında `rafavcisi` ekle. Android 11+ için PickyList'in `AndroidManifest.xml` dosyasına:
  ```xml
  <queries>
    <intent><action android:name="android.intent.action.VIEW" /><data android:scheme="rafavcisi" /></intent>
  </queries>
  ```
- **Yeni sürüm:** `android/app/build.gradle` içinde `versionCode`'u 1 artır ve `versionName`'i değiştir; Xcode'da General › Version / Build'i artır. Sonra 1c / 2c adımları.

## 5. Göndermeden önce telefonda kontrol listesi
- [ ] Açılış ekranı krem zeminli, simge ve "Raf Avcısı" görünüyor, sonra oyun açılıyor.
- [ ] **iPhone'da ürünler (domates, süt, kahve…) Android'deki Noto görselleriyle çıkıyor.** (Bu bulut ortamında iOS tarayıcısı olmadığı için bunu deneyemedim; boş kare görürsen bana yaz.)
- [ ] Ses ve titreşim çalışıyor, sessiz düğmesi sesi kapatıyor.
- [ ] Uygulama arka plana alınınca süre duruyor.
- [ ] "PickyList" butonu mağaza uygulamasını açıyor.
- [ ] Safari / Chrome adres çubuğuna `rafavcisi://oyun?from=pickylist&list=Domates,Kahve` yazınca oyun açılıyor ve "PickyList'ten hoş geldin" kartı çıkıyor.
- [ ] Uçak modunda oyun açılıyor.

## Klasör yapısı
```
src/              Oyunun kaynağı (index.html) ve native.js (mağaza sürümü eklentileri)
scripts/          www/ derleme betiği (yazı tiplerini gömer)
android/, ios/    Capacitor'ın yerel projeleri
assets/           Simge ve açılış ekranı kaynakları (npm run assets ile tüm boyutlar üretilir)
design/           Simge, açılış ekranı ve ekran görüntülerini üreten dosyalar
store/            Mağaza metinleri, gizlilik politikası, simgeler, ekran görüntüleri
```

## 6. Otomatik derleme (GitHub Actions) — Mac'te Android Studio ve Xcode gerekmez

Depoda üç hazır akış var (GitHub › **Actions** sekmesi):

| Akış | Ne yapar |
| --- | --- |
| **Android imza anahtarı üret (bir kez)** | Google Play yükleme anahtarını rastgele şifreyle üretir, 1 gün indirilebilir dosya olarak verir. |
| **Android (Google Play)** | İmzalı `.aab` dosyasını derler. İstersen Play'e taslak olarak da yükler. |
| **iOS (App Store / TestFlight)** | iPhone uygulamasını derleyip App Store Connect'e yükler; birkaç dakika sonra TestFlight'ta görünür. |

Sürüm numaraları otomatik artar (derleme numarası = akışın çalışma sayısı). `v1.0.1` gibi bir etiket (tag) atınca ikisi birden çalışır.

### Gizli bilgiler (Settings › Secrets and variables › Actions › New repository secret)

**Android**
1. Actions › **Android imza anahtarı üret (bir kez)** › Run workflow.
2. Bitince sayfanın altındaki `android-imza-anahtari` dosyasını indir. İçindeki `SECRETS.txt` hangi secret'a ne yazacağını söyler:
   `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`.
3. `raf-avcisi-upload.jks` dosyasını ve şifreyi bir şifre yöneticisinde sakla. Bu akışı bir daha çalıştırma (her seferinde farklı anahtar üretir).

**iOS** (Apple Developer üyeliği gerekir)
1. App Store Connect › **Kullanıcılar ve Erişim** › **Entegrasyonlar** › **App Store Connect API** › Takım Anahtarları › **+**. Ad: `GitHub`, Erişim: **Admin** (Xcode'un sertifika oluşturabilmesi için gerekli).
2. İnen `AuthKey_XXXX.p8` dosyasını metin düzenleyiciyle aç, tamamını `ASC_KEY_P8` secret'ına yapıştır (BEGIN/END satırları dahil).
3. Aynı sayfadaki **Key ID** → `ASC_KEY_ID`, sayfanın üstündeki **Issuer ID** → `ASC_ISSUER_ID`.
4. https://developer.apple.com/account › Membership details › **Team ID** → `APPLE_TEAM_ID`.
5. Bundle ID'yi (`com.listeal.rafavcisi`) ve App Store Connect'teki uygulama kaydını 2b adımındaki gibi önceden oluştur; yükleme ona gider.

**Play'e otomatik yükleme (isteğe bağlı, sonra da yapılabilir)**
Google ilk `.aab` dosyasını Play Console'a **elle** yüklemeni ister. Sonraki sürümler için Play Console › Kurulum › API erişimi'nden bir hizmet hesabı oluşturup JSON anahtarını `PLAY_SERVICE_ACCOUNT_JSON` secret'ına koyarsan, Android akışını çalıştırırken "play_track" alanına `internal` yazman yeterli.

### Akışı çalıştırmak
Actions › akışı seç › **Run workflow** › sürüm adını yaz (ör. `1.0`) › Run. Android'de bitince sayfanın altından `.aab` dosyasını indirip Play Console'a yükle. iOS'ta dosya doğrudan App Store Connect'e gider.


## 7. Reklam ve satın alma (ödüllü reklam, Yardım paketi, Premium)

Oyunda şunlar var (yalnızca mağaza sürümünde, web sürümünde yok):
- Bir yardım (Geri al / İpucu / Karıştır) bitince Mağaza açılır: **Reklam izle: +1** ya da Yardım paketi / Premium.
- Süre bitince, her reyonda bir kez: **Reklam izle: +30 saniye**.
- Premium alan reklam izlemeden bu ödülleri alır, bir kez 10'ar yardım kazanır.
- Avrupa'da ilk açılışta Google'ın izin formu çıkar; Mağaza ekranında "Gizlilik ayarları" ve "Satın alımları geri yükle" var.

Şu an kodda **Google'ın test reklam kimlikleri** var: reklamlar çalışır ama para kazandırmaz. Gerçek kimlikleri bana verince değiştiririm.

### 7a. AdMob (bir kez)
1. https://admob.google.com → PickyList'in Google hesabıyla giriş → hesap ve ödeme bilgilerini doldur.
2. **Uygulamalar › Uygulama ekle** → Android → "Uygulama mağazada yayında mı?" sorusuna, Play'de yayına girdiyse Evet deyip Raf Avcısı'nı seç, girmediyse Hayır (sonra bağlarsın). Aynısını iOS için de yap.
3. Her uygulamada **Reklam birimi ekle › Ödüllü** (Rewarded) → ad: "Yardim odulu". Ödül ayarı önemli değil (oyun kendisi veriyor).
4. Bana şu 4 değeri gönder (gizli değiller):
   - Android uygulama kimliği `ca-app-pub-…~…` ve ödüllü reklam birimi `ca-app-pub-…/…`
   - iOS uygulama kimliği ve ödüllü reklam birimi
5. **Gizlilik ve mesajlaşma › Avrupa düzenlemeleri** → yeni mesaj oluştur, iki uygulamayı seç, yayınla. (Bu olmadan Avrupa'da izin formu çıkmaz ve reklam gösterilemez.)
6. **app-ads.txt:** AdMob'un verdiği satırı `https://ailiste.web.app/app-ads.txt` adresine koy (gizlilik sayfasıyla aynı Firebase Hosting, `public/app-ads.txt`). Play ve App Store'daki "web sitesi" alanına `https://ailiste.web.app` yaz.

### 7b. Play Console satın almaları
1. **Kurulum › Ödeme profili**: banka/vergi bilgileri (satış yapabilmek için şart).
2. Reklamlı sürümün AAB'sini önce **Kapalı test**e yükle (ürün oluşturma, faturalandırma izni olan bir AAB yüklenince açılır).
3. **Para kazanma › Ürünler › Uygulama içi ürünler** → `yardim_paketi_5` ve `premium` oluştur, fiyatları gir, **Etkinleştir**. Ad/açıklamalar `store/MAGAZA_METINLERI.md` sonunda.
4. **Ayarlar › Lisans testi**: kendi Gmail'ini ekle; test kanalından kurduğunda satın almalar ücretsiz denenir.

### 7c. App Store Connect satın almaları
1. **Sözleşmeler, Vergi ve Bankacılık** → Ücretli Uygulamalar sözleşmesini imzala, banka/vergi bilgilerini gir.
2. Uygulama › **Uygulama İçi Satın Almalar** → `yardim_paketi_5` (Tüketilebilir) ve `premium` (Tüketilemez) oluştur, fiyat ve en az bir dilde ad/açıklama, inceleme ekran görüntüsü (Mağaza ekranı) ekle.
3. İlk sürümle birlikte incelemeye gönder.

### 7d. Formlar
Reklamlı sürümü yüklediğin gün: Play'de "Reklam içeriyor: Evet", veri güvenliği formu ve içerik derecelendirmesindeki "dijital satın alma" sorusu değişir. App Store'da Uygulama Gizliliği değişir. Cevaplar `store/MAGAZA_METINLERI.md`'nin sonunda. Güncel gizlilik politikasını (`store/gizlilik.html`) yayınlamayı unutma.
