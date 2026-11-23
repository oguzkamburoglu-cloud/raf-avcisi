# amazon-iap (yalnızca Amazon Appstore derlemesi)

Amazon Appstore SDK ile satın alma. Bu modül npm bağımlılığı **değildir**; Google Play ve
iOS derlemelerine girmez. `scripts/amazon-prep.mjs` (Actions › Android (Amazon Appstore))
`npx cap sync android` sonrasında onu projeye ekler, Play Billing (`@capgo/native-purchases`)
ve Play Games (`raf-game-services`) modüllerini çıkarır.

JS tarafı (`src/native.js`) `Capacitor.Plugins.AmazonIap`'ı `NativePurchases` ile aynı
yöntem adlarıyla kullanır: `getProducts`, `getPurchases`, `purchaseProduct`, `restorePurchases`.
