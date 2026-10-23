"""Device propagation and drift rejection; these are not inference benchmarks."""
import ast
from types import SimpleNamespace
import unittest

from automation.avatar43_smoke import patch_reference_attention_device


FIXTURE = '''
class ReferenceAttentionControl:
    def register_reference_hooks(self, mode, dtype=torch.float16, device=torch.device("cuda")):
        return device, dtype
    def update(self, writer, dtype=torch.float16):
        return dtype
'''


class DevicePatchTests(unittest.TestCase):
    def make_controller(self, device='cpu', dtype='float32'):
        patched = patch_reference_attention_device(FIXTURE)
        scope = {}
        exec(compile(patched, '<patched-reference-attention>', 'exec'), scope)
        obj = scope['ReferenceAttentionControl']()
        obj.unet = SimpleNamespace(parameters=lambda: iter([SimpleNamespace(device=device, dtype=dtype)]))
        return obj

    def test_cpu_device_and_bank_dtype_follow_actual_unet(self):
        obj = self.make_controller()
        self.assertEqual(obj.register_reference_hooks('write'), ('cpu', 'float32'))
        self.assertEqual(obj.update(None), 'float32')

    def test_explicit_arguments_are_preserved(self):
        obj = self.make_controller()
        self.assertEqual(obj.register_reference_hooks('read', device='custom', dtype='custom_dtype'), ('custom', 'custom_dtype'))
        self.assertEqual(obj.update(None, dtype='explicit'), 'explicit')

    def test_does_not_globally_force_device_or_fake_cuda(self):
        obj = self.make_controller(device='model_device', dtype='model_dtype')
        self.assertEqual(obj.register_reference_hooks('read'), ('model_device', 'model_dtype'))

    def test_upstream_drift_and_double_patch_fail_closed(self):
        for changed in (FIXTURE.replace('torch.device("cuda")', 'get_device()'),
                        FIXTURE.replace('def update', 'def renamed'),
                        patch_reference_attention_device(FIXTURE)):
            with self.assertRaises(ValueError):
                patch_reference_attention_device(changed)


if __name__ == '__main__':
    unittest.main()
