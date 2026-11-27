"""Mission16 regression fixtures are simulations, never perceptual evidence."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import photoreal_policy as policy


class RejectedIllustration16(unittest.TestCase):
    def quality(self):
        return json.loads((Path(policy.__file__).parent/'mission15-evidence/episode/video-review.json').read_text())

    def test_approved_voice_cannot_reactivate_owners_visual_rejection(self):
        from mission15_stage import finalized_quality
        q=self.quality();q.update(technical_pass=True,visual_editorial_approved=True)
        with self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):
            finalized_quality({'status':'APPROVED','perceptual_review_approved':True},q,{}, {},q['sha256'],'a'*64)

    def test_removing_origin_metadata_does_not_remove_rejection_of_the_file(self):
        q=self.quality();q.pop('video_origin',None);q.update(visual_style='photorealistic')
        with self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):policy.reject_incompatible(q)

    def test_visual_rejection_precedes_voice_and_fingerprint_approval(self):
        from mission14_policy import require_output
        from visual_library import require_evidence
        q=self.quality()
        for check in (lambda:require_output(q),lambda:require_evidence({'quality':q})):
            with self.assertRaisesRegex(ValueError,'VISUAL_STYLE_NOT_PHOTOREALISTIC'):check()
