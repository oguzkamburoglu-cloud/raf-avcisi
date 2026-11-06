const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");
(async () => {
  const root = path.resolve(__dirname, "..");
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 2732, height: 2732 } });
  await pg.goto("http://127.0.0.1:8765/design/splash.html"); // serve the project root first: python3 -m http.server 8765 await pg.evaluate(async () => { await document.fonts.load('900 150px Fraunces', "Raf Avcısı"); await document.fonts.load('700 72px Roboto', "PickyList"); });
  await pg.waitForTimeout(800);
  await pg.locator("#c").screenshot({ path: path.join(root, "assets/splash.png") });
  await pg.locator("#c").screenshot({ path: path.join(root, "assets/splash-dark.png") });
  await b.close();
})();
