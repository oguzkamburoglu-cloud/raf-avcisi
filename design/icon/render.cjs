// NODE_PATH=/opt/node-tools/node_modules node design/icon/render.cjs [lang...]  -> design/icon/out/<lang>-{ios,android-full}.png
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
const NAMES={tr:['Raf','Avcısı'],en:['Shelf','Hunter'],de:['Regal','Jäger'],es:['Caza','Estantes'],fr:['Chasse','Rayon'],pt:['Caça','Prateleira'],ru:['Охотник','за полками']};
(async()=>{const dir=__dirname, out=path.join(dir,'out');fs.mkdirSync(out,{recursive:true});
const only=process.argv.slice(2);const b=await chromium.launch();
for(const [lang,[l1,l2]] of Object.entries(NAMES)){ if(only.length&&!only.includes(lang))continue;
 for(const kind of ['ios','android']){
  const opts={l1,l2,base:kind=='ios'?'base-clean.png':'base-clean-notick.png',
    tick:kind=='android'?{left:'700px',top:'728px',width:'135px',height:'135px'}:null};
  const p=await b.newPage({viewport:{width:1024,height:1024}});
  await p.addInitScript(o=>{window.OPTS=o},opts);
  await p.goto('file://'+path.join(dir,'icon.html'));
  await p.waitForFunction(()=>document.title==='ready'&&document.getElementById('base').complete);
  await p.waitForTimeout(200);
  await p.locator('#c').screenshot({path:path.join(out,`${lang}-${kind}.png`)});await p.close();
 }}
await b.close();})();
