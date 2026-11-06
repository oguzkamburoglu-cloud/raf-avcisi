// Play feature graphic (1024x500) + 512px store icon. Serve project root on :8765 first.
const { chromium } = require("playwright"); const path = require("path");
(async () => { const root = path.resolve(__dirname, ".."); const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1024, height: 500 } });
  await pg.goto("http://127.0.0.1:8765/design/feature.html"); await pg.evaluate(() => document.fonts.ready); await pg.waitForTimeout(500);
  await pg.locator("#f").screenshot({ path: path.join(root, "store/play-feature-graphic-1024x500.png") });
  await b.close();
  const sharp = null; })();
