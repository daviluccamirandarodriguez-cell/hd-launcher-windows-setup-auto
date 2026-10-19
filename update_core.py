"""Windows self-update: public GitHub Releases metadata + verified installer.

Pure Python, no Qt. A release must have a SHA-256 digest supplied by GitHub.
Never execute an installer if that checksum is absent or does not match.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

REPO = "daviluccamirandarodriguez-cell/hd-launcher-windows-setup"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
USER_AGENT = "HDLauncher-Updater/1.7 (public-releases)"
MAX_DOWNLOAD_BYTES = 450 * 1024 * 1024


@dataclass(frozen=True)
class Update:
    version: str
    url: str
    digest: str
    size: int
    filename: str


def version_tuple(value: str) -> tuple[int, int, int]:
    """Accept v1.7.0 and legacy v.1.6.0; reject malformed tags."""
    m = re.fullmatch(r"v?\.?([0-9]+)\.([0-9]+)\.([0-9]+)", value.strip(), re.I)
    if not m:
        raise ValueError(f"Versão inválida: {value!r}")
    return tuple(int(part) for part in m.groups())


def parse_release(data: dict, installed_version: str) -> Update | None:
    """Select exactly the expected Windows Setup.exe from trusted public release."""
    if data.get("draft") or data.get("prerelease"):
        return None
    tag = data.get("tag_name") or ""
    try:
        version = version_tuple(tag)
    except ValueError:
        return None
    if version <= version_tuple(installed_version):
        return None
    normalized = ".".join(str(n) for n in version)
    expected = f"HDLauncher-Setup-v{normalized}.exe"
    for asset in data.get("assets", []):
        if not isinstance(asset, dict) or asset.get("name") != expected:
            continue
        size = asset.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= MAX_DOWNLOAD_BYTES:
            raise ValueError("O instalador publicado tem tamanho inválido.")
        checksum = asset.get("digest") or ""
        if not re.fullmatch(r"sha256:[a-fA-F0-9]{64}", checksum):
            raise ValueError("A Release não forneceu SHA-256. Atualização cancelada por segurança.")
        url = asset.get("browser_download_url") or ""
        path = urlparse(url)
        expected_path = f"/{REPO}/releases/download/{tag}/{expected}"
        if (path.scheme != "https" or path.netloc.lower() != "github.com"
                or unquote(path.path) != expected_path or path.username or path.password
                or path.query or path.fragment):
            raise ValueError("O endereço do instalador não é o esperado no GitHub.")
        return Update(normalized, url, checksum.split(":", 1)[1].lower(), size, expected)
    raise ValueError("A Release mais recente não contém um Setup.exe compatível.")


def latest_update(installed_version: str) -> Update | None:
    request = Request(API_URL, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "Cache-Control": "no-cache",
    })
    with urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise OSError("Resposta inesperada do GitHub.")
        data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ValueError("Resposta muito grande do servidor.")
    return parse_release(json.loads(data), installed_version)


def download_verified(update: Update, progress: Callable[[int], None] | None = None) -> Path:
    """Download in chunks and hash the bytes, never running mismatched binaries."""
    directory = Path(tempfile.gettempdir()) / "HDLauncherUpdates"
    directory.mkdir(parents=True, exist_ok=True)
    final = directory / update.filename
    # A previous verified cached file is safe to use if its hash is identical.
    if final.is_file():
        hasher = hashlib.sha256()
        with final.open("rb") as old:
            for block in iter(lambda: old.read(1024 * 1024), b""):
                hasher.update(block)
        if final.stat().st_size == update.size and hasher.hexdigest() == update.digest:
            if progress:
                progress(100)
            return final
    fd, tmp_name = tempfile.mkstemp(prefix="download-", suffix=".part", dir=directory)
    digest = hashlib.sha256()
    received = 0
    try:
        request = Request(update.url, headers={"User-Agent": USER_AGENT})
        with os.fdopen(fd, "wb") as dst, urlopen(request, timeout=35) as source:
            while True:
                block = source.read(256 * 1024)
                if not block:
                    break
                received += len(block)
                if received > MAX_DOWNLOAD_BYTES or received > update.size:
                    raise ValueError("Arquivo maior que o informado pela Release.")
                dst.write(block)
                digest.update(block)
                if progress:
                    progress(min(99, int(received * 100 / update.size)))
        if received != update.size or digest.hexdigest() != update.digest:
            raise ValueError("Falha na verificação SHA-256. O instalador foi descartado.")
        os.replace(tmp_name, final)
        if progress:
            progress(100)
        return final
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def is_installed_windows() -> bool:
    """Skip automatic replacement from source trees and unpacked builds."""
    import sys
    exe = Path(sys.executable)
    return bool(sys.platform == "win32" and getattr(sys, "frozen", False)
                and (exe.parent / "unins000.exe").is_file())


def read_auto_update_setting(data_dir: Path) -> bool:
    """Default ON; an invalid configuration must never crash startup."""
    path = data_dir / "update-settings.json"
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
        return content.get("auto_update", True) is not False
    except (OSError, ValueError, AttributeError):
        return True


def write_auto_update_setting(data_dir: Path, enabled: bool) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "update-settings.json"
    fd, tmp = tempfile.mkstemp(dir=data_dir, prefix="update-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"auto_update": bool(enabled)}, f)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
