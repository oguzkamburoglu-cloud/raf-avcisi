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
// captions per store language: [title (use <br> for the line break), subtitle]
const LANGS = {
  tr: [["Market raflarında<br>üçlüleri yakala", "PickyList'in bulmaca oyunu"], ["Alışveriş listeni<br>raf raf tamamla", "Aynı üç ürünü bir rafa diz"], ["Her reyon yeni<br>bir bulmaca", "Arka sıradakiler öne gelir"], ["Fişini al,<br>yıldızları topla", "Süre bonusu ve kombo puanları"], ["PickyList listen<br>oyuna gelsin", "Her gün +30 sn ve 2x puan"], "Kombo x2"],
  en: [["Match three on<br>grocery shelves", "The puzzle game from PickyList"], ["Finish your list<br>shelf by shelf", "Put three of a kind on one shelf"], ["Every aisle is<br>a new puzzle", "The back row moves forward"], ["Get your receipt,<br>collect stars", "Time bonus and combo points"], ["Bring your PickyList<br>into the game", "+30 s and 2x points every day"], "Combo x2"],
  de: [["Drei Gleiche<br>im Supermarktregal", "Das Puzzlespiel von PickyList"], ["Erledige deine Liste<br>Regal für Regal", "Drei gleiche Produkte in ein Regal"], ["Jeder Gang ist<br>ein neues Rätsel", "Die hintere Reihe rückt nach"], ["Hol dir den Bon,<br>sammle Sterne", "Zeitbonus und Kombopunkte"], ["Deine PickyList<br>kommt ins Spiel", "Täglich +30 s und doppelte Punkte"], "Kombo x2"],
  es: [["Junta tres iguales<br>en el súper", "El juego de puzles de PickyList"], ["Completa tu lista<br>estante a estante", "Tres productos iguales en un estante"], ["Cada pasillo es<br>un puzle nuevo", "La fila de atrás avanza"], ["Llévate el ticket<br>y las estrellas", "Bonus de tiempo y puntos de combo"], ["Tu lista de PickyList<br>llega al juego", "+30 s y puntos x2 cada día"], "Combo x2"],
  fr: [["Aligne trois produits<br>en rayon", "Le jeu de puzzle de PickyList"], ["Finis ta liste<br>rayon par rayon", "Trois produits identiques par étagère"], ["Chaque rayon est<br>un nouveau puzzle", "La rangée de derrière avance"], ["Prends ton ticket,<br>gagne des étoiles", "Bonus de temps et points de combo"], ["Ta liste PickyList<br>arrive dans le jeu", "+30 s et points x2 chaque jour"], "Combo x2"],
  pt: [["Junte três iguais<br>no mercado", "O jogo de quebra-cabeça do PickyList"], ["Complete sua lista<br>prateleira a prateleira", "Três produtos iguais numa prateleira"], ["Cada corredor é<br>um novo desafio", "A fileira de trás vem para a frente"], ["Pegue o cupom,<br>junte estrelas", "Bônus de tempo e pontos de combo"], ["Sua lista do PickyList<br>vem para o jogo", "+30 s e pontos 2x todo dia"], "Combo x2"],
  ru: [["Собирай по три<br>на полках магазина", "Головоломка от PickyList"], ["Закрой список<br>полка за полкой", "Три одинаковых товара на полку"], ["Каждый отдел —<br>новая головоломка", "Задний ряд выходит вперёд"], ["Получи чек,<br>собери звёзды", "Бонус за время и комбо-очки"], ["Твой список PickyList<br>в игре", "+30 с и очки x2 каждый день"], "Комбо x2"]
};
const STATES = ["start", "play", "level", "win", "bonus"];

async function state(pg, name, lang, combo) {
  const q = (name === "bonus" ? "?from=pickylist&list=Domates,K%C4%B1yma,Kahve,S%C3%BCt&" : "?") + "lang=" + lang;
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
    if (name === "level") { S.list[0].done = true; S.list[1].done = true; S.score = 2350; S.time = 104; S.combo = 2; g.render(); }
    if (name === "win") { S.list.forEach(x => x.done = true); S.score = 1280; S.time = 58; S.clears = 6; S.moves = 21; g.win(); }
  }, name);
  if (name === "level") await pg.evaluate((c) => window.__g.flashCombo(c), combo);
  await pg.waitForTimeout(name === "level" ? 250 : 500);
  await pg.addStyleTag({ content: "#toast{display:none!important}" });
}


(async () => {
  const b = await chromium.launch();
  const only = process.argv[2] ? process.argv[2].split(",") : Object.keys(LANGS);
  for (const lang of only) {
    const [c1, c2, c3, c4, c5, combo] = LANGS[lang];
    const CAPTIONS = [c1, c2, c3, c4, c5];
    for (const [dev, d] of Object.entries(DEVICES)) {
      const dir = path.join(root, "store/screenshots", lang, dev); fs.mkdirSync(dir, { recursive: true });
      const ctx = await b.newContext({ viewport: { width: d.w, height: d.h }, deviceScaleFactor: d.dpr, isMobile: true, hasTouch: true, locale: lang,
        userAgent: "Mozilla/5.0 (Linux; Android 15) RafAvcisiScreens" /* chromium cannot draw the iOS (SVG) emoji font; system Noto looks the same */ });
      const pg = await ctx.newPage();
      for (const n of STATES) {
        await state(pg, n, lang, combo);
        await pg.screenshot({ path: path.join(dir, `raw-${n}.png`) });
      }
      const fp = await b.newPage({ viewport: { width: d.out[0], height: d.out[1] }, deviceScaleFactor: 1 });
      for (let k = 0; k < STATES.length; k++) {
        const n = STATES[k], [title, sub] = CAPTIONS[k];
        await fp.goto(`${BASE}/design/frame.html?img=${encodeURIComponent("/store/screenshots/" + lang + "/" + dev + "/raw-" + n + ".png")}&t=${encodeURIComponent(title)}&s=${encodeURIComponent(sub)}&w=${d.out[0]}&h=${d.out[1]}`);
        await fp.evaluate(async () => { await document.fonts.ready; await new Promise(r => { const im = document.querySelector("img"); im.complete ? r() : im.onload = r; }); });
        await fp.waitForTimeout(250);
        await fp.screenshot({ path: path.join(dir, `${k + 1}-${n}.png`) });
      }
      await ctx.close(); await fp.close();
    }
    console.log(lang, "ok");
  }
  fs.unlinkSync(path.join(root, "www/_shots.html"));
  await b.close();
})();
