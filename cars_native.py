"""The Cars HD v0.1 — adaptação QPainter do jogo do site, sem HTML/WebView.

Visual, geometria e regras inspirados diretamente no código-fonte do protótipo
web existente no projeto. A implementação é completamente nativa para Qt.
"""
from __future__ import annotations
import math
import time
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF, QLinearGradient, QBrush, QPainterPath
from PySide6.QtWidgets import QWidget
from cars_physics import (
    RaceState, CAR_OPTIONS, SEG, NUM_SEG, TRACK_METERS, TOTAL_LAPS, DRAW_DIST,
    ROAD_HALF, CAMERA_HEIGHT, PLAYER_Z, clamp, mod, rand, center, slope,
    course_elevation,
)

W,H=1000.,620.

def c(hexcode,alpha=None):
    color=QColor(hexcode)
    if alpha is not None: color.setAlpha(alpha)
    return color


def rect(x,y,w,h):return QRectF(float(x),float(y),float(w),float(h))


def poly(points):return QPolygonF([QPointF(float(x),float(y)) for x,y in points])


def clock(seconds):
    minutes=int(seconds//60)
    secs=int(seconds%60)
    return f'{minutes:02d}:{secs:02d}.{int((seconds%1)*100):02d}'


class CarsNativeGame(QWidget):
    """Corrida dentro do HD Launcher com o mesmo conteúdo e regras da versão web."""
    exit_requested=Signal()

    def __init__(self,banner_path=None,parent=None):
        super().__init__(parent)
        self.setObjectName('carsNativeGame')
        self.setMinimumSize(650,410)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.scene='select'
        self.selected=0
        self.race=None
        self.keys=set()
        self.frame=0
        self.preview_position=0.
        self.countdown=0.
        self.countdown_text='3'
        self.countdown_flash=0.
        self.last_tick=time.monotonic()
        self.timer=QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        QTimer.singleShot(0,self.setFocus)

    def start(self):
        self.race=RaceState(self.selected)
        self.keys.clear()
        self.scene='countdown'
        self.countdown=0.
        self.countdown_text='3'
        self.setFocus()
        self.update()

    def garage(self):
        self.scene='select'
        self.keys.clear()
        self.race=None
        self.setFocus()
        self.update()

    def pause(self):
        if self.scene in ('race','countdown'):
            self.scene='pause'
            self.keys.clear()
        elif self.scene=='pause':
            self.scene='race' if self.countdown>=3 else 'countdown'
        self.update()

    def tick(self):
        now=time.monotonic()
        dt=clamp(now-self.last_tick,0,.04)
        self.last_tick=now
        if not self.isVisible():return
        self.frame+=1
        if self.scene=='select':
            self.preview_position=mod(self.preview_position+dt*1200,TRACK_METERS)
        elif self.scene=='countdown':
            self.countdown+=dt
            if self.countdown>=3:
                self.scene='race'
                self.countdown_flash=.58
                self.race.announce('PISA FUNDO!',1.6)
        elif self.scene=='race':
            k=self.keys
            self.race.update(
                dt,
                accelerate=bool(k.intersection((Qt.Key.Key_Up,Qt.Key.Key_W))),
                brake=bool(k.intersection((Qt.Key.Key_Down,Qt.Key.Key_S))),
                steer=int(bool(k.intersection((Qt.Key.Key_Right,Qt.Key.Key_D))))-int(bool(k.intersection((Qt.Key.Key_Left,Qt.Key.Key_A)))),
                nitro=bool(k.intersection((Qt.Key.Key_Shift,))),
            )
            if self.race.finished:self.scene='finished'
        self.countdown_flash=max(0.,self.countdown_flash-dt)
        self.update()

    def hideEvent(self,event):
        if self.scene in ('race','countdown'):self.pause()
        self.keys.clear()
        super().hideEvent(event)

    def keyPressEvent(self,event):
        key=event.key()
        if key==Qt.Key.Key_Escape:
            if self.scene=='pause':self.garage()
            else:self.exit_requested.emit()
            return
        if event.isAutoRepeat():return
        if key==Qt.Key.Key_P:
            self.pause()
            return
        if self.scene=='select':
            if key in (Qt.Key.Key_Left,Qt.Key.Key_A):self.selected=(self.selected-1)%len(CAR_OPTIONS)
            elif key in (Qt.Key.Key_Right,Qt.Key.Key_D):self.selected=(self.selected+1)%len(CAR_OPTIONS)
            elif key in (Qt.Key.Key_Return,Qt.Key.Key_Enter,Qt.Key.Key_Space):self.start()
        elif self.scene=='pause':
            if key in (Qt.Key.Key_Return,Qt.Key.Key_Enter,Qt.Key.Key_Space):self.pause()
        elif self.scene=='finished':
            if key in (Qt.Key.Key_R,Qt.Key.Key_Return,Qt.Key.Key_Enter):self.start()
            elif key==Qt.Key.Key_G:self.garage()
        elif self.scene in ('race','countdown'):
            if key in (Qt.Key.Key_Space,Qt.Key.Key_E) and self.scene=='race':self.race.use_item()
            self.keys.add(key)
        self.update()

    def keyReleaseEvent(self,event):
        if not event.isAutoRepeat():self.keys.discard(event.key())
        super().keyReleaseEvent(event)

    def mousePressEvent(self,event):
        x=event.position().x()*W/max(self.width(),1)
        y=event.position().y()*H/max(self.height(),1)
        if self.scene=='select':
            if 80<=x<=380 and 325<=y<=445:
                if x<145:self.selected=(self.selected-1)%3
                elif x>310:self.selected=(self.selected+1)%3
            if 69<=x<=409 and 483<=y<=533:self.start()
            elif x>=900 and y<55:self.exit_requested.emit()
        elif self.scene=='race':
            if x>900 and y<64:self.pause()
            elif x>840 and 180<=y<=320 and self.race:self.race.use_item()
        elif self.scene=='countdown':
            if x>900 and y<64:self.pause()
        elif self.scene=='pause':
            if 245<=y<=455:
                if x<535:self.pause()
                else:self.garage()
        elif self.scene=='finished':
            if 390<=y<=570:
                if x<530:self.start()
                else:self.garage()
        self.setFocus()
        self.update()

    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self.width()/W,self.height()/H)
        pos=self.preview_position if self.scene=='select' else (self.race.distance if self.race else 0)
        lane=0 if self.scene=='select' else self.race.lane
        self.draw_sky(p)
        self.draw_road(p,pos,lane)
        if self.scene=='select':
            self.draw_car(p,770,552,180,c('#238eff'),True,True)
        else:
            self.draw_actors(p,pos,lane)
            self.draw_car(p,500,552,145,c(CAR_OPTIONS[self.selected]['color']),True,self.race.nitro_active)
            if self.race.shield>0:
                p.setPen(QPen(c('#71D8FF',210),3))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(rect(393,410,214,165))
        self.draw_weather(p)
        self.draw_header(p)
        if self.scene=='select':self.draw_menu(p)
        else:
            if self.scene!='finished':self.draw_hud(p)
            if self.scene=='countdown':
                label=str(max(1,3-int(self.countdown)))
                self.text(p,label,370,195,260,175,100,'#FFDF43',True)
            elif self.countdown_flash>0:
                self.text(p,'VAI!',380,230,240,110,55,'#FFDF43',True)
            if self.scene=='pause':self.draw_pause(p)
            elif self.scene=='finished':self.draw_finish(p)
        self.text(p,'© HD LAUNCHER  •  THE CARS HD  •  PROTÓTIPO ORIGINAL',580,590,405,25,9,'#8095A4')
        p.end()

    @staticmethod
    def text(p,s,x,y,w,h,size=12,color='#F3FAFF',bold=False,align=None):
        p.setPen(c(color))
        font=QFont('Segoe UI',size,QFont.Weight.Bold if bold else QFont.Weight.Normal)
        p.setFont(font)
        p.drawText(rect(x,y,w,h),align or (Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignHCenter),str(s))

    @staticmethod
    def box(p,x,y,w,h,fill='#0D2131',outline=None,radius=8):
        p.setPen(QPen(c(outline),1) if outline else Qt.PenStyle.NoPen)
        p.setBrush(c(fill))
        p.drawRoundedRect(rect(x,y,w,h),radius,radius)

    @staticmethod
    def polygon(p,points,color):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c(color))
        p.drawPolygon(poly(points))

    def draw_sky(self,p):
        sky=QLinearGradient(0,0,0,H)
        for t,color in ((0,'#0c2435'),(.32,'#37556b'),(.53,'#65818a'),(.56,'#a8a49c'),(.80,'#333c42'),(1,'#131d23')):
            sky.setColorAt(t,c(color))
        p.fillRect(rect(0,0,W,H),QBrush(sky))
        # Skyline multicamada como no jogo do site.
        for layer in range(3):
            x=-15.
            base=H*(.56+layer*.025)
            while x<W+80:
                idx=int(x*1.3+layer*235)
                bw=(13+rand(idx+3)*45+layer*15)*.80
                bh=(24+rand(idx+4)*130+layer*20)*.84
                y=base-bh
                p.setPen(Qt.PenStyle.NoPen)
                p.fillRect(rect(x,y,bw,bh+80),c(('#526470','#354856','#233b49')[layer]))
                p.fillRect(rect(x,y,bw,2),c(('#607888','#4c6172','#354c59')[layer]))
                for wx in range(int(x+5),int(x+bw-3),9):
                    for wy in range(int(y+7),int(base-6),13):
                        if rand(wx*7+wy*13+layer*21)>.65:
                            p.fillRect(rect(wx,wy,2,3),c('#E5E8C5',110 if layer==2 else 60))
                x+=bw+1
        # Viaduto sobre a zona portuária.
        p.setPen(QPen(c('#1B2C39'),6))
        p.drawLine(QPointF(500,330),QPointF(1065,326))
        for i in range(9):
            x=480+i*83
            p.fillRect(rect(x,323,5,26),c('#1C303D'))
        # Luz urbana difusa junto ao horizonte.
        glow=QLinearGradient(0,285,0,510)
        glow.setColorAt(0,c('#F6CC9C',65))
        glow.setColorAt(1,c('#061524',0))
        p.fillRect(rect(0,285,1000,240),QBrush(glow))

    def project(self,z,lateral,pos,cam_x=0):
        forward=z-pos
        if forward<35:return None
        depth=1.10/forward
        x=W*.5+(center(z)-center(pos+PLAYER_Z)-slope(pos+PLAYER_Z)*(z-pos-PLAYER_Z)+lateral-cam_x)*depth*W*.47
        y=H*.555+(CAMERA_HEIGHT-course_elevation(z))*depth*H*.5
        road=ROAD_HALF*depth*W*.47
        return x,y,road

    def draw_road(self,p,pos,lane):
        p.fillRect(rect(0,H*.55,W,H*.45),c('#253a40'))
        start=int((pos+PLAYER_Z)//SEG)
        surface=[]
        for i in range(DRAW_DIST):
            segment=start+i
            z1=segment*SEG
            a=self.project(z1,0,pos,lane*ROAD_HALF)
            b=self.project(z1+SEG,0,pos,lane*ROAD_HALF)
            if a is not None and b is not None and a[1]>b[1] and b[1]<H*1.25 and a[1]>H*.48:
                surface.append((segment,a,b))
        for segment,a,b in reversed(surface):
            x1,y1,w1=a
            x2,y2,w2=b
            alt=(segment//3)%2==0
            p.fillRect(rect(0,y2,W,max(1,y1-y2)),c('#293b3f' if alt else '#2c4043'))
            for factor,color in ((1.20,'#46545A'),(1.10,'#A9AFAB'),(1.05,'#B7504C' if alt else '#CBC0B2'),(1.,'#202C32' if alt else '#243039')):
                self.polygon(p,[(x1-w1*factor,y1),(x1+w1*factor,y1),(x2+w2*factor,y2),(x2-w2*factor,y2)],color)
            for lane_pos in (-.955,.955):
                self.lane_strip(p,a,b,lane_pos,.008,'#D4D4C0')
            if segment%7<4:
                self.lane_strip(p,a,b,-.34,.008,'#A9B8C0')
                self.lane_strip(p,a,b,.34,.008,'#A9B8C0')
            if segment%7==0:
                self.lane_strip(p,a,b,-.43,.008,'#435660')
            if segment%NUM_SEG==3:
                for j in range(-8,8):
                    xx=x1+(j/8)*w1
                    p.fillRect(rect(xx,y1-max(3,y1-y2),max(1,w1/8),max(3,y1-y2)),c('#E2E8E6' if j%2 else '#23323A'))
        for segment,a,b in reversed(surface):
            index=segment%NUM_SEG
            x,y,w=a
            if not (H*.51<y<H*1.1):continue
            if index%19==0:
                for side in (-1,1):self.draw_lamp(p,x+side*w*1.26,y,w*.20,side)
            if index%67==16:self.draw_billboard(p,x+w*1.70,y,w*.33,'PORTO NEON' if index%2 else 'HD RACING')
            if index%57==35:self.draw_sign(p,x-w*1.36,y,w*.14)

    def lane_strip(self,p,a,b,lane,width,color):
        x1,y1,w1=a
        x2,y2,w2=b
        self.polygon(p,[(x1+w1*(lane-width),y1),(x1+w1*(lane+width),y1),(x2+w2*(lane+width),y2),(x2+w2*(lane-width),y2)],color)

    def draw_lamp(self,p,x,y,size,side):
        size=clamp(size,1,210)
        if size<3:return
        pole=size*2.4
        p.setPen(QPen(c('#758C9A'),max(1.,size*.08)))
        p.drawLine(QPointF(x,y),QPointF(x,y-pole))
        p.drawLine(QPointF(x,y-pole),QPointF(x+side*size*.8,y-pole-size*.12))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c('#FFE7B2'))
        p.drawEllipse(rect(x+side*size*.8-size*.13,y-pole-size*.25,size*.26,size*.26))

    def draw_billboard(self,p,x,y,size,name):
        size=clamp(size,0,155)
        if size<7:return
        p.fillRect(rect(x-size*.07,y-size*1.05,size*.14,size*1.05),c('#38464B'))
        self.box(p,x-size*.90,y-size*1.8,size*1.8,size*.75,'#07263B','#3BCD9B',2)
        self.text(p,name,x-size*.85,y-size*1.7,size*1.7,size*.50,max(6,int(size*.19)),'#DFF6EA',True)

    def draw_sign(self,p,x,y,size):
        size=clamp(size,0,90)
        if size<4:return
        p.fillRect(rect(x-size*.04,y-size*2,size*.09,size*2),c('#72808A'))
        p.fillRect(rect(x-size*.78,y-size*2.3,size*1.56,size*.65),c('#145B60'))
        self.text(p,'NEON',x-size*.76,y-size*2.28,size*1.52,size*.54,max(5,int(size*.25)),'#E1FFDF',True)

    def draw_garage_car(self,p,x,y,width,color):
        """Vista lateral da garagem, como na interface do protótipo web."""
        w=width
        p.save()
        p.translate(x,y)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c('#03121A',125))
        p.drawEllipse(rect(-w*.57,38,w*1.14,19))
        self.polygon(p,[(-w*.50,8),(-w*.40,-3),(-w*.21,-20),(w*.22,-20),(w*.42,0),(w*.50,13),(w*.46,34),(-w*.50,34)],color.name())
        self.polygon(p,[(-w*.19,-19),(-w*.10,-39),(w*.20,-39),(w*.32,-18)],'#A5D0E4')
        self.polygon(p,[(-w*.08,-35),(w*.16,-35),(w*.26,-20),(-w*.16,-20)],'#254055')
        p.fillRect(rect(-w*.46,18,w*.90,5),c('#092337'))
        p.fillRect(rect(-w*.48,15,22,7),c('#FFF5AE'))
        p.fillRect(rect(w*.37,15,20,7),c('#FFF5AE'))
        for cx in (-w*.33,w*.30):
            p.setPen(QPen(c('#7C909F'),4))
            p.setBrush(c('#09111B'))
            p.drawEllipse(rect(cx-15,18,30,30))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c('#A3C9D9'))
            p.drawEllipse(rect(cx-6,27,12,12))
        p.restore()

    def draw_car(self,p,x,y,width,color,player=False,boost=False):
        if width<4:return
        w=width;h=w*.80
        p.save();p.translate(x,y)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(c('#06111C',100))
        p.drawEllipse(rect(-w*.70,-h*.12,w*1.4,h*.30))
        p.fillRect(rect(-w*.58,-h*.5,w*.17,h*.55),c('#060D12'))
        p.fillRect(rect(w*.41,-h*.5,w*.17,h*.55),c('#060D12'))
        p.fillRect(rect(-w*.51,-h*.16,w*1.02,h*.24),c('#121921'))
        self.polygon(p,[(-w*.51,-h*.14),(-w*.44,-h*.59),(-w*.27,-h*.80),(w*.27,-h*.80),(w*.44,-h*.59),(w*.51,-h*.14)],color.name())
        self.polygon(p,[(-w*.31,-h*.73),(-w*.23,-h*.96),(w*.23,-h*.96),(w*.31,-h*.73)],'#274459')
        self.polygon(p,[(-w*.27,-h*.77),(-w*.20,-h*.92),(w*.20,-h*.92),(w*.27,-h*.77)],'#92CBDF')
        p.fillRect(rect(-w*.45,-h*.23,w*.90,h*.15),c('#09151F'))
        for xx in (-w*.45,w*.29):p.fillRect(rect(xx,-h*.30,w*.16,h*.12),c('#F54D4D'))
        p.fillRect(rect(-w*.08,-h*.15,w*.16,h*.07),c('#CDE9F1'))
        p.fillRect(rect(-w*.43,-h*.91,w*.86,h*.075),c('#071419'))
        p.fillRect(rect(-w*.45,-h*.93,w*.90,h*.050),color)
        if player and boost:
            self.polygon(p,[(-w*.21,-h*.10),(-w*.13,h*.45),(0,-h*.08)],'#59D5FF')
            self.polygon(p,[(w*.21,-h*.10),(w*.13,h*.45),(0,-h*.08)],'#FFD55D')
        p.restore()

    def draw_actors(self,p,pos,lane):
        actors=[]
        lap_index=int(pos//TRACK_METERS)
        for ai in self.race.rivals:
            dist=mod(ai.progress-pos,TRACK_METERS)
            if 300<dist<DRAW_DIST*SEG:actors.append((dist,'car',ai))
        for pickup in self.race.pickups:
            if pickup.collected_lap==lap_index:continue
            dist=mod(pickup.progress-mod(pos,TRACK_METERS),TRACK_METERS)
            if 80<dist<DRAW_DIST*SEG:actors.append((dist,'pickup',pickup))
        for dist,kind,obj in sorted(actors,key=lambda x:-x[0]):
            projection=self.project(pos+PLAYER_Z+dist,obj.lane*ROAD_HALF,pos,lane*ROAD_HALF)
            if not projection:continue
            x,y,w=projection
            if not H*.51<y<H*1.4:continue
            if kind=='car':self.draw_car(p,x,y,clamp(w*.30,5,225),c(obj.color))
            else:self.draw_pickup(p,x,y,clamp(w*.13,4,72))

    def draw_pickup(self,p,x,y,s):
        self.polygon(p,[(x,y-s*1.7),(x+s*.8,y-s*1.2),(x+s*.8,y-s*.2),(x,y+s*.3),(x-s*.8,y-s*.2),(x-s*.8,y-s*1.2)],'#1C4F77')
        p.setPen(QPen(c('#FFDC55'),max(1,s*.075)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolygon(poly([(x,y-s*1.7),(x+s*.8,y-s*1.2),(x+s*.8,y-s*.2),(x,y+s*.3),(x-s*.8,y-s*.2),(x-s*.8,y-s*1.2)]))
        self.text(p,'?',x-s/2,y-s*1.35,s,s,max(8,int(s*.9)),'#FFED97',True)

    def draw_weather(self,p):
        p.setPen(QPen(c('#DCEFFB',25),1))
        for i in range(49):
            x=mod(rand(i*8+9)*W*2+self.frame*1.7*(1+rand(i)*2),W+150)-65
            y=mod(rand(i*3+1)*H+self.frame*5*(1+rand(i*2)),H+90)-45
            p.drawLine(QPointF(x,y),QPointF(x-4,y+11+rand(i)*17))
        shade=QLinearGradient(0,0,0,H)
        shade.setColorAt(0,c('#081524',14))
        shade.setColorAt(.55,c('#051018',6))
        shade.setColorAt(1,c('#02080E',85))
        p.fillRect(rect(0,0,W,H),QBrush(shade))

    def draw_header(self,p):
        self.box(p,0,0,W,57,'#061522')
        self.box(p,29,11,37,36,'#064E47','#1BE98E',1)
        self.text(p,'HD',30,12,35,34,15,'#FFFFFF',True)
        self.text(p,'THE CARS',72,10,133,23,16,'#FFFFFF',True)
        self.text(p,'HD',205,10,32,23,16,'#FFDA3F',True)
        self.text(p,'STREET RACING SERIES',76,33,218,16,8,'#BFD4E5')
        self.text(p,'●  PROTÓTIPO 0.1  •  EDIÇÃO NATIVA',708,11,217,35,9,'#BEE4DB',True)
        self.box(p,940,12,42,34,'#12283A','#45627A',8)
        self.text(p,'Ⅱ',941,13,40,31,18,'#D9EEFF',True)

    def draw_menu(self,p):
        p.fillRect(rect(0,57,470,H-57),c('#030D17',198))
        self.text(p,'✦  HD ORIGINALS    ───    PRIMEIRA TEMPADA',52,72,400,22,10,'#91D8C2',True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.text(p,'THE CARS',54,96,304,68,43,'#F3FCFF',True)
        self.text(p,'HD',345,96,110,68,44,'#FFDA3F',True)
        self.text(p,'A cidade é sua pista. Desvie do trânsito, desafie',54,166,406,28,11,'#C6D9E4',False,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.text(p,'rivais e chegue ao topo.',54,192,410,28,11,'#C6D9E4',False,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        for label,x,width,color in [('◆ CORRIDA ARCADE',54,128,'#98FFD6'),('◆ 3 VOLTAS',189,100,'#FFE28F'),('⚡ TURBO & ITENS',297,124,'#A7CFFF')]:
            self.box(p,x,229,width,23,'#12283A','#325574',4)
            self.text(p,label,x,229,width,23,8,color,True)
        self.box(p,54,263,371,297,'#0B1F31','#31536A',11)
        self.text(p,'SUA GARAGEM',68,269,150,20,9,'#89BDB7',True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.text(p,'Escolha seu carro',68,289,241,28,17,'#FFFFFF',True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.text(p,f'{self.selected+1:02d} / 03',320,287,92,27,12,'#FFE349',True)
        self.box(p,78,326,32,32,'#122F43','#557C92',16)
        self.box(p,368,326,32,32,'#122F43','#557C92',16)
        self.text(p,'‹',78,326,32,32,22,'#D6F2FF')
        self.text(p,'›',368,326,32,32,22,'#D6F2FF')
        car=CAR_OPTIONS[self.selected]
        self.draw_garage_car(p,241,374,195,c(car['color']))
        self.text(p,car['name'].upper(),68,404,201,23,14,'#FFFFFF',True,Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.text(p,car['description'],190,426,216,20,9,'#BFD2DB')
        stats=(('VELOCIDADE',car['speed_stat'],'#1FE58D'),('CONTROLE',car['handling'],'#43A3FF'),('TURBO',car['turbo'],'#FFDB4D'))
        for i,(name,value,color) in enumerate(stats):
            x=69+i*115
            self.text(p,name,x,448,105,15,8,'#AEC1CF',True)
            self.box(p,x,465,99,5,'#253D4E',None,2)
            self.box(p,x,465,99*value,5,color,None,2)
        self.box(p,69,483,340,50,'#00D365',None,6)
        self.text(p,'▶   INICIAR CORRIDA   →',69,483,340,50,14,'#001D1C',True)
        self.text(p,'🏁 CIRCUITO PORTO NEON               6 PILOTOS • 3 VOLTAS',70,535,338,21,8,'#A8C6D1')
        self.text(p,'W / ↑ ACELERAR  •  A D / ← → DIRIGIR  •  SHIFT NITRO  •  ESPAÇO ITEM',42,571,660,20,9,'#ABBFCF')

    def draw_hud(self,p):
        race=self.race
        # Posição, volta, tempo: canto esquerdo, como a HUD do site.
        for x,w,title,value in ((28,91,'POSIÇÃO',str(race.place)+' /6'),(126,80,'VOLTA',str(race.lap)+'/3'),(213,139,'TEMPO',clock(race.seconds))):
            self.box(p,x,66,w,57,'#0B2234','#31516B',6)
            self.text(p,title,x+8,70,w-16,16,9,'#A4C9C5',True)
            self.text(p,value,x+5,85,w-10,34,22 if title!='TEMPO' else 17,'#FFDA36' if title=='POSIÇÃO' else '#FFFFFF',True)
        # Velocidade, nitro e item à direita.
        for y,h in ((66,80),(152,51),(209,65)):
            self.box(p,860,y,132,h,'#0B2234','#31516B',6)
        self.text(p,'VELOCIDADE',867,66,116,18,9,'#A4C9C5',True)
        speed_kmh=int(round(race.speed/race.car['top']*265))
        self.text(p,f'{speed_kmh:03d}',863,82,118,43,34,'#FDFEFF',True)
        self.text(p,'KM/H',933,125,43,17,9,'#BBD0E0')
        self.box(p,872,136,107,5,'#233E54',None,2)
        self.box(p,872,136,107*min(1,race.speed/race.car['top']),5,'#1EE88E',None,2)
        self.text(p,'NITRO  •  SHIFT',866,155,120,18,9,'#B3D2E4',True)
        self.box(p,872,181,105,6,'#264052',None,3)
        self.box(p,872,181,105*race.nitro,6,'#3EA3FF',None,3)
        self.text(p,'ITEM  •  ESPAÇO',867,212,118,18,9,'#A4C9C5',True)
        self.text(p,race.item or '—',863,234,123,33,14,'#FFD836',True)
        self.box(p,28,581,935,3,'#213950',None,1)
        self.box(p,28,581,935*clamp(race.distance/(TRACK_METERS*TOTAL_LAPS),0,1),3,'#07D478',None,1)
        if race.message_time>0:
            self.box(p,340,129,320,42,'#073828','#1EBC79',7)
            self.text(p,race.message,340,129,320,42,12,'#FFE459',True)

    def overlay(self,p,title,subtitle):
        p.fillRect(rect(0,58,W,H-58),c('#04111C',225))
        self.box(p,218,137,564,345,'#0D2232','#36678B',14)
        self.text(p,title,241,169,518,74,32,'#FFE253',True)
        self.text(p,subtitle,245,265,510,34,12,'#C6DDED')

    def draw_pause(self,p):
        self.overlay(p,'CORRIDA PAUSADA','Pressione P para continuar')
        self.box(p,262,370,214,62,'#00CE61',None,9)
        self.text(p,'▶ CONTINUAR',262,370,214,62,15,'#041D1A',True)
        self.box(p,524,370,214,62,'#154F79',None,9)
        self.text(p,'VOLTAR À GARAGEM',524,370,214,62,14,'#FFFFFF',True)

    def draw_finish(self,p):
        race=self.race
        title='VOCÊ VENCEU!' if race.place==1 else ('PÓDIO GARANTIDO!' if race.place<=3 else 'CORRIDA CONCLUÍDA')
        self.overlay(p,title,'Porto Neon tem um novo campeão.' if race.place==1 else 'Hora de tentar um resultado ainda melhor!')
        self.text(p,'🏆' if race.place==1 else '🏁',459,248,82,70,34,'#FFDF39')
        self.text(p,f'{race.place}º LUGAR  •  TEMPO {clock(race.seconds)}',260,315,480,31,17,'#36E69A',True)
        best='--:--' if math.isinf(race.best_lap) else clock(race.best_lap)
        self.text(p,'MELHOR VOLTA: '+best,285,350,430,25,11,'#B8D7E8')
        self.box(p,262,399,215,55,'#00CE61',None,9)
        self.text(p,'↻ CORRER DE NOVO',262,399,215,55,14,'#041D1A',True)
        self.box(p,523,399,215,55,'#154F79',None,9)
        self.text(p,'VOLTAR À GARAGEM',523,399,215,55,13,'#FFFFFF',True)
