"""Offline regression tests: release validation, version comparison, integrity and settings."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import update_core as u


class FakeResponse(io.BytesIO):
    status = 200


def release(version='1.8.0', payload=b'WIN-INSTALLER'):
    name = f'HDLauncher-Setup-v{version}.exe'
    return {
        'tag_name': f'v{version}', 'draft': False, 'prerelease': False,
        'assets': [{
            'name': name,
            'browser_download_url': f'https://github.com/{u.REPO}/releases/download/v{version}/{name}',
            'size': len(payload),
            'digest': 'sha256:' + hashlib.sha256(payload).hexdigest(),
        }],
    }


class UpdaterTests(unittest.TestCase):
    def test_version_parsing_supports_legacy_tag(self):
        self.assertEqual(u.version_tuple('v.1.6.0'), (1, 6, 0))
        self.assertEqual(u.version_tuple('v1.7.0'), (1, 7, 0))
        self.assertEqual(u.version_tuple('1.7.0'), (1, 7, 0))

    def test_bad_version_rejected(self):
        for value in ['1.7', 'v1.7.0-beta', 'v1.7.0.exe']:
            with self.assertRaises(ValueError):
                u.version_tuple(value)

    def test_no_update_if_older_or_same(self):
        self.assertIsNone(u.parse_release(release('1.6.0'), '1.7.0'))
        self.assertIsNone(u.parse_release(release('1.7.0'), '1.7.0'))

    def test_updater_accepts_exact_newer_asset(self):
        update = u.parse_release(release('1.8.0'), '1.7.0')
        self.assertEqual(update.version, '1.8.0')
        self.assertTrue(update.url.endswith('/HDLauncher-Setup-v1.8.0.exe'))

    def test_rejects_draft_or_prerelease(self):
        for flag in ['draft', 'prerelease']:
            entry = release()
            entry[flag] = True
            self.assertIsNone(u.parse_release(entry, '1.7.0'))

    def test_bad_origin_rejected(self):
        entry = release()
        entry['assets'][0]['browser_download_url'] = 'https://malicious.example/setup.exe'
        with self.assertRaisesRegex(ValueError, 'endereço'):
            u.parse_release(entry, '1.7.0')

    def test_no_digest_rejected(self):
        entry = release()
        entry['assets'][0]['digest'] = None
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            u.parse_release(entry, '1.7.0')

    def test_no_asset_rejected(self):
        entry = release()
        entry['assets'] = []
        with self.assertRaisesRegex(ValueError, 'não contém'):
            u.parse_release(entry, '1.7.0')

    def test_latest_update_no_network_in_test(self):
        with patch.object(u, 'urlopen', return_value=FakeResponse(json.dumps(release()).encode())) as fake:
            result = u.latest_update('1.7.0')
        self.assertEqual(result.version, '1.8.0')
        self.assertEqual(fake.call_count, 1)

    def test_download_checks_digest_and_uses_cached_verified_file(self):
        payload = b'simulated install file\x00\x01'
        data = u.parse_release(release(payload=payload), '1.7.0')
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(u.tempfile, 'gettempdir', return_value=tmp):
                with patch.object(u, 'urlopen', return_value=FakeResponse(payload)) as mock:
                    path = u.download_verified(data)
                self.assertEqual(path.read_bytes(), payload)
                with patch.object(u, 'urlopen', side_effect=AssertionError('redownloaded')):
                    self.assertEqual(u.download_verified(data), path)
                self.assertEqual(mock.call_count, 1)

    def test_download_rejects_corruption_and_removes_partial(self):
        payload = b'good' * 100
        data = u.parse_release(release(payload=payload), '1.7.0')
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(u.tempfile, 'gettempdir', return_value=tmp):
                with patch.object(u, 'urlopen', return_value=FakeResponse(b'evil' * 100)):
                    with self.assertRaisesRegex(ValueError, 'SHA-256'):
                        u.download_verified(data)
                self.assertEqual(list(Path(tmp).rglob('*.part')), [])

    def test_settings_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            self.assertTrue(u.read_auto_update_setting(folder))
            u.write_auto_update_setting(folder, False)
            self.assertFalse(u.read_auto_update_setting(folder))
            u.write_auto_update_setting(folder, True)
            self.assertTrue(u.read_auto_update_setting(folder))


if __name__ == '__main__':
    unittest.main()
