"""Three bundled offline mini games, using the same PySide6 dependency as HD Launcher."""
from __future__ import annotations

import random
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QKeyEvent, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

BG = QColor("#07111C")
GRID = QColor("#122439")
GREEN = QColor("#00D769")
YELLOW = QColor("#FFD600")
BLUE = QColor("#398BFF")
WHITE = QColor("#F4FAFF")


class GameWindow(QWidget):
    def __init__(self, name: str):
        super().__init__()
        self.setWindowTitle(f"{name} • HD Launcher")
        self.resize(760, 580)
        self.setMinimumSize(580, 440)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.reset()
        self.timer.start(16)

    def reset(self):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError

    def paint_background(self, painter):
        painter.fillRect(self.rect(), BG)
        painter.setPen(QPen(GRID, 1))
        for x in range(0, self.width(), 42):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 42):
            painter.drawLine(0, y, self.width(), y)

    def draw_text(self, painter, title, instructions, score, secondary):
        painter.setPen(WHITE)
        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        painter.drawText(25, 42, title)
        painter.setPen(QColor("#A6CBFA"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(25, 69, instructions)
        painter.setPen(YELLOW)
        painter.drawText(self.width() - 170, 40, score)
        painter.drawText(self.width() - 170, 62, secondary)

    def draw_gameover(self, painter, score: int):
        painter.fillRect(self.rect(), QColor(2, 8, 18, 225))
        painter.setPen(WHITE)
        painter.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        painter.drawText(self.rect().adjusted(0, -55, 0, 0), Qt.AlignmentFlag.AlignCenter, "FIM DE JOGO")
        painter.setPen(YELLOW)
        painter.setFont(QFont("Segoe UI", 15))
        painter.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignCenter,
                         f"{score} pontos • R ou ESPAÇO para reiniciar")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_R, Qt.Key.Key_Space) and self.game_over:
            self.reset()
        else:
            super().keyPressEvent(event)


