import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import avatar_backend as avatar


class AvatarBoundaryTests(unittest.TestCase):
    def test_requested_presenter_does_not_mislabel_fallback(self):
        for preferred in ('A', 'B'):
            result = avatar.select_format(preferred)
            self.assertEqual(result['actual_format'], 'C')
            self.assertFalse(result['avatar_present'])
            self.assertEqual(result['reason'], 'NO_VALIDATED_AVATAR_BACKEND')

    def test_every_investigated_engine_fails_closed(self):
        for engine in avatar.ENGINE_BLOCKERS:
            with self.subTest(engine=engine), self.assertRaises(avatar.AvatarUnavailable):
                avatar.load_avatar_engine(engine)

    def test_unknown_provider_and_commands_are_rejected(self):
        for engine in ('paid-api', 'ffmpeg', 'portrait-pan', 'echo fake-avatar'):
            with self.subTest(engine=engine), self.assertRaisesRegex(avatar.AvatarUnavailable, 'UNKNOWN'):
                avatar.load_avatar_engine(engine)

    def test_installed_packages_do_not_certify_avatar_quality(self):
        with patch.object(avatar.importlib.util, 'find_spec', return_value=object()), \
             patch.object(avatar.shutil, 'which', return_value='/usr/bin/nvidia-smi'):
            result = avatar.probe()
        self.assertFalse(result['avatar_video_produced'])
        self.assertFalse(result['commercial_lip_sync_ready'])
        self.assertEqual(result['validated_avatar_engines'], [])

    def test_invalid_format_does_not_silently_fallback(self):
        with self.assertRaises(ValueError):
            avatar.select_format('unknown')
