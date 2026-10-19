"""Generate original neon-style promotional graphics (no external assets needed)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math, random
import numpy as np

ROOT = Path(__file__).parent / 'assets'
ROOT.mkdir(exist_ok=True)
random.seed(127)
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
ITALIC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf'

def font(size, italic=False):
    return ImageFont.truetype(ITALIC if italic else BOLD, size)

def text_glow(base, xy, message, f, color, stroke='#00101c', glow='#057aff'):
    aura=Image.new('RGBA',base.size)
    d=ImageDraw.Draw(aura)
    d.text(xy, message, font=f, fill=color, stroke_width=5, stroke_fill=stroke)
    blur=aura.filter(ImageFilter.GaussianBlur(13))
    base.alpha_composite(blur)
    base.alpha_composite(aura)

def dark_gradient(w,h, top=(2,9,22), bottom=(3,28,37)):
    ys=np.linspace(0,1,h)[:,None,None]
    xs=np.linspace(0,1,w)[None,:,None]
    top=np.array(top).reshape(1,1,3)
    bottom=np.array(bottom).reshape(1,1,3)
    grad=top*(1-ys)+bottom*ys
    grad=np.tile(grad,(1,w,1))
    glow=(np.sin(xs*math.pi)**2)*np.sin(ys*math.pi)**2
    grad[...,2]=np.clip(grad[...,2]+40*glow[...,0],0,255)
    a=np.empty((h,w,4),dtype=np.uint8)
    a[...,:3]=grad.astype('uint8')
    a[...,3]=255
    return Image.fromarray(a,'RGBA')

def glow_line(img,a,b,color,width=3):
    ov=Image.new('RGBA',img.size)
    g=ImageDraw.Draw(ov)
    g.line([a,b], fill=color,width=width+12)
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(11)))
    g=ImageDraw.Draw(img)
    g.line([a,b], fill=color,width=width)

def skyline(img,y_base):
    d=ImageDraw.Draw(img)
    W,H=img.size
    for x in range(0,W,22):
        v=random.randint(50,185)
        peak=max(5,int(y_base-v))
        d.rectangle((x,peak,x+19,H),fill=(3,12,24,255))
        for wy in range(peak+10,int(y_base),14):
            if random.random()>.68:
                d.rectangle((x+4,wy,x+7,wy+4),fill=random.choice(['#1C68A9','#0B8648','#A87F19']))

def neon_cube(im,cx,cy,r,main='#2B96FF'):
    d=ImageDraw.Draw(im)
    p1=(cx,cy-r);p2=(cx+r,cy-r//3);p3=(cx+r,cy+r//2);p4=(cx,cy+r);p5=(cx-r,cy+r//2);p6=(cx-r,cy-r//3)
    d.polygon([p1,p2,p3,(cx,cy+r//4)], fill=(6,36,67,255))
    d.polygon([(cx,cy+r//4),p3,p4,p5],fill=(5,23,42,255))
    for a,b in [(p1,p2),(p2,p3),(p3,p4),(p4,p5),(p5,p6),(p6,p1),(p1,(cx,cy+r//4)),((cx,cy+r//4),p3),((cx,cy+r//4),p5)]:
        glow_line(im,a,b,main,2)

# Main featured artwork: skyline, glowing road, floating cubes and arc.
hero=dark_gradient(1160,365, (3,10,26),(2,31,42))
skyline(hero, 263)
d=ImageDraw.Draw(hero)
for i in range(6):
    y=275+i*i*4
    if y<365:glow_line(hero,(0,y),(1160,y), '#0A66B4',1)
for x in range(-250,1350,100):
    glow_line(hero,(580,263),(x,365), '#045F74',2)
for (cx,cy,r) in [(860,140,50),(1080,225,33),(700,220,25)]:neon_cube(hero,cx,cy,r)
for i in range(6):
    x=650+i*64
    glow_line(hero,(x,-20),(x+250,220),random.choice(['#2F7DFF','#03AB54','#FFD600']),2)
# Racer silhouette
layer=Image.new('RGBA',hero.size)
d=ImageDraw.Draw(layer)
d.ellipse((700,100,820,220),fill='#091C2B')
d.polygon([(722,180),(792,179),(847,270),(814,349),(666,349),(663,255)],fill='#092638')
d.line([(714,164),(751,120),(795,142)],fill='#21E371',width=7)
d.line([(682,249),(731,223),(757,328)],fill='#137BFA',width=8)
d.line([(800,223),(835,260),(819,335)],fill='#FFDA12',width=6)
hero.alpha_composite(layer)
# highlight on the right to keep left text visible
hero.save(ROOT/'hero.png')

# Cards have big distinctive visuals, text labels, and neon accents.
W,H=600,380
for name in ('neon-dodge','star-catcher','reflex-rush'):
    im=dark_gradient(W,H, (3,11,25),{'neon-dodge':(7,23,64),'star-catcher':(7,48,33),'reflex-rush':(2,36,75)}[name])
    d=ImageDraw.Draw(im)
    for i in range(75):
        x=random.randint(0,W); y=random.randint(0,H)
        if name=='star-catcher':
            r=random.randint(1,3); d.ellipse((x-r,y-r,x+r,y+r),fill=(255,209,25,random.randint(50,185)))
        else:
            d.line([(x,y),(x+random.randint(-8,12),y+random.randint(8,30))], fill=random.choice(['#125A8B','#164E39','#176188']),width=1)
    if name=='neon-dodge':
        skyline(im,280)
        neon_cube(im,458,156,62,'#278EFF')
        neon_cube(im,165,244,45,'#12DB79')
        d=ImageDraw.Draw(im)
        d.polygon([(320,120),(274,281),(371,281)],fill='#00C853')
        d.polygon([(320,141),(297,264),(349,264)],fill='#0A2B40')
        title='NEON';sub='DODGE';base='#66CDFF'
    elif name=='star-catcher':
        glow_line(im,(110,370),(425,40),'#E6B706',5)
        d=ImageDraw.Draw(im)
        for cx,cy,r in [(445,125,49),(325,205,25),(170,130,16)]:
            pts=[]
            for z in range(10):
                a=-math.pi/2+math.pi*z/5
                rad=r if z%2==0 else r*.43
                pts.append((cx+math.cos(a)*rad,cy+math.sin(a)*rad))
            d.polygon(pts,fill='#FFD600')
        title='CAÇA';sub='ESTRELAS';base='#FFF0A1'
    else:
        for i in range(4):
            r=82+i*24
            d=ImageDraw.Draw(im)
            d.arc((365-r,210-r,365+r,210+r),10,315,fill=['#28B2FF','#FFD600','#05C960'][i%3],width=9)
        d.ellipse((336,180,394,238),fill='#FFD600')
        title='REFLEXO';sub='TURBO';base='#67C7FF'
    f=font(62,True) if name!='star-catcher' else font(65,True)
    f2=font(64,True)
    text_glow(im,(25,25),title,f,base)
    text_glow(im,(45,94),sub,f2,'#FFD600' if name!='star-catcher' else '#53FFAB')
    im.save(ROOT/f'{name}.png')

# New original HD crown logo with blue HD, yellow crown, green/blue light trails
logo=Image.new('RGBA',(520,280),(0,0,0,0))
for a,b,color in [((25,218),(170,32),'#00C853'),((330,22),(482,201),'#FFD600'),((8,245),(150,135),'#178DFE')]:
    glow_line(logo,a,b,color,7)
d=ImageDraw.Draw(logo)
# Gold crown on HD
d.polygon([(190,48),(179,11),(218,30),(238,4),(255,29),(293,8),(282,50)],fill='#FFD600')
d.line([(190,48),(282,50)],fill='#FFF29A',width=5)
text_glow(logo,(75,33),'HD',font(168,True),'#55B7FF',stroke='#06142B',glow='#079DFF')
# inset yellow highlight
d.text((87,43),'HD',font=font(168,True),fill='#55B7FF',stroke_width=2,stroke_fill='#E4FF42')
text_glow(logo,(96,204),'LAUNCHER',font(47,True),'#F1F7FF',stroke='#071527',glow='#00BB77')
logo.save(ROOT/'hd-logo.png')
logo.crop((80,0,354,255)).resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'hd-launcher.ico',format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('Created',[(p.name,p.stat().st_size) for p in ROOT.iterdir()])
