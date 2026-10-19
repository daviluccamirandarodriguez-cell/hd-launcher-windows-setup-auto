"""Regressão: Qt.clicked(bool) jamais substitui o ID do jogo.

Estes testes não dependem de PySide6 e cobrem o adaptador usado nos cards.
"""
import unittest
from pathlib import Path
from click_handlers import bind_click
from storage import CATALOG, Storage
import tempfile


class ClickHandlerTests(unittest.TestCase):
    def test_signal_checked_does_not_replace_catalog_id(self):
        for game in CATALOG:
            received = []
            cb = bind_click(received.append, game['id'])
            cb(True)
            cb(False)
            cb()
            self.assertEqual(received, [game['id']] * 3)

    def test_store_actions_from_buttons_install_all_games(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Storage(Path(tmp))
            user, _ = store.register('JogadorTeste', 'senha segura 123')
            for game in CATALOG:
                cb = bind_click(lambda ident: store.install_free_game(user, ident), game['id'])
                cb(False)  # exato parâmetro que Qt.clicked pode enviar
                self.assertIn(game['id'], store.installed_ids(user))
            self.assertEqual(store.installed_ids(user), {g['id'] for g in CATALOG})

    def test_remove_and_play_actions_keep_id(self):
        seen=[]
        game_id = CATALOG[0]['id']
        for action in ('play','remove'):
            cb = bind_click(lambda ident, a=action: seen.append((a, ident)), game_id)
            cb(False)
        self.assertEqual(seen, [('play',game_id),('remove',game_id)])

    def test_local_game_path_is_not_replaced(self):
        path=r'C:\Jogos\Jogo Exemplo\game.exe'
        seen=[]
        bind_click(seen.append, path)(False)
        self.assertEqual(seen, [path])

if __name__ == '__main__':
    unittest.main()
