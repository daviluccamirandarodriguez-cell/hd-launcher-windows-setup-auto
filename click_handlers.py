"""Adaptadores para sinais Qt clicked(bool), preservando IDs de jogos.

QPushButton.clicked costuma enviar ``checked`` (bool) para o callback.
Um lambda como ``lambda game_id=...: ...`` recebe esse bool no lugar do ID.
"""
from __future__ import annotations
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def bind_click(action: Callable[[T], object], game_id: T) -> Callable[[bool], object]:
    """Vincula o ID real e ignora o ``checked`` enviado pelo Qt."""
    def handle_click(_checked: bool = False) -> object:
        return action(game_id)

    return handle_click
