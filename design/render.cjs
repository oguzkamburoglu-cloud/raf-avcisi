// Renders app icon PNGs from design/icon.html (run: NODE_PATH=<global node_modules> node design/render.cjs)
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");
(async () => {
  const root = path.resolve(__dirname, "..");
  const html = fs.readFileSync(path.join(__dirname, "icon.html"), "utf8")
    .replace('href="../www/fonts/fonts.css"', `href="file://${root}/www/fonts/fonts.css"`);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1024, height: 1024 } });
  async function shot(opts, out, transparent) {
    await pg.setContent(html.replace("<script>", `<script>window.OPTS=${JSON.stringify(opts)};`));
    await pg.evaluate(async () => { await document.fonts.load('190px "Noto Color Emoji"', "🍅"); await document.fonts.ready; });
    await pg.waitForTimeout(800);
    await pg.locator("#c").screenshot({ path: path.join(root, out), omitBackground: transparent });
  }
  await shot({ bg: 1, scale: 1 }, "assets/icon-only.png", false);
  await shot({ bg: 0, scale: 0.78 }, "assets/icon-foreground.png", true);
  await b.close();
})();
