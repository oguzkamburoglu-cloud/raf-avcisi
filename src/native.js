/* Raf Avcısı - native bridge (Capacitor). The game itself stays plain web code;
   this file only adds what the store apps need. In a normal browser it does nothing. */
(function () {
  var C = window.Capacitor;
  var isNative = !!(C && C.isNativePlatform && C.isNativePlatform());
  var ua = navigator.userAgent;
  if ((isNative && C.getPlatform() === "ios") || (!isNative && /iPhone|iPad|iPod/.test(ua))) {
    document.documentElement.classList.add("ios");
  }
  if (!isNative) return;
  var P = C.Plugins || {};
  var platform = C.getPlatform();

  window.RAF_NATIVE = {
    platform: platform,
    // kind is the game's vibration pattern: 25 = shelf cleared, 40 = wrong move,
    // [30,40,30] = level won, 120 = time up (or the names clear/bad/win/lose)
    haptic: function (kind) {
      if (!P.Haptics) return;
      if (kind === "clear" || kind === 25) P.Haptics.impact({ style: "MEDIUM" });
      else if (kind === "win" || Array.isArray(kind)) P.Haptics.notification({ type: "SUCCESS" });
      else if (kind === "bad" || kind === 40) P.Haptics.notification({ type: "WARNING" });
      else if (kind === "lose" || kind === 120) P.Haptics.notification({ type: "ERROR" });
      else P.Haptics.impact({ style: "LIGHT" });
    }
  };

  // Status bar: dark icons on the cream/white game background
  if (P.StatusBar) {
    try { P.StatusBar.setStyle({ style: "LIGHT" }); } catch (e) {}
  }

  // Store links (PickyList on Google Play / App Store) open outside the game.
  // Navigating to an external https URL makes Capacitor hand it to the OS,
  // which opens the Play Store / App Store app.
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href^='http']");
    if (!a) return;
    e.preventDefault();
    window.location.href = a.href;
  }, true);

  // PickyList opens the game with:  rafavcisi://oyun?from=pickylist&list=Domates,Kıyma
  // The game reads ?from= / ?list= on start, so reload the page with that query.
  function applyLink(url) {
    if (!url) return;
    try {
      var q = url.indexOf("?") >= 0 ? url.slice(url.indexOf("?")) : "";
      var h = url.indexOf("#") >= 0 ? url.slice(url.indexOf("#")) : "";
      if (q.indexOf("#") >= 0) q = q.slice(0, q.indexOf("#"));
      if (!q && !h) return;
      if (location.search === q && location.hash === h) return;
      location.replace(location.pathname + q + h);
    } catch (e) {}
  }
  if (P.App) {
    // app to background / foreground: pause the game and its music
    P.App.addListener("pause", function () { window.RAF_ONPAUSE && window.RAF_ONPAUSE(); });
    P.App.addListener("resume", function () { window.RAF_ONRESUME && window.RAF_ONRESUME(); });
    P.App.addListener("appUrlOpen", function (ev) { applyLink(ev && ev.url); });
    if (!location.search && !location.hash) {
      P.App.getLaunchUrl().then(function (r) { applyLink(r && r.url); }).catch(function () {});
    }
  }

  /* ---------- Shop: rewarded ads (AdMob) and in-app purchases ----------
     The game calls window.RAF_SHOP; without it (in a browser) the shop is hidden.
     AD_UNITS are Google's public TEST ids until the real AdMob ids are filled in
     (see MAGAZA_REHBERI.md, "Reklam ve satın alma"). Test ads earn nothing. */
  var AD_UNITS = {
    android: "ca-app-pub-2461120295843731/2415832110",
    ios: "ca-app-pub-2461120295843731/4129415219"
  };
  var ADS_TEST = AD_UNITS[platform].indexOf("3940256099942544") >= 0;
  // Product ids: create the same ids in Play Console and App Store Connect
  var PRODUCT_IDS = { pack: "yardim_paketi_5", premium: "premium" };

  var AdMob = P.AdMob, IAP = P.NativePurchases;
  var adReady = false, adLoading = false, canAds = false, privacyReq = false;
  var prices = {};
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var premium = lsGet("raf_premium") === "1";

  function loadAd() {
    if (!AdMob || !canAds || adReady || adLoading) return;
    adLoading = true;
    AdMob.prepareRewardVideoAd({ adId: AD_UNITS[platform], isTesting: ADS_TEST })
      .then(function () { adReady = true; })
      .catch(function () { adReady = false; setTimeout(loadAd, 30000); })
      .then(function () { adLoading = false; });
  }
  function startAds() {
    if (!AdMob) return;
    AdMob.requestConsentInfo()
      .then(function (info) {
        if (info.isConsentFormAvailable && info.status === "REQUIRED") return AdMob.showConsentForm();
        return info;
      })
      .then(function (info) {
        privacyReq = info.privacyOptionsRequirementStatus === "REQUIRED";
        canAds = !!info.canRequestAds;
        if (canAds) return AdMob.initialize({ initializeForTesting: ADS_TEST }).then(loadAd);
      })
      .catch(function () {});
  }
  function showRewarded() {
    return new Promise(function (resolve) {
      if (premium) { resolve(true); return; }
      if (!AdMob || !adReady) { loadAd(); resolve(false); return; }
      var got = false, done = false, hs = [];
      function finish(ok) {
        if (done) return; done = true;
        hs.forEach(function (h) { Promise.resolve(h).then(function (x) { x && x.remove(); }); });
        adReady = false; loadAd();
        if (window.RAF_ONRESUME) window.RAF_ONRESUME();
        resolve(ok);
      }
      hs.push(AdMob.addListener("onRewardedVideoAdReward", function () { got = true; }));
      hs.push(AdMob.addListener("onRewardedVideoAdDismissed", function () { finish(got); }));
      hs.push(AdMob.addListener("onRewardedVideoAdFailedToShow", function () { finish(false); }));
      AdMob.showRewardVideoAd().catch(function () { finish(got); });
    });
  }

  function setPremium() { premium = true; lsSet("raf_premium", "1"); }
  function loadProducts() {
    if (!IAP) return;
    IAP.getProducts({ productIdentifiers: [PRODUCT_IDS.pack, PRODUCT_IDS.premium], productType: "inapp" })
      .then(function (r) {
        (r.products || []).forEach(function (p) {
          Object.keys(PRODUCT_IDS).forEach(function (k) { if (PRODUCT_IDS[k] === p.identifier) prices[k] = p.priceString; });
        });
      })
      .catch(function () {});
  }
  function checkPremium() {
    if (!IAP) return Promise.resolve();
    return IAP.getPurchases({ productType: "inapp" })
      .then(function (r) {
        (r.purchases || []).forEach(function (t) { if (t.productIdentifier === PRODUCT_IDS.premium) setPremium(); });
      })
      .catch(function () {});
  }
  function buy(kind) {
    if (!IAP || !PRODUCT_IDS[kind]) return Promise.resolve(false);
    return IAP.purchaseProduct({
      productIdentifier: PRODUCT_IDS[kind], productType: "inapp", quantity: 1,
      isConsumable: kind === "pack"   // the pack can be bought again; Premium is bought once
    })
      .then(function () { if (kind === "premium") setPremium(); return true; })
      .catch(function () { return false; });
  }

  window.RAF_SHOP = {
    premium: function () { return premium; },
    price: function (kind) { return prices[kind] || ""; },
    rewarded: showRewarded,
    buy: buy,
    restore: function () { return (IAP ? IAP.restorePurchases().catch(function () {}) : Promise.resolve()).then(checkPremium); },
    privacyRequired: function () { return privacyReq; },
    privacyForm: function () { if (AdMob) AdMob.showPrivacyOptionsForm().catch(function () {}); }
  };
  startAds();
  loadProducts();
  checkPremium();

  // Hide the native splash once the first frame is drawn
  window.addEventListener("load", function () {
    if (P.SplashScreen) setTimeout(function () { P.SplashScreen.hide(); }, 250);
  });
})();
