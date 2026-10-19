"""Qt worker for background release checks and downloads (keeps UI responsive)."""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from update_core import download_verified, latest_update


class UpdateWorker(QThread):
    status = Signal(str)
    progress = Signal(int)
    result = Signal(str, str)  # ready/up-to-date/error, installer path/message

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self):
        try:
            self.status.emit("Procurando uma versão nova...")
            update = latest_update(self.current_version)
            if update is None:
                self.result.emit("up-to-date", "O HD Launcher está atualizado.")
                return
            self.status.emit(f"Baixando HD Launcher {update.version}...")
            installer = download_verified(update, self.progress.emit)
            self.result.emit("ready", str(installer))
        except Exception as exc:
            self.result.emit("error", str(exc))
