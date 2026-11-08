// Play feature graphic (1024x500) per language -> store/feature/<lang>.png
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
const L={tr:['Raf Avcısı','Raflardaki üçlüleri yakala,<br>alışveriş listeni tamamla.','PickyList oyunu','assets/icon-only.png'],
en:['Shelf Hunter','Match three on the shelves,<br>finish your shopping list.','A PickyList game','design/icon/out/en-ios.png'],
de:['Regaljäger','Finde drei Gleiche im Regal,<br>erledige deine Einkaufsliste.','Ein PickyList-Spiel','design/icon/out/de-ios.png'],
es:['Caza Estantes','Junta tres iguales en el estante,<br>completa tu lista de la compra.','Un juego de PickyList','design/icon/out/es-ios.png'],
fr:['Chasse Rayon','Aligne trois produits en rayon,<br>finis ta liste de courses.','Un jeu PickyList','design/icon/out/fr-ios.png'],
pt:['Caça Prateleira','Junte três iguais na prateleira,<br>complete sua lista de compras.','Um jogo do PickyList','design/icon/out/pt-ios.png'],
ru:['Охотник за полками','Собирай по три на полках,<br>закрой список покупок.','Игра от PickyList','design/icon/out/ru-ios.png']};
(async()=>{const root=path.resolve(__dirname,'..');fs.mkdirSync(path.join(root,'store/feature'),{recursive:true});
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1024,height:500}});
for(const [l,[t,s,pill,ic]] of Object.entries(L)){
 const html=`<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="file://${root}/www/fonts/fonts.css"><style>html,body{margin:0}
.f{width:1024px;height:500px;background:linear-gradient(120deg,#B3F1BE,#7FD99A);display:flex;align-items:center;gap:52px;padding:0 64px;box-sizing:border-box;overflow:hidden}
img{width:300px;height:300px;border-radius:68px;box-shadow:0 18px 44px rgba(10,69,33,.3);flex:none}
.t{font-family:"Fraunces","Roboto";font-variation-settings:"opsz" 72;font-weight:900;font-size:78px;color:#0A4521;line-height:1.02}
.s{font-family:Roboto;font-weight:500;font-size:30px;color:#0A4521;margin-top:18px;line-height:1.3}
.p{font-family:Roboto;font-weight:700;font-size:22px;color:#fff;background:#1F9D55;border-radius:999px;padding:9px 20px;display:inline-block;margin-top:24px}</style></head>
<body><div class="f" id="f"><img src="file://${root}/${ic}"><div id="tx"><div class="t" id="t">${t}</div><div class="s">${s}</div><div class="p">${pill}</div></div></div>
<script>document.fonts.ready.then(()=>{const t=document.getElementById('t'),tx=document.getElementById('tx');let fs=78;while((t.scrollWidth>560||tx.scrollHeight>440)&&fs>40){fs-=2;t.style.fontSize=fs+'px'}document.title='ok'})</script></body></html>`;
 const tmp=path.join(__dirname,'_feature.html');fs.writeFileSync(tmp,html);await p.goto('file://'+tmp);await p.waitForFunction(()=>document.title==='ok');await p.waitForTimeout(300);
 await p.locator('#f').screenshot({path:path.join(root,'store/feature',l+'.png')});}
fs.unlinkSync(path.join(__dirname,'_feature.html'));await b.close();})();
