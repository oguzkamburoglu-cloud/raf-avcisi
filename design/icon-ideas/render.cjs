const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1024,height:4200}});
await p.goto('file://'+path.resolve(__dirname,'ideas.html'));await p.evaluate(async()=>{await document.fonts.load('100px "Noto Color Emoji"','🍅');await document.fonts.ready});await p.waitForTimeout(800);
for(const id of ['A','B','C','D'])await p.locator('#'+id).screenshot({path:path.join(__dirname,id+'.png')});
await b.close();})();