class NeonDodge(GameWindow):
    def __init__(self):
        super().__init__("Neon Dodge")

    def reset(self):
        self.player_x = self.width() / 2
        self.blocks = []
        self.frame = 0
        self.score = 0
        self.lives = 3
        self.invulnerable = 0
        self.left = self.right = False
        self.game_over = False
        self.update()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self.left = True
        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self.right = True
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_A): self.left = False
            if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_D): self.right = False
        super().keyReleaseEvent(event)

    def step(self):
        if self.game_over: return
        self.frame += 1
        self.player_x = min(max(self.player_x + (int(self.right) - int(self.left))*7, 28), self.width()-28)
        interval = max(19, 42 - self.score // 5)
        if self.frame % interval == 0:
            s = random.randint(23, 52)
            self.blocks.append([random.randint(18, max(18, self.width()-s-18)), -s, s, 3.5 + min(self.score/22,5)])
        remaining = []
        for obstacle in self.blocks:
            obstacle[1] += obstacle[3]
            x,y,s,_ = obstacle
            collides = (x < self.player_x+18 and x+s > self.player_x-18 and
                        y < self.height()-57 and y+s > self.height()-98)
            if collides and not self.invulnerable:
                self.lives -= 1
                self.invulnerable = 75
                if not self.lives: self.game_over=True
            if y <= self.height(): remaining.append(obstacle)
            else: self.score += 1
        self.blocks = remaining
        self.invulnerable = max(0, self.invulnerable-1)
        self.update()

    def paintEvent(self, event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.paint_background(p)
        self.draw_text(p,"NEON DODGE","← → ou A / D: mover • Fuja dos blocos",f"PONTOS {self.score}",f"VIDAS {self.lives}")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(YELLOW)
        for x,y,s,_ in self.blocks: p.drawRoundedRect(QRectF(x,y,s,s),6,6)
        if self.invulnerable % 8 < 4:
            x=self.player_x; y=self.height()-76
            p.setBrush(GREEN)
            p.drawPolygon(QPolygonF([QPointF(x,y-22),QPointF(x-21,y+21),QPointF(x+21,y+21)]))
            p.setBrush(BLUE)
            p.drawEllipse(QRectF(x-5,y,10,10))
        if self.game_over: self.draw_gameover(p,self.score)
        p.end()


class StarCatcher(GameWindow):
    def __init__(self):
        super().__init__("Caça-Estrelas")

    def reset(self):
        self.x=self.width()/2
        self.drops=[]
        self.frame=0
        self.score=0
        self.lives=3
        self.left=self.right=False
        self.game_over=False
        self.update()

    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Left,Qt.Key.Key_A): self.left=True
        elif event.key() in (Qt.Key.Key_Right,Qt.Key.Key_D): self.right=True
        else: super().keyPressEvent(event)

    def keyReleaseEvent(self,event):
        if not event.isAutoRepeat():
            if event.key() in (Qt.Key.Key_Left,Qt.Key.Key_A): self.left=False
            if event.key() in (Qt.Key.Key_Right,Qt.Key.Key_D): self.right=False
        super().keyReleaseEvent(event)

    def step(self):
        if self.game_over: return
        self.frame += 1
        self.x = min(max(self.x + (int(self.right)-int(self.left))*8,40),self.width()-40)
        if self.frame % 24 == 0:
            self.drops.append([random.randint(24,max(24,self.width()-24)), -10,random.random()<.22])
        remaining=[]
        for drop in self.drops:
            drop[1]+=4.0+min(self.score/32,5)
            x,y,bomb=drop
            if abs(x-self.x)<42 and self.height()-81 <= y <= self.height()-44:
                if bomb:
                    self.lives -= 1
                    if self.lives == 0:self.game_over=True
                else:self.score += 1
            elif y <= self.height():remaining.append(drop)
        self.drops=remaining
        self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.paint_background(p)
        self.draw_text(p,"CAÇA-ESTRELAS","← → ou A / D: pegar estrelas amarelas e evitar bombas azuis",f"ESTRELAS {self.score}",f"VIDAS {self.lives}")
        p.setPen(Qt.PenStyle.NoPen)
        for x,y,bomb in self.drops:
            p.setBrush(BLUE if bomb else YELLOW)
            p.drawEllipse(QRectF(x-13,y-13,26,26))
        p.setBrush(GREEN)
        p.drawRoundedRect(QRectF(self.x-42,self.height()-61,84,21),8,8)
        if self.game_over:self.draw_gameover(p,self.score)
        p.end()


class ReflexRush(GameWindow):
    def __init__(self):
        super().__init__("Reflexo Turbo")

    def reset(self):
        self.frames=0
        self.score=0
        self.game_over=False
        self.target=self.new_target()
        self.update()

    def new_target(self):
        return QPointF(random.randint(56,max(56,self.width()-56)),random.randint(140,max(140,self.height()-55)))

    def step(self):
        if self.game_over:return
        self.frames += 1
        if self.frames >= 60*30:
            self.game_over=True
        elif self.frames % 95 == 0:
            self.target=self.new_target()
        self.update()

    def mousePressEvent(self,event:QMouseEvent):
        if not self.game_over and event.button()==Qt.MouseButton.LeftButton:
            dx=event.position().x()-self.target.x()
            dy=event.position().y()-self.target.y()
            if dx*dx+dy*dy < 35*35:
                self.score += 1
                self.target=self.new_target()
                self.update()
        super().mousePressEvent(event)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.paint_background(p)
        self.draw_text(p,"REFLEXO TURBO","Clique nos círculos para pontuar • 30 segundos",f"ACERTOS {self.score}",f"TEMPO {max(0,30-self.frames//60)}s")
        if not self.game_over:
            p.setPen(QPen(BLUE,5));p.setBrush(YELLOW)
            p.drawEllipse(self.target,31,31)
            p.setBrush(GREEN);p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(self.target,11,11)
        else:self.draw_gameover(p,self.score)
        p.end()


GAME_CLASSES={"neon-dodge":NeonDodge,"star-catcher":StarCatcher,"reflex-rush":ReflexRush}
