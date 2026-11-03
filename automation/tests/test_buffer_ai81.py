"""AI-only 30s exception is narrow; legacy publishing validation unchanged."""
from pathlib import Path
import io
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import buffer_runner
import media_quality


class BufferAI81Tests(unittest.TestCase):
    def test_legacy_duration_default_still_restricted(self):
        source=Path(media_quality.__file__).read_text()
        self.assertIn('15 <= duration <= 28',source)
        self.assertIn('def validate(path, *, ai_only30=False)',source)

    def test_ai_only_incomplete_metadata_blocks(self):
        item={'publication_provider':'buffer',
              'video_origin':'ai_only30',
              'quality':{'technical_pass':True,'editorial_approved':True}}
        with self.assertRaisesRegex(ValueError,'AI30_OWNER_CONSENT'):
            buffer_runner.prepare(item,{'posts':{}},'channel')

    def test_ai_only_30_media_uses_explicit_opt_in(self):
        item={'video_origin':'ai_only30',
              'video_url':'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-11/example.mp4',
              'quality':{'sha256':'a'*64}}
        with patch.object(buffer_runner.urllib.request,'urlopen',return_value=io.BytesIO(b'not-a-real-mp4')),\
             patch.object(buffer_runner,'validate',return_value={'sha256':'a'*64}) as check:
            buffer_runner.verify_hosted(item)
        check.assert_called_once()
        self.assertEqual(check.call_args.kwargs,{'ai_only30':True})

    def test_legacy_video_keeps_one_arg_validator(self):
        item={'video_url':'https://github.com/ebooksproprof-dot/tiktok-automation/releases/download/media-2026-11/example.mp4',
              'quality':{'sha256':'a'*64}}
        with patch.object(buffer_runner.urllib.request,'urlopen',return_value=io.BytesIO(b'not-a-real-mp4')),\
             patch.object(buffer_runner,'validate',return_value={'sha256':'a'*64}) as check:
            buffer_runner.verify_hosted(item)
        check.assert_called_once()
        self.assertEqual(check.call_args.kwargs,{})


if __name__=='__main__':
    unittest.main()
