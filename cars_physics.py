"""The Cars HD — simulação nativa baseada nas regras do protótipo web v0.1.

Partilha os mesmos números, geometria, ordem das voltas e efeitos do jogo publicado
no site, sem executar HTML/JS ou abrir um navegador no Windows.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

SEG = 210.0
NUM_SEG = 650
TRACK_METERS = SEG * NUM_SEG  # unidades fictícias da pista original (136.500)
TOTAL_LAPS = 3
DRAW_DIST = 165
ROAD_HALF = 1850.0
CAMERA_HEIGHT = 1050.0
PLAYER_Z = 1120.0
TWO_PI = math.tau

CAR_OPTIONS = (
    {"name": "Falcão GT", "description": "Equilibrado • Grip urbano", "color": "#09dd72", "speed_stat": .87, "handling": .87, "turbo": .72, "top": 3650.0},
    {"name": "Vortex X", "description": "Velocidade máxima • Nervoso", "color": "#2699ff", "speed_stat": .98, "handling": .65, "turbo": .77, "top": 3950.0},
    {"name": "Relâmpago 77", "description": "Turbo potente • Agressivo", "color": "#ffcc32", "speed_stat": .78, "handling": .81, "turbo": .99, "top": 3470.0},
)


def clamp(value, low, high):
    return max(low, min(high, value))


def mod(value, base):
    return ((value % base) + base) % base


def rand(seed):
    x = math.sin(seed * 89.141 + 7.17) * 47583.295
    return x - math.floor(x)


def center(z):
    t = TWO_PI * z / TRACK_METERS
    return 1770 * math.sin(2*t+.3) + 820*math.sin(4*t+1.5) + 300*math.sin(7*t+2)


def slope(z):
    return (center(z+50)-center(z-50))/100


def course_elevation(z):
    t = TWO_PI*z/TRACK_METERS
    return 115*math.sin(3*t)+30*math.cos(8*t)


@dataclass
class Rival:
    id: int
    lane: float
    base_lane: float
    progress: float
    speed: float
    color: str
    wobble: float
    stun: float = 0.0


@dataclass
class Pickup:
    progress: float
    lane: float
    collected_lap: int = -1


class RaceState:
    """Port da simulação JS, mantendo valores e física do The Cars HD web."""
    def __init__(self, car_index=0):
        self.car_index = car_index
        self.car = CAR_OPTIONS[car_index]
        self.distance = 0.0
        self.lane = 0.0
        self.speed = 0.0
        self.seconds = 0.0
        self.nitro = .68
        self.nitro_active = False
        self.item = None
        self.shield = 0.0
        self.emp = 0.0
        self.shake = 0.0
        self.message = ''
        self.message_time = 0.0
        self.best_lap = float('inf')
        self.lap_start = 0.0
        self.previous_lap = 1
        self.finished = False
        self.finished_place = 0
        self.crashes = 0
        self.frames = 0
        self.rivals = []
        self.pickups = []
        self._spawn()

    def _spawn(self):
        colors = ['#08d876','#238eff','#ffbf31','#f36c52','#d46cff','#cce9f0']
        lanes = [-.68,.55,-.25,.17,.77]
        initial = [750,1580,-430,3050,2350]
        self.rivals = [Rival(i, lanes[i], lanes[i],float(initial[i]), 3000+(i%3)*170+rand(i)*100, colors[i+1],i*2.7) for i in range(5)]
        self.pickups = []
        for i in range(33):
            z=4300+i*3940+rand(i)*750
            self.pickups.append(Pickup(mod(z,TRACK_METERS),[-.58,0.,.55,-.22,.30][i%5]))

    @property
    def lap(self):
        return min(TOTAL_LAPS, int(self.distance//TRACK_METERS)+1)

    @property
    def place(self):
        if self.finished: return self.finished_place
        return 1+sum(x.progress>self.distance for x in self.rivals)

    def announce(self, message, seconds=2.1):
        self.message = message
        self.message_time = seconds

    def use_item(self):
        if self.finished or not self.item:
            return False
        item,self.item=self.item,None
        if item == 'NITRO':
            self.nitro = clamp(self.nitro+.55,0.,1.)
            self.announce('TANQUE DE NITRO +55%')
        elif item == 'ESCUDO':
            self.shield=7.
            self.announce('ESCUDO ATIVADO')
        elif item == 'ONDA':
            self.emp=2.5
            for ai in self.rivals:
                gap=mod(ai.progress-self.distance,TRACK_METERS)
                if gap<7000:ai.stun=2.2
            self.announce('ONDA ELETROMAGNÉTICA')
        return True

    def update(self,dt,accelerate=False,brake=False,steer=0.,nitro=False):
        if self.finished:return
        dt=clamp(dt,0.,.04)
        self.seconds+=dt
        self.frames+=1
        self.message_time=max(0.,self.message_time-dt)
        speeding=self.speed>650
        if accelerate:self.speed+=2050*dt
        else:self.speed-=1120*dt
        if brake:self.speed-=3600*dt
        boosted=bool(nitro and self.nitro>0 and speeding)
        if boosted:
            self.nitro=clamp(self.nitro-dt*(.23/self.car['turbo']),0.,1.)
            self.speed+=3650*dt
        else:
            self.nitro=clamp(self.nitro+dt*.011,0.,1.)
        self.nitro_active=boosted
        self.speed=clamp(self.speed,0.,self.car['top']*(1.27 if boosted else 1))
        turn=clamp(float(steer),-1.,1.)
        handling=(.65+.55*self.car['handling'])
        self.lane+=turn*dt*1.05*handling*(.32+self.speed/self.car['top'])
        curve=slope(self.distance+PLAYER_Z)*(self.speed/self.car['top'])**2*dt*.65
        self.lane=clamp(self.lane-curve,-1.8,1.8)
        if abs(self.lane)>1.04:
            self.speed=min(self.speed,self.car['top']*.63)
            self.shake=5
        self.distance+=self.speed*dt
        self.shield=max(0.,self.shield-dt)
        self.emp=max(0.,self.emp-dt)
        self.shake=max(0.,self.shake-22*dt)
        for ai in self.rivals:
            ai.stun=max(0.,ai.stun-dt)
            ai.progress+=ai.speed*dt*(.52 if ai.stun>0 else 1.)
            ai.lane=clamp(ai.base_lane+math.sin(self.seconds*.7+ai.wobble)*.08,-.82,.82)
            if abs(ai.progress-self.distance)<220 and abs(ai.lane-self.lane)<.25 and self.speed>500 and self.shield==0:
                self.speed*=.62
                self.shake=13
                ai.stun=.48
                self.crashes+=1
                self.announce('BATIDA! CONTINUE CORRENDO',1.2)
        lap_number=int(self.distance//TRACK_METERS)
        for pickup in self.pickups:
            if pickup.collected_lap==lap_number:continue
            pickup_position=lap_number*TRACK_METERS+pickup.progress
            if abs(self.distance+PLAYER_Z-pickup_position)<180 and abs(self.lane-pickup.lane)<.34:
                pickup.collected_lap=lap_number
                if not self.item:
                    types=['NITRO','ESCUDO','ONDA']
                    self.item=types[int(rand(pickup.progress+self.frames)*3)]
                    self.announce('ITEM COLETADO • ESPAÇO PARA USAR',1.9)
        lap=int(self.distance//TRACK_METERS)+1
        if lap>self.previous_lap:
            self.best_lap=min(self.best_lap,self.seconds-self.lap_start)
            self.lap_start=self.seconds
            self.previous_lap=lap
            if lap<=TOTAL_LAPS:self.announce(f'VOLTA {lap} / {TOTAL_LAPS} • VAMOS!',2.2)
        if self.distance>=TRACK_METERS*TOTAL_LAPS:
            self.finished_place=1+sum(x.progress>self.distance for x in self.rivals)
            self.finished=True
            self.speed=0.
            self.nitro_active=False
