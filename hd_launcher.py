"""HD Launcher 1.7.0 — The Cars HD nativo integrado ao launcher + contas locais.

Use `python hd_launcher.py` or `build_windows.bat` on Windows.
The store grants bundled mini games per account; it does NOT download files.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea, QProgressBar, QCheckBox,
    QStackedWidget, QVBoxLayout, QWidget,
)
from cars_native import CarsNativeGame
from click_handlers import bind_click
from mini_games import GAME_CLASSES
from storage import CATALOG, CATALOG_BY_ID, Storage
from update_core import is_installed_windows, read_auto_update_setting, write_auto_update_setting
from update_qt import UpdateWorker

APP_VERSION = '1.7.0'
BG = '#050C15'
GREEN = '#00CE61'
YELLOW = '#FFDA23'
BLUE = '#2495FF'
BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
ASSETS = BUNDLE_DIR / 'assets'

CSS = """
QWidget { background: transparent; color: #E8F2FC; font-family: 'Segoe UI', 'Arial'; font-size: 13px; }
QMainWindow, QWidget#root, QWidget#loginRoot { background: #050C15; }
QWidget#sidebar { background: #06131D; border-right: 1px solid #18334A; }
QFrame#topbar { background: #07131F; border-bottom: 1px solid #16314C; }
QLabel#bigTitle { font-size: 27px; font-weight: 900; color: #F7FBFF; }
QLabel#section { font-size: 19px; font-weight: 900; color: #F2F7FF; }
QLabel#subsection { font-size: 15px; font-weight: 800; color: #F2F7FF; }
QLabel#muted { font-size: 12px; color: #94AAC0; }
QLabel#eyebrow { color: #FFD923; font-size: 11px; font-weight: 900; }
QLabel#gameName { font-size: 15px; font-weight: 800; }
QLabel#heroTitle { font-size: 36px; font-weight: 900; color: #FFFFFF; }
QLabel#badge { color: #05120B; background: #FFD923; border-radius: 7px; padding: 4px 8px; font-size: 10px; font-weight: 900; }
QFrame#gameCard { background: #091C2B; border: 1px solid #1B3B55; border-radius: 13px; }
QFrame#gameCard:hover { border: 1px solid #238FFF; }
QFrame#promo { background: #0A1B26; border: 1px solid #256044; border-radius: 15px; }
QFrame#promoyellow { background: #161909; border: 1px solid #806E19; border-radius: 15px; }
QFrame#settingsBox { background: #091C2B; border: 1px solid #244560; border-radius: 14px; }
QPushButton { border: 0; outline: none; font-weight: 700; }
QPushButton#navTop { background: transparent; color: #9DB6D0; padding: 15px 12px; border-radius: 8px; font-size: 13px; }
QPushButton#navTop:hover { background: #102A3D; color: white; }
QPushButton#navTop[active='true'] { background: #0D3424; color: #2CFF8C; border-bottom: 2px solid #00CE61; }
QPushButton#navSide { background: transparent; color: #A8BDCF; text-align: left; border-radius: 10px; padding: 12px; }
QPushButton#navSide:hover { color: white; background: #0E2638; }
QPushButton#navSide[active='true'] { background: #126139; color: #FFFFFF; border-left: 3px solid #FFDA23; }
QPushButton#greenBtn { background: #00BC57; color: #06140C; border: 1px solid #27E979; border-radius: 8px; padding: 10px 13px; font-weight: 900; }
QPushButton#greenBtn:hover { background: #26EB7C; }
QPushButton#blueBtn { background: #157EDB; color: white; border: 1px solid #3DA9FF; border-radius: 8px; padding: 10px 13px; font-weight: 900; }
QPushButton#blueBtn:hover { background: #299CFF; }
QPushButton#ghostBtn { color: #B8D3E8; background: #102539; border: 1px solid #23425D; border-radius: 8px; padding: 10px 13px; }
QPushButton#ghostBtn:hover { background: #16364F; }
QPushButton#linkBtn { color: #4DB4FF; background: transparent; padding: 7px; }
QPushButton#linkBtn:hover { color: #FFD923; }
QPushButton#dangerBtn { background: #192436; border: 1px solid #643A41; color: #FFC5C5; border-radius: 7px; padding: 10px; }
QPushButton#dangerBtn:hover { background: #402632; }
QLineEdit { background: #091C2B; border: 1px solid #29475F; border-radius: 9px; padding: 11px 13px; color: #F3F9FF; selection-background-color: #157EDB; }
QLineEdit:focus { border: 1px solid #269AFF; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { width: 8px; background: #071422; }
QScrollBar::handle:vertical { background: #175782; border-radius: 4px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def image(name: str) -> QPixmap:
    return QPixmap(str(ASSETS / name))


def label(text: str, name: str = '', wrap: bool = False) -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    w.setWordWrap(wrap)
    return w


def button(text: str, name: str, callback) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName(name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.clicked.connect(callback)
    return b


def refresh_style(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class FeatureArt(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pix = image('the-cars-hero.png')
        self.setMinimumHeight(252)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 13, 13)
        painter.setClipPath(clip)
        if not self.pix.isNull():
            scaled = self.pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation)
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())
        else:
            painter.fillRect(self.rect(), QColor('#0B3150'))
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(0, 10, 23, 247))
        grad.setColorAt(.36, QColor(3, 16, 30, 220))
        grad.setColorAt(.7, QColor(4, 15, 26, 10))
        grad.setColorAt(1, QColor(2, 8, 19, 30))
        painter.fillRect(self.rect(), QBrush(grad))
        painter.setClipping(False)
        painter.setPen(QColor('#246AA5'))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -2, -2), 13, 13)


class HDLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.auto_update = read_auto_update_setting(self.storage.root)
        self.update_worker = None
        self.update_manual = False
        self._ready_installer = None
        self.user_id = None
        self.username = None
        self.filter_genre = None
        self.page = 'inicio'
        self.windows = {}
        self.setWindowTitle(f'HD Launcher • v{APP_VERSION}')
        self.resize(1280, 830)
        self.setMinimumSize(1010, 700)
        ico = ASSETS / 'hd-launcher.ico'
        if ico.is_file():
            self.setWindowIcon(QIcon(str(ico)))
        self.setStyleSheet(CSS)
        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)
        self.build_login()
        self.build_shell()
        self.main_stack.setCurrentWidget(self.login_root)
        self.statusBar().setStyleSheet("QStatusBar {background:#07131F; color:#A8CCE8; border-top:1px solid #193850;}")
        self.update_progress_bar = QProgressBar(self)
        self.update_progress_bar.setFixedWidth(150)
        self.update_progress_bar.setFixedHeight(13)
        self.update_progress_bar.setTextVisible(False)
        self.update_progress_bar.setRange(0, 100)
        self.update_progress_bar.setStyleSheet("QProgressBar {border:1px solid #215C8B; background:#0B1B2B; border-radius:5px;} QProgressBar::chunk{background:#00CE61; border-radius:4px;}")
        self.statusBar().addPermanentWidget(self.update_progress_bar)
        self.update_progress_bar.hide()
        if self.auto_update and is_installed_windows():
            QTimer.singleShot(1800, self.check_for_updates)

    def check_for_updates(self, manual=False):
        """On startup and on demand; never blocks Qt's main thread."""
        if self.update_worker is not None and self.update_worker.isRunning():
            if manual:
                QMessageBox.information(self, 'Atualização', 'Já estou verificando as atualizações.')
            return
        if not is_installed_windows():
            if manual:
                QMessageBox.information(self, 'Atualização',
                                        'A verificação automática funciona no HD Launcher instalado pelo Setup.exe do Windows.')
            return
        self.update_manual = bool(manual)
        self.update_worker = UpdateWorker(APP_VERSION, self)
        self.update_worker.status.connect(self.statusBar().showMessage)
        self.update_worker.progress.connect(self.on_update_progress)
        self.update_worker.result.connect(self.on_update_result)
        self.update_worker.finished.connect(self.on_update_finished)
        self.update_worker.start()

    def on_update_finished(self):
        worker = self.update_worker
        self.update_worker = None
        if worker is not None:
            worker.deleteLater()
        if self._ready_installer:
            installer = self._ready_installer
            self._ready_installer = None
            QTimer.singleShot(0, lambda: self.install_verified_update(installer))

    def on_update_progress(self, percent: int):
        self.update_progress_bar.show()
        self.update_progress_bar.setValue(percent)

    def on_update_result(self, state: str, detail: str):
        self.update_progress_bar.hide()
        if state == 'up-to-date':
            self.statusBar().showMessage(detail, 9000)
            if self.update_manual:
                QMessageBox.information(self, 'Atualizações', detail)
        elif state == 'error':
            self.statusBar().showMessage('Atualização indisponível: ' + detail, 18000)
            if self.update_manual:
                QMessageBox.warning(self, 'Falha ao atualizar', detail)
        elif state == 'ready':
            self.statusBar().showMessage('Instalador verificado. Preparando atualização...')
            self._ready_installer = detail

    def install_verified_update(self, installer_path: str):
        if not is_installed_windows():
            return
        try:
            subprocess.Popen([
                installer_path, '/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                '/CLOSEAPPLICATIONS', '/NORESTARTAPPLICATIONS', '/SP-',
            ], cwd=str(Path(installer_path).parent), shell=False)
        except OSError as exc:
            QMessageBox.critical(self, 'Instalador não iniciado', str(exc))
            return
        QApplication.instance().quit()

    def update_setting_changed(self, checked: bool):
        self.auto_update = bool(checked)
        try:
            write_auto_update_setting(self.storage.root, self.auto_update)
        except OSError as exc:
            QMessageBox.warning(self, 'Não foi possível salvar', str(exc))

    def build_login(self):
        self.login_root = QWidget()
        self.login_root.setObjectName('loginRoot')
        row = QHBoxLayout(self.login_root)
        row.setContentsMargins(50, 45, 50, 45)
        row.addStretch(1)
        card = QFrame()
        card.setObjectName('settingsBox')
        card.setMaximumWidth(465)
        c = QVBoxLayout(card)
        c.setContentsMargins(45, 24, 45, 35)
        c.setSpacing(14)
        icon = label('')
        logo = image('hd-logo.png')
        icon.setPixmap(logo.scaled(QSize(270, 146), Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c.addWidget(icon)
        lead = label('BEM-VINDO AO SEU UNIVERSO GAMER', 'eyebrow')
        lead.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c.addWidget(lead)
        explainer = label('Entre ou crie uma conta para salvar sua biblioteca.', 'muted')
        explainer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c.addWidget(explainer)
        c.addSpacing(15)
        c.addWidget(label('NOME DE USUÁRIO', 'eyebrow'))
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText('Seu nome de jogador')
        self.input_user.setMaxLength(32)
        c.addWidget(self.input_user)
        c.addWidget(label('SENHA', 'eyebrow'))
        self.input_pass = QLineEdit()
        self.input_pass.setPlaceholderText('Mínimo de 8 caracteres')
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.returnPressed.connect(self.login)
        c.addWidget(self.input_pass)
        c.addSpacing(8)
        c.addWidget(button('▶  ENTRAR', 'greenBtn', self.login))
        c.addWidget(button('＋  CRIAR CONTA GRÁTIS', 'blueBtn', self.register))
        c.addSpacing(13)
        note = label('CONTAS LOCAIS • SEM COMPRAS • SEM CONEXÃO OBRIGATÓRIA', 'muted', True)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c.addWidget(note)
        row.addWidget(card, 6)
        row.addStretch(1)
        self.main_stack.addWidget(self.login_root)

    def build_shell(self):
        self.shell = QWidget()
        self.shell.setObjectName('root')
        root = QHBoxLayout(self.shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(205)
        left = QVBoxLayout(sidebar)
        left.setContentsMargins(14, 16, 14, 21)
        left.setSpacing(6)
        logo = label('')
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(image('hd-logo.png').scaled(QSize(176, 118), Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation))
        left.addWidget(logo)
        left.addSpacing(12)
        self.side_buttons = {}
        menu = [
            ('★  Destaques', None),
            ('▦  Todos os jogos', 'all'),
            ('◈  Arcade', 'Arcade'),
            ('✦  Casual', 'Casual'),
            ('◎  Reflexos', 'Reflexos'),
            ('🏁  Corrida', 'Corrida'),
            ('▣  Gratuitos', 'all'),
        ]
        for caption, genre in menu:
            b = button(caption, 'navSide', lambda checked=False, g=genre: self.category(g))
            left.addWidget(b)
            self.side_buttons[genre if genre is not None else 'inicio'] = b
        left.addStretch(1)
        promo = QFrame()
        promo.setObjectName('promoyellow')
        p = QVBoxLayout(promo)
        p.setContentsMargins(13, 12, 13, 12)
        p.addWidget(label('♛  HD STORE', 'eyebrow'))
        p.addWidget(label('100% GRATUITA', 'subsection'))
        p.addWidget(label('Jogos feitos para a comunidade.', 'muted', True))
        left.addWidget(promo)
        root.addWidget(sidebar)

        main = QWidget()
        maincol = QVBoxLayout(main)
        maincol.setContentsMargins(0, 0, 0, 0)
        maincol.setSpacing(0)
        self.topbar = QFrame()
        self.topbar.setObjectName('topbar')
        tl = QHBoxLayout(self.topbar)
        tl.setContentsMargins(23, 10, 24, 10)
        tl.setSpacing(8)
        self.top_buttons = {}
        for page, caption in [
            ('inicio','⌂   Início'),('biblioteca','▣   Biblioteca'),
            ('loja','🛒   Loja'),('config','⚙   Configurações'),
        ]:
            b = button(caption, 'navTop', lambda checked=False, pg=page: self.show_page(pg))
            b.setMinimumHeight(45)
            tl.addWidget(b)
            self.top_buttons[page] = b
        tl.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText('⌕  Buscar jogos...')
        self.search.setFixedWidth(195)
        self.search.textChanged.connect(self.search_changed)
        tl.addWidget(self.search)
        self.account_label = label('♛  JOGADOR', 'eyebrow')
        self.account_label.setMinimumWidth(115)
        self.account_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl.addWidget(self.account_label)
        maincol.addWidget(self.topbar)
        self.area = QStackedWidget()
        maincol.addWidget(self.area, 1)
        root.addWidget(main, 1)
        self.main_stack.addWidget(self.shell)

    def credentials(self):
        name = self.input_user.text().strip()
        password = self.input_pass.text()
        try:
            self.storage.validate_credentials(name, password)
        except ValueError as exc:
            QMessageBox.warning(self, 'Dados inválidos', str(exc))
            return None
        return name, password

    def login(self):
        data = self.credentials()
        if data is None:
            return
        try:
            account = self.storage.login(*data)
        except Exception as exc:
            QMessageBox.critical(self, 'Falha no banco de dados', str(exc))
            return
        if account is None:
            QMessageBox.warning(self, 'Login não realizado', 'Usuário ou senha incorretos.')
            return
        self.enter(*account)

    def register(self):
        data = self.credentials()
        if data is None:
            return
        try:
            account = self.storage.register(*data)
        except ValueError as exc:
            QMessageBox.warning(self, 'Conta não criada', str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, 'Erro ao criar a conta', str(exc))
            return
        self.enter(*account)

    def enter(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.input_pass.clear()
        self.account_label.setText('♛  ' + username[:16])
        self.filter_genre = None
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.main_stack.setCurrentWidget(self.shell)
        self.show_page('inicio')

    def logout(self):
        if self.page == 'corrida':
            self.show_page('biblioteca')
        self.user_id = self.username = None
        self.input_user.clear()
        self.input_pass.clear()
        self.main_stack.setCurrentWidget(self.login_root)

    def category(self, genre):
        self.filter_genre = genre
        if genre is None:
            self.show_page('inicio')
        else:
            self.show_page('loja')

    def search_changed(self, *_):
        if self.user_id:
            self.show_page('loja' if self.page != 'biblioteca' else 'biblioteca')

    def show_page(self, page):
        if not self.user_id:
            return
        self.page = page
        for pg,b in self.top_buttons.items():
            b.setProperty('active', 'true' if pg == page else 'false')
            refresh_style(b)
        selected = 'inicio' if page == 'inicio' else self.filter_genre
        for k,b in self.side_buttons.items():
            b.setProperty('active', 'true' if page in ('inicio','loja') and k == selected else 'false')
            refresh_style(b)
        current = self.area.currentWidget()
        if current:
            self.area.removeWidget(current)
            current.deleteLater()
        contents = {'inicio':self.home_page, 'loja':self.store_page,
                    'biblioteca':self.library_page, 'config':self.settings_page,
                    'corrida': self.cars_page}[page]()
        self.area.addWidget(contents)
        self.area.setCurrentWidget(contents)
        if page == 'corrida':
            self.cars_widget.setFocus()

    def cars_page(self):
        """Tela jogável nativa dentro do próprio HD Launcher, sem navegador."""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(15, 10, 15, 13)
        outer.setSpacing(6)
        bar = QHBoxLayout()
        bar.addWidget(label('🏁   THE CARS HD  •  EDIÇÃO NATIVA PORTO NEON', 'eyebrow'))
        bar.addStretch()
        bar.addWidget(button('←   VOLTAR À BIBLIOTECA', 'ghostBtn',
                             lambda: self.show_page('biblioteca')))
        outer.addLayout(bar)
        self.cars_widget = CarsNativeGame(ASSETS / 'the-cars-hero.png', page)
        self.cars_widget.exit_requested.connect(lambda: self.show_page('biblioteca'))
        outer.addWidget(self.cars_widget, 1)
        return page

    def scroll_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        v = QVBoxLayout(body)
        v.setContentsMargins(27, 22, 27, 32)
        v.setSpacing(20)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(body)
        return scroll, v

    def section_heading(self, title, click_title=None, callback=None):
        r = QHBoxLayout()
        r.addWidget(label(title, 'section'))
        r.addStretch(1)
        if click_title and callback:
            r.addWidget(button(click_title + '   →', 'linkBtn', callback))
        return r

    def home_page(self):
        page, v = self.scroll_page()
        row = QHBoxLayout()
        row.setSpacing(15)
        hero = FeatureArt()
        hero.setMinimumWidth(450)
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(27, 25, 18, 24)
        hl.setSpacing(9)
        hl.addWidget(label('✦  DESTAQUE  /  HD ORIGINAL', 'eyebrow'))
        hl.addSpacing(8)
        hl.addWidget(label('THE CARS\nHD', 'heroTitle'))
        hl.addWidget(label('Corra pelas ruas de Porto Neon, use itens e nitro!', 'muted'))
        hl.addStretch(1)
        play = button('▶   JOGAR AGORA', 'greenBtn', lambda: self.obtain_or_play('the-cars-hd'))
        play.setFixedWidth(175)
        hl.addWidget(play)
        row.addWidget(hero, 5)
        info = QVBoxLayout()
        info.setSpacing(12)
        block = QFrame()
        block.setObjectName('promo')
        b = QVBoxLayout(block)
        b.setContentsMargins(15, 15, 15, 14)
        b.addWidget(label('♛  NOSSOS JOGOS,', 'eyebrow'))
        b.addWidget(label('SUA DIVERSÃO!', 'subsection'))
        b.addWidget(label('Explore aventuras criadas para o HD Launcher.', 'muted', True))
        b.addStretch(1)
        info.addWidget(block, 2)
        block2 = QFrame()
        block2.setObjectName('promoyellow')
        t = QVBoxLayout(block2)
        t.setContentsMargins(14, 13, 14, 12)
        t.addWidget(label('★  LOJA GRATUITA', 'eyebrow'))
        t.addWidget(button('VER JOGOS   →', 'ghostBtn', lambda:self.show_page('loja')))
        info.addWidget(block2, 1)
        row.addLayout(info, 2)
        v.addLayout(row)
        v.addLayout(self.section_heading('★   Jogos em Destaque', 'Ver todos', lambda:self.show_page('loja')))
        v.addLayout(self.catalog_grid(CATALOG))
        v.addSpacing(2)
        v.addLayout(self.section_heading('✦   Novidades do HD Launcher'))
        bottom = QFrame()
        bottom.setObjectName('promo')
        b = QHBoxLayout(bottom)
        b.setContentsMargins(18, 19, 18, 19)
        bl = QVBoxLayout()
        bl.addWidget(label('4 JOGOS ORIGINAIS • THE CARS HD CHEGOU!', 'eyebrow'))
        bl.addWidget(label('Novo jogo de corrida! Todos grátis e prontos para sua biblioteca.', 'muted'))
        b.addLayout(bl)
        b.addStretch(1)
        b.addWidget(button('EXPLORAR LOJA →', 'blueBtn',lambda:self.show_page('loja')))
        v.addWidget(bottom)
        return page

    def visible_catalog(self):
        games = list(CATALOG)
        if self.filter_genre not in (None, 'all'):
            games = [g for g in games if g['genre'] == self.filter_genre]
        q = self.search.text().strip().casefold()
        if q:
            games = [g for g in games if q in g['title'].casefold() or q in g['genre'].casefold()]
        return games

    def store_page(self):
        page, v = self.scroll_page()
        v.addWidget(label('HD STORE   /   JOGOS GRÁTIS', 'eyebrow'))
        v.addWidget(label('Descubra seu próximo jogo', 'bigTitle'))
        v.addWidget(label('Escolha um jogo original e adicione à sua biblioteca. Tudo funciona offline.', 'muted'))
        tabs = QHBoxLayout()
        tabs.setSpacing(9)
        for text, genre in [('Todos', 'all'), ('Arcade','Arcade'), ('Casual','Casual'), ('Reflexos','Reflexos'), ('Corrida','Corrida')]:
            b = button(text, 'greenBtn' if self.filter_genre == genre else 'ghostBtn',
                       lambda checked=False, g=genre:self.category(g))
            tabs.addWidget(b)
        tabs.addStretch(1)
        v.addLayout(tabs)
        games = self.visible_catalog()
        v.addLayout(self.section_heading(f'★   {len(games)} jogo(s) disponíveis'))
        if games:
            v.addLayout(self.catalog_grid(games))
        else:
            v.addWidget(label('Nenhum jogo nessa categoria ou busca. Experimente outro filtro.', 'muted'))
        tip = QFrame()
        tip.setObjectName('promo')
        t = QVBoxLayout(tip)
        t.addWidget(label('✓   GRATUITOS DE VERDADE', 'eyebrow'))
        t.addWidget(label('Os quatro jogos já vêm no programa. “Obter grátis” libera o jogo para sua conta local. The Cars HD roda diretamente no launcher, sem navegador e sem internet.', 'muted', True))
        v.addWidget(tip)
        return page

    def catalog_grid(self, games):
        row = QGridLayout()
        row.setHorizontalSpacing(15)
        row.setVerticalSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        installed = self.storage.installed_ids(self.user_id)
        for idx, game in enumerate(games):
            row.addWidget(self.game_card(game, game['id'] in installed), idx // 3, idx % 3,
                          Qt.AlignmentFlag.AlignTop)
        return row

    def game_card(self, game, installed=False, local=False):
        card = QFrame()
        card.setObjectName('gameCard')
        card.setFixedWidth(239)
        c = QVBoxLayout(card)
        c.setContentsMargins(9, 9, 9, 11)
        c.setSpacing(7)
        art = QLabel()
        art.setFixedSize(219, 140)
        if local:
            art.setText('◈\nJOGO LOCAL')
            art.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art.setStyleSheet('background:#0D3450;color:#FFDA23;border-radius:8px;font-size:24px;font-weight:900;')
        else:
            pm = image(game['id']+'.png')
            art.setPixmap(pm.scaled(219, 140, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                    Qt.TransformationMode.SmoothTransformation))
            art.setStyleSheet('background:#0D2338;border-radius:8px;')
        c.addWidget(art)
        headline = QHBoxLayout()
        name = label(game['title'], 'gameName')
        name.setToolTip(game['title'])
        name.setMaximumWidth(155)
        headline.addWidget(name)
        headline.addStretch(1)
        if not local:
            headline.addWidget(label('GRÁTIS','badge'))
        c.addLayout(headline)
        c.addWidget(label(game.get('genre','No computador'), 'muted'))
        c.addWidget(label(game.get('description','Jogo adicionado pelo usuário.'), 'muted', True))
        c.addStretch(1)
        if local:
            c.addWidget(button('▶  JOGAR', 'blueBtn', bind_click(self.launch_executable, game['path'])))
            c.addWidget(button('REMOVER DA BIBLIOTECA', 'dangerBtn', bind_click(self.remove_local, game['id'])))
        elif installed:
            c.addWidget(button('▶  JOGAR', 'blueBtn', bind_click(self.play_builtin, game['id'])))
            if self.page == 'biblioteca':
                c.addWidget(button('REMOVER DA BIBLIOTECA', 'dangerBtn', bind_click(self.remove_builtin, game['id'])))
        else:
            c.addWidget(button('＋  OBTER GRÁTIS', 'greenBtn', bind_click(self.obtain_game, game['id'])))
        return card

    def obtain_game(self, game_id):
        try:
            self.storage.install_free_game(self.user_id, game_id)
        except Exception as exc:
            QMessageBox.critical(self,'Não foi possível adicionar',str(exc))
            return
        self.show_page(self.page)

    def obtain_or_play(self, game_id):
        if game_id not in self.storage.installed_ids(self.user_id):
            try:
                self.storage.install_free_game(self.user_id, game_id)
            except Exception as exc:
                QMessageBox.critical(self,'Erro ao adicionar',str(exc))
                return
        self.play_builtin(game_id)

    def play_builtin(self, game_id):
        if game_id not in self.storage.installed_ids(self.user_id):
            QMessageBox.information(self,'Adicione primeiro','Obtenha o jogo grátis na loja.')
            return
        if game_id == 'the-cars-hd':
            self.show_page('corrida')
            return
        cls = GAME_CLASSES.get(game_id)
        if cls is None:
            QMessageBox.warning(self,'Jogo indisponível','Este jogo não está incluído nesta versão.')
            return
        win = self.windows.get(game_id)
        if win is None or not win.isVisible():
            win = cls()
            self.windows[game_id] = win
            win.destroyed.connect(lambda _=None, i=game_id:self.windows.pop(i,None))
            win.show()
        else:
            win.raise_()
            win.activateWindow()

    def library_page(self):
        page, v = self.scroll_page()
        v.addWidget(label('SUA COLEÇÃO   /   BIBLIOTECA', 'eyebrow'))
        v.addWidget(label('Meus jogos', 'bigTitle'))
        bar = QHBoxLayout()
        bar.addWidget(label('Jogos liberados na loja + programas .exe que você adicionou.', 'muted'))
        bar.addStretch(1)
        bar.addWidget(button('＋  ADICIONAR JOGO .EXE', 'greenBtn',self.add_local))
        v.addLayout(bar)
        installed = self.storage.installed_ids(self.user_id)
        local = self.storage.local_games(self.user_id)
        q = self.search.text().strip().casefold()
        entries = [g for g in CATALOG if g['id'] in installed and q in g['title'].casefold()]
        entries += [dict(id=g['id'], title=g['title'], path=g['path'],genre='Jogo local')
                    for g in local if q in g['title'].casefold()]
        if not entries:
            promo = QFrame()
            promo.setObjectName('promo')
            inner = QVBoxLayout(promo)
            inner.setContentsMargins(25, 25, 25, 25)
            inner.addWidget(label('Sua biblioteca ainda está vazia.', 'subsection'))
            inner.addWidget(label('Acesse a loja e clique em “Obter grátis” para jogar sem pagar nada.', 'muted'))
            inner.addWidget(button('VER LOJA →','greenBtn',lambda:self.show_page('loja')))
            v.addWidget(promo)
        else:
            v.addLayout(self.section_heading(f'▣   {len(entries)} jogo(s) na biblioteca'))
            grid = QGridLayout()
            grid.setSpacing(15)
            for idx,g in enumerate(entries):
                islocal = 'path' in g
                grid.addWidget(self.game_card(g, installed=True, local=islocal), idx // 3, idx % 3)
            v.addLayout(grid)
        return page

    def add_local(self):
        path, _ = QFileDialog.getOpenFileName(self,'Selecione o .exe do jogo',str(Path.home()),
                                              'Executáveis do Windows (*.exe)')
        if not path: return
        try:
            success = self.storage.add_local_game(self.user_id, path)
        except ValueError as exc:
            QMessageBox.warning(self,'Arquivo inválido',str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self,'Erro ao salvar',str(exc))
            return
        if not success:
            QMessageBox.information(self,'Já adicionado','Este jogo já está na sua biblioteca.')
        self.show_page('biblioteca')

    def launch_executable(self, path):
        exe = Path(path)
        if not exe.is_file():
            QMessageBox.warning(self,'Jogo não encontrado',f'O arquivo foi movido ou excluído:\n{path}')
            return
        try:
            subprocess.Popen([str(exe)], cwd=str(exe.parent), shell=False)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self,'Falha ao iniciar',str(exc))

    def remove_local(self, game_id):
        if QMessageBox.question(self,'Remover jogo','Remover o jogo da biblioteca?\nO arquivo original não será apagado.',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.storage.remove_local_game(self.user_id, game_id)
        self.show_page('biblioteca')

    def remove_builtin(self, game_id):
        if QMessageBox.question(self,'Remover jogo','Remover da sua biblioteca? Ele continuará disponível grátis na loja.',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.storage.uninstall_free_game(self.user_id,game_id)
        self.show_page('biblioteca')

    def settings_page(self):
        page, v = self.scroll_page()
        v.addWidget(label('SUA CONTA   /   CONFIGURAÇÕES', 'eyebrow'))
        v.addWidget(label('Configurações', 'bigTitle'))
        for heading, detail in [
            ('♛  Conta local', f'Logado como {self.username}. Seus jogos são salvos somente neste PC.'),
            ('▣  Biblioteca e dados', f'Dados em: {self.storage.database}'),
            ('★  HD Store', 'Jogue grátis: quatro jogos inclusos, incluindo The Cars HD nativo com pista e regras da versão web v0.1.'),
            ('ⓘ  Versão do aplicativo', f'HD Launcher {APP_VERSION} • Loja offline • Verde, amarelo e azul'),
        ]:
            frame = QFrame()
            frame.setObjectName('settingsBox')
            lay = QVBoxLayout(frame)
            lay.setContentsMargins(20, 17, 20, 17)
            lay.addWidget(label(heading, 'subsection'))
            lay.addWidget(label(detail, 'muted', True))
            v.addWidget(frame)
        updates = QFrame()
        updates.setObjectName('settingsBox')
        u = QVBoxLayout(updates)
        u.setContentsMargins(20, 16, 20, 16)
        u.addWidget(label('↻  Atualizações automáticas', 'subsection'))
        u.addWidget(label('Ao abrir, procura atualizações no GitHub, baixa o instalador verificado e instala em segundo plano.', 'muted', True))
        checkbox = QCheckBox('Atualizar automaticamente ao iniciar o HD Launcher')
        checkbox.setChecked(self.auto_update)
        checkbox.toggled.connect(self.update_setting_changed)
        u.addWidget(checkbox)
        u.addWidget(button('↻  VERIFICAR ATUALIZAÇÕES AGORA', 'blueBtn',
                           lambda checked=False: self.check_for_updates(manual=True)))
        v.addWidget(updates)
        v.addWidget(button('SAIR DA MINHA CONTA', 'dangerBtn',self.logout))
        return page


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('HD Launcher')
    app.setStyle('Fusion')
    launcher = HDLauncher()
    launcher.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
