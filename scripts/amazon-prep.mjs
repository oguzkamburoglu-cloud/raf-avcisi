// Turns the synced Android project into the Amazon Appstore build. Run after `npx cap sync android`
// (Actions › Android (Amazon Appstore) does this). Never commit the result: the next `cap sync`
// regenerates these files for Google Play.
//  - removes Google Play Billing (@capgo/native-purchases) and Play Games (raf-game-services)
//  - adds plugins/amazon-iap (Amazon Appstore SDK in-app purchases)
//  - copies the app's Amazon public key (env AMAZON_PUBLIC_KEY_PEM) to assets/AppstoreAuthenticationKey.pem
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const android = path.join(root, "android");
const DROP = ["capgo-native-purchases", "raf-game-services"];
const DROP_PKG = ["@capgo/native-purchases", "raf-game-services"];

function edit(file, fn) {
  const p = path.join(android, file);
  const before = fs.readFileSync(p, "utf8");
  const after = fn(before);
  fs.writeFileSync(p, after);
}

edit("capacitor.settings.gradle", (s) =>
  s.includes("':raf-amazon-iap'") ? s :
  s.trimEnd() + "\n\ninclude ':raf-amazon-iap'\nproject(':raf-amazon-iap').projectDir = new File('../plugins/amazon-iap/android')\n");

edit("app/capacitor.build.gradle", (s) => {
  for (const d of DROP) {
    const line = `    implementation project(':${d}')\n`;
    if (!s.includes(line)) throw new Error(`capacitor.build.gradle: ${d} satırı bulunamadı`);
    s = s.replace(line, "");
  }
  if (!s.includes("':raf-amazon-iap'")) {
    s = s.replace("dependencies {\n", "dependencies {\n    implementation project(':raf-amazon-iap')\n");
  }
  return s;
});

edit("app/src/main/assets/capacitor.plugins.json", (s) => {
  let list = JSON.parse(s).filter((p) => !DROP_PKG.includes(p.pkg));
  if (!list.some((p) => p.pkg === "raf-amazon-iap")) {
    list.push({ pkg: "raf-amazon-iap", classpath: "com.listeal.rafavcisi.amazon.AmazonIapPlugin" });
  }
  return JSON.stringify(list, null, "\t") + "\n";
});

// the bundled web game learns it is the Amazon build (store links, no Play Games text)
edit("app/src/main/assets/public/native.js", (s) => "window.RAF_STORE=\"amazon\";\n" + s);

const pem = process.env.AMAZON_PUBLIC_KEY_PEM || "";
const pemOut = path.join(android, "app/src/main/assets/AppstoreAuthenticationKey.pem");
if (pem.trim()) {
  fs.writeFileSync(pemOut, pem.trim() + "\n");
  console.log("Amazon genel anahtarı eklendi (AppstoreAuthenticationKey.pem).");
} else {
  console.log("::warning::AMAZON_PUBLIC_KEY_PEM secret yok: satın almalar Amazon'da çalışmaz. MAGAZA_REHBERI.md › Amazon Appstore.");
}
console.log("Android projesi Amazon Appstore derlemesine çevrildi.");
