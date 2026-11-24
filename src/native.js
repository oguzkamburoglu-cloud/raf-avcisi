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
  // Amazon Appstore build (scripts/amazon-prep.mjs sets RAF_STORE): Amazon IAP instead of Google Play
  // Billing, no Play Games, and no links to Google Play (Amazon does not allow them).
  var amazon = window.RAF_STORE === "amazon";
  // PickyList's Amazon Appstore page; empty = the PickyList store links are hidden in the Amazon build
  var PICKYLIST_AMAZON_URL = "";
  if (amazon) {
    var css = document.createElement("style");
    css.textContent = "#boardCard .lbnote{display:none!important}" +
      (PICKYLIST_AMAZON_URL ? "" : ".plband,.plcta,.applink{display:none!important}");
    document.head.appendChild(css);
  }

  window.RAF_NATIVE = {
    platform: platform,
    store: amazon ? "amazon" : (platform === "ios" ? "appstore" : "play"),
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

  // Leaderboards: Game Center on iOS, Google Play Games on Android (plugins/game-services).
  // ready() turns true once the platform says it can be used; the game then shows the
  // world ranking buttons, otherwise only the player's own records.
  var G = P.RafGameServices;
  if (G) {
    var gReady = platform === "ios", gAuth = false;
    var signIn = function (interactive) {
      return G.signIn({ interactive: !!interactive })
        .then(function (r) { gAuth = !!(r && r.authenticated); return gAuth; })
        .catch(function () { return false; });
    };
    window.RAF_GAMES = {
      platform: platform,
      ready: function () { return gReady; },
      submit: function (board, score) {
        if (!gReady || !gAuth) return;
        G.submitScore({ leaderboard: board, score: Math.round(score) }).catch(function () {});
      },
      show: function (board) {
        if (!gReady) return;
        (gAuth ? Promise.resolve(true) : signIn(true)).then(function (ok) {
          if (ok) G.showLeaderboard({ leaderboard: board }).catch(function () {});
        });
      }
    };
    G.available().then(function (r) {
      gReady = !!(r && r.available);
      if (gReady) setTimeout(function () { signIn(false); }, 1500);
    }).catch(function () { gReady = false; });
  }

  // v19: local reminders (at most one a day: daily wheel tomorrow 19:00, aisle reminder in 3 days).
  // The game asks for permission after the third aisle and reschedules each time it goes to the background.
  var LN = P.LocalNotifications;
  if (LN) {
    window.RAF_NOTIFY = {
      ask: function () { return LN.requestPermissions().catch(function () {}); },
      clear: function () { return LN.cancel({ notifications: [{ id: 1 }, { id: 2 }] }).catch(function () {}); },
      schedule: function (list) {
        LN.checkPermissions().then(function (p) {
          if (!p || p.display !== "granted") return;
          return window.RAF_NOTIFY.clear().then(function () {
            return LN.schedule({ notifications: list.map(function (n) {
              return { id: n.id, title: n.title, body: n.body, schedule: { at: new Date(n.at), allowWhileIdle: false }, smallIcon: "ic_stat_notify", iconColor: "#1F9D55" };
            }) });
          });
        }).catch(function () {});
      }
    };
  }

  // v19: analytics bridge. Events go to Firebase Analytics once its plugin and config files are in the app;
  // until then the game only counts them on the device.
  var FA = P.FirebaseAnalytics;
  if (FA) {
    window.RAF_ANALYTICS = {
      log: function (name, params) { FA.logEvent({ name: name, params: params || {} }).catch(function () {}); }
    };
  }

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
    var href = a.href;
    if (amazon && /play\.google\.com|apps\.apple\.com/.test(href)) {
      if (!PICKYLIST_AMAZON_URL) return;
      href = PICKYLIST_AMAZON_URL;
    }
    window.location.href = href;
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
  var PRODUCT_IDS = { pack: "yardim_paketi_5", premium: "premium", starter: "baslangic_paketi", coins1: "para_1200", coins2: "para_3500" };

  var AdMob = P.AdMob, IAP = amazon ? P.AmazonIap : P.NativePurchases;
  var adReady = false, adLoading = false, canAds = false, privacyReq = false;
  var prices = {};
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  var premium = lsGet("raf_premium") === "1";

  // v32: an ad that is not loaded yet no longer makes the button do nothing. The tap starts loading
  // and waits up to AD_WAIT ms with a small spinner; a consent error no longer blocks ads for good.
  var AD_WAIT = 9000, adWaiters = [], adStarted = false;
  function adSettled(ok) {
    var w = adWaiters; adWaiters = [];
    w.forEach(function (f) { f(ok); });
  }
  function loadAd() {
    if (!AdMob || !canAds || adReady || adLoading) return;
    adLoading = true;
    AdMob.prepareRewardVideoAd({ adId: AD_UNITS[platform], isTesting: ADS_TEST })
      .then(function () { adReady = true; lsSet("raf_ad_err", ""); })
      .catch(function (e) {
        adReady = false;
        // keep the reason (e.g. code 1 = no ad to show) so it can be read from the settings screen
        lsSet("raf_ad_err", String((e && (e.code || e.message)) || "?"));
        setTimeout(loadAd, 30000);
      })
      .then(function () { adLoading = false; adSettled(adReady); });
  }
  function initAds() {
    if (adStarted) return Promise.resolve();
    adStarted = true; canAds = true;
    return AdMob.initialize({ initializeForTesting: ADS_TEST }).then(loadAd).catch(function () { adStarted = false; });
  }
  function startAds() {
    if (!AdMob) return;
    AdMob.requestConsentInfo()
      .then(function (info) {
        if (info.isConsentFormAvailable && info.status === "REQUIRED") {
          return AdMob.showConsentForm().catch(function () { return info; });
        }
        return info;
      })
      .then(function (info) {
        privacyReq = info.privacyOptionsRequirementStatus === "REQUIRED";
        if (info.canRequestAds) return initAds();
      })
      // consent info could not be read (offline, no privacy message set up): still start the SDK;
      // outside the EEA/UK no consent is needed, inside it Google serves limited ads only
      .catch(function () { return initAds(); });
  }
  function waitForAd() {
    return new Promise(function (resolve) {
      if (adReady) { resolve(true); return; }
      if (!AdMob || !canAds) { if (AdMob && !adStarted) startAds(); }
      var spin = document.createElement("div");
      spin.setAttribute("aria-hidden", "true");
      spin.style.cssText = "position:fixed;inset:0;z-index:99;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.25);font-size:44px";
      spin.innerHTML = '<span style="background:#fff;border-radius:22px;padding:14px 18px;box-shadow:0 6px 18px rgba(0,0,0,.2)">🎬 <span style="display:inline-block;animation:rafspin 1s linear infinite">⏳</span></span><style>@keyframes rafspin{to{transform:rotate(360deg)}}</style>';
      document.body.appendChild(spin);
      var done = false;
      function fin(ok) { if (done) return; done = true; spin.remove(); resolve(ok); }
      adWaiters.push(fin);
      setTimeout(function () { fin(adReady); }, AD_WAIT);
      loadAd();
    });
  }
  function showRewarded() {
    return new Promise(function (resolve) {
      if (premium) { resolve(true); return; }
      if (!AdMob) { resolve(false); return; }
      waitForAd().then(function (ready) {
        if (!ready) { resolve(false); return; }
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
        AdMob.showRewardVideoAd().catch(function () { adReady = false; finish(got); });
      });
    });
  }

  function setPremium() { premium = true; lsSet("raf_premium", "1"); }
  function loadProducts() {
    if (!IAP) return;
    IAP.getProducts({ productIdentifiers: Object.keys(PRODUCT_IDS).map(function (k) { return PRODUCT_IDS[k]; }), productType: "inapp" })
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
      isConsumable: kind !== "premium"   // packs and coins can be bought again; Premium is bought once
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
    privacyForm: function () { if (AdMob) AdMob.showPrivacyOptionsForm().catch(function () {}); },
    adError: function () { return lsGet("raf_ad_err") || ""; }
  };
  startAds();
  loadProducts();
  checkPremium();

  // Hide the native splash once the first frame is drawn
  window.addEventListener("load", function () {
    // the splash background is the intro's sky gradient, so a slow fade hands over smoothly
    if (P.SplashScreen) setTimeout(function () { P.SplashScreen.hide({ fadeOutDuration: 450 }); }, 150);
  });
})();
