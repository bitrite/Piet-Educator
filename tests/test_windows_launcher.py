import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from windows_launcher import load_settings, matches_learning_space, main


class WindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='Piet path with spaces ')
        self.home = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def settings(self, band='6-9'):
        (self.home / 'settings.json').write_text(json.dumps({'schema_version': 1, 'age_band': band}), encoding='utf-8-sig')

    def test_windows_utf8_bom_and_space_in_path(self):
        self.settings('10-12')
        self.assertEqual(load_settings(self.home)['age_band'], '10-12')

    def test_missing_configuration_needs_installer(self):
        with self.assertRaisesRegex(ValueError, 'Install-Windows'):
            load_settings(self.home)

    def test_invalid_age_never_falls_back_to_adult(self):
        for band in ('unknown', '', 17):
            self.settings(band)
            with self.assertRaises(ValueError): load_settings(self.home)

    def test_existing_server_must_match_age_and_data_location(self):
        data = self.home / 'data'
        session = {'application': 'piet-educator', 'age_band': '6-9', 'instance_id': hashlib.sha256(str(data.resolve()).casefold().encode()).hexdigest()[:16]}
        self.assertTrue(matches_learning_space(session, '6-9', data))
        self.assertFalse(matches_learning_space(session, 'adult', data))
        self.assertFalse(matches_learning_space(session, '6-9', self.home / 'other'))
        self.assertFalse(matches_learning_space(dict(session, application='other'), '6-9', data))

    def test_diagnostics_does_not_start_reader_or_create_books(self):
        self.settings()
        with patch('windows_launcher.ensure_ollama'), patch('windows_launcher.Ollama') as model, patch('windows_launcher.make_server') as server:
            self.assertEqual(main(['--home', str(self.home), '--diagnostics']), 0)
            self.assertEqual(model.call_count, 2)
            server.assert_not_called()
        self.assertFalse((self.home / 'data').exists())

    def test_missing_model_stops_launch(self):
        self.settings()
        with patch('windows_launcher.ensure_ollama'), patch('windows_launcher.Ollama') as model, patch('windows_launcher.make_server') as server:
            model.return_value.verify_local.side_effect = ValueError('Missing local weights')
            with self.assertRaises(ValueError): main(['--home', str(self.home)])
            server.assert_not_called()


if __name__ == '__main__':
    unittest.main()
