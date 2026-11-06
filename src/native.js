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

  // Hide the native splash once the first frame is drawn
  window.addEventListener("load", function () {
    if (P.SplashScreen) setTimeout(function () { P.SplashScreen.hide(); }, 250);
  });
})();
