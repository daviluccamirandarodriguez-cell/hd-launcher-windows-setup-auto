"""Database regression tests; standard-library only (no PySide6 required)."""
import tempfile
import unittest
from pathlib import Path
from storage import Storage

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Storage(Path(self.tmp.name))
    def tearDown(self):
        self.tmp.cleanup()

    def test_accounts_games_isolated_and_persistent(self):
        a, _ = self.store.register('Jogador1', 'senha segura 1')
        b, _ = self.store.register('Jogador2', 'senha segura 2')
        self.assertEqual(self.store.login('jogador1', 'senha segura 1'), (a,'Jogador1'))
        self.assertIsNone(self.store.login('Jogador1', 'senha incorreta'))
        self.store.install_free_game(a, 'neon-dodge')
        self.store.install_free_game(a, 'neon-dodge')
        self.assertEqual(self.store.installed_ids(a), {'neon-dodge'})
        self.assertEqual(self.store.installed_ids(b), set())
        db2 = Storage(Path(self.tmp.name))
        self.assertEqual(db2.installed_ids(a), {'neon-dodge'})
        self.store.uninstall_free_game(a, 'neon-dodge')
        self.assertEqual(self.store.installed_ids(a), set())

    def test_local_game_isolation(self):
        a, _ = self.store.register('JogadorA', 'senha segura A')
        b, _ = self.store.register('JogadorB', 'senha segura B')
        exe = Path(self.tmp.name) / 'meu_jogo.exe'
        exe.write_bytes(b'fake exe only for database tests')
        self.assertTrue(self.store.add_local_game(a,str(exe)))
        self.assertFalse(self.store.add_local_game(a,str(exe)))
        self.assertEqual(len(self.store.local_games(a)),1)
        self.assertEqual(self.store.local_games(b),[])
        self.store.remove_local_game(b,self.store.local_games(a)[0]['id'])
        self.assertEqual(len(self.store.local_games(a)),1)
        self.store.remove_local_game(a,self.store.local_games(a)[0]['id'])
        self.assertEqual(self.store.local_games(a),[])

    def test_username_collision(self):
        self.store.register('Jogador1', 'senha segura 1')
        with self.assertRaises(ValueError):
            self.store.register('jogador1','senha segura 2')
        with self.assertRaises(ValueError):
            self.store.install_free_game('does-not-exist','fake-game')

if __name__ == '__main__': unittest.main()
