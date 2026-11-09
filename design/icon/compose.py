"""out/<lang>-android.png (full art) -> out/<lang>-adaptive.png (108dp layer: art at 70% over its own
edge-stretched copy) ; preview sheet."""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFilter
D=os.path.dirname(os.path.abspath(__file__))+'/out'
def adaptive(art):
    s=int(1024*0.70); a=art.resize((s,s),Image.LANCZOS); off=(1024-s)//2
    bg=art.resize((1024,1024)).filter(ImageFilter.GaussianBlur(30))   # only shows during launcher animations
    bg.paste(a,(off,off)); return bg
def mask(s,kind):
    m=Image.new('L',(s,s),0); d=ImageDraw.Draw(m)
    (d.ellipse if kind=='circle' else lambda b,fill: d.rounded_rectangle(b,radius=int(s*.225),fill=fill))([0,0,s-1,s-1],fill=255); return m
langs=sys.argv[1:] or sorted({os.path.basename(p).split('-')[0] for p in glob.glob(D+'/*-ios.png')})
S=300; sheet=Image.new('RGB',(40+len(langs)*(S+30),2*S+120),'#ECECEC')
for i,l in enumerate(langs):
    ios=Image.open(f'{D}/{l}-ios.png').convert('RGB'); ad=adaptive(Image.open(f'{D}/{l}-android.png').convert('RGB')); ad.save(f'{D}/{l}-adaptive.png')
    x=40+i*(S+30); sheet.paste(ios.resize((S,S),Image.LANCZOS),(x,40),mask(S,'sq'))
    vis=ad.crop((171,171,853,853)).resize((S,S),Image.LANCZOS); sheet.paste(vis,(x,80+S),mask(S,'circle'))
sheet.save(D+'/preview.png'); print(D+'/preview.png')
