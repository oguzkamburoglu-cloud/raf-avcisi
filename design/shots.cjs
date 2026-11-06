// Store screenshots: serves www/ (python3 -m http.server 8765 from project root), drives the game into
// five states and writes raw + captioned PNGs to store/screenshots/{ios,android}/.
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");
const root = path.resolve(__dirname, "..");
const BASE = "http://127.0.0.1:8765";

// test copy of the game that exposes its internal state
const src = fs.readFileSync(path.join(root, "www/index.html"), "utf8");
const hook = 'window.__g={get S(){return S},render,win,front,newGame,flashCombo,stop(){clearInterval(timerId)}};\n})();\n</script>';
const i = src.lastIndexOf("})();\n</script>");
fs.writeFileSync(path.join(root, "www/_shots.html"), src.slice(0, i) + hook + src.slice(i + "})();\n</script>".length));

const DEVICES = {
  ios: { w: 440, h: 956, dpr: 3, out: [1320, 2868] },      // iPhone 6.9"
  android: { w: 360, h: 640, dpr: 3, out: [1080, 1920] }   // Play phone 9:16
};
const CAPTIONS = [
  ["start", "Market raflarında<br>üçlüleri yakala", "PickyList'in bulmaca oyunu"],
  ["play", "Alışveriş listeni<br>raf raf tamamla", "Aynı üç ürünü bir rafa diz"],
  ["level", "Her reyon yeni<br>bir bulmaca", "Arka sıradakiler öne gelir"],
  ["win", "Fişini al,<br>yıldızları topla", "Süre bonusu ve kombo puanları"],
  ["bonus", "PickyList listen<br>oyuna gelsin", "Her gün +30 sn ve 2x puan"]
];

async function state(pg, name) {
  const q = name === "bonus" ? "?from=pickylist&list=Domates,K%C4%B1yma,Kahve,S%C3%BCt" : "";
  await pg.goto(`${BASE}/www/_shots.html${q}`);
  await pg.evaluate(() => { localStorage.clear(); ["tutDone","tip_basket","tip_sale","tip_box"].forEach(k => localStorage.setItem("raf_" + k, "true")); });
  await pg.goto(`${BASE}/www/_shots.html${q}`);
  await pg.evaluate(async () => { await document.fonts.ready; });
  await pg.waitForTimeout(600);
  if (name === "start" || name === "bonus") { await pg.addStyleTag({ content: "#toast{display:none!important}" }); return; }
  await pg.evaluate((name) => {
    const g = window.__g;
    document.getElementById("ovStart").hidden = true;
    g.newGame(name === "level" ? 6 : name === "win" ? 3 : 2); g.stop();
    const S = g.S;
    if (name === "play") {
      S.list[0].done = true; S.score = 450; S.time = 71;
      // select an item that has a pair somewhere
      for (let si = 0; si < S.shelves.length; si++) { const k = g.front(si).findIndex(x => x != null); if (k >= 0) { S.sel = [si, k]; break; } }
      g.render();
    }
    if (name === "level") { S.list[0].done = true; S.list[1].done = true; S.score = 2350; S.time = 104; S.combo = 2; g.render(); g.flashCombo("Kombo x2"); }
    if (name === "win") { S.list.forEach(x => x.done = true); S.score = 1280; S.time = 58; S.clears = 6; S.moves = 21; g.win(); }
  }, name);
  await pg.waitForTimeout(name === "level" ? 250 : 500);
  await pg.addStyleTag({ content: "#toast{display:none!important}" });
}

(async () => {
  const b = await chromium.launch();
  for (const [dev, d] of Object.entries(DEVICES)) {
    const dir = path.join(root, "store/screenshots", dev); fs.mkdirSync(dir, { recursive: true });
    const ctx = await b.newContext({ viewport: { width: d.w, height: d.h }, deviceScaleFactor: d.dpr, isMobile: true, hasTouch: true,
      userAgent: "Mozilla/5.0 (Linux; Android 15) RafAvcisiScreens" /* chromium cannot draw the iOS (SVG) emoji font; system Noto looks the same */ });
    const pg = await ctx.newPage();
    const raws = [];
    for (const [n, , ] of CAPTIONS) {
      await state(pg, n);
      const f = path.join(dir, `raw-${n}.png`); await pg.screenshot({ path: f }); raws.push(f);
    }
    // captioned versions
    const fp = await b.newPage({ viewport: { width: d.out[0], height: d.out[1] }, deviceScaleFactor: 1 });
    for (let k = 0; k < CAPTIONS.length; k++) {
      const [n, title, sub] = CAPTIONS[k];
      await fp.goto(`${BASE}/design/frame.html?img=${encodeURIComponent("/store/screenshots/" + dev + "/raw-" + n + ".png")}&t=${encodeURIComponent(title)}&s=${encodeURIComponent(sub)}&w=${d.out[0]}&h=${d.out[1]}`);
      await fp.evaluate(async () => { await document.fonts.ready; await new Promise(r => { const im = document.querySelector("img"); im.complete ? r() : im.onload = r; }); });
      await fp.waitForTimeout(200);
      await fp.screenshot({ path: path.join(dir, `${k + 1}-${n}.png`) });
    }
    await ctx.close(); await fp.close();
  }
  fs.unlinkSync(path.join(root, "www/_shots.html"));
  await b.close();
})();
