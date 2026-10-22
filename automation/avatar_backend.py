"""Explicit avatar capability boundary. No validated avatar engine is deployed.

A portrait is an identity asset, not a speaking avatar. This module performs no
downloads, license acceptance, paid fallback, rendering, or publication.
"""
import importlib.util
import json
import os
import platform
import shutil


class AvatarUnavailable(RuntimeError):
    pass


ENGINE_BLOCKERS = {
    'sadtalker': ('THIRD_PARTY_BFM_ASSET_COMMERCIAL_PERMISSION_UNRESOLVED',
                  'CPU_PATH_EXISTS_BUT_NO_VALIDATED_RUNTIME_OR_WEIGHTS',
                  'LIP_SYNC_QUALITY_AND_CPU_RENDER_BUDGET_UNMEASURED'),
    'musetalk': ('DOCUMENTED_SETUP_USES_CUDA_NOT_AVAILABLE_IN_STANDARD_CPU_RUNNER',),
    'wav2lip': ('OFFICIAL_RELEASE_RESTRICTED_TO_NONCOMMERCIAL_USE',),
    'liveportrait': ('DEFAULT_INSIGHTFACE_WEIGHTS_NONCOMMERCIAL',
                     'DRIVING_MOTION_DOES_NOT_PROVE_AUDIO_DRIVEN_LIP_SYNC'),
}


def probe():
    """Read-only measured environment inventory; never infer model performance."""
    return {
        'python_version': platform.python_version(),
        'cpu_count_reported': os.cpu_count(),
        'torch_installed': importlib.util.find_spec('torch') is not None,
        'opencv_installed': importlib.util.find_spec('cv2') is not None,
        'nvidia_smi_present': shutil.which('nvidia-smi') is not None,
        'validated_avatar_engines': [],
        'avatar_inference_executed': False,
        'avatar_video_produced': False,
        'commercial_lip_sync_ready': False,
        'fallback_format': 'C',
        'blockers': ENGINE_BLOCKERS,
    }


def select_format(preferred='B'):
    if preferred not in ('A', 'B', 'C'):
        raise ValueError('Unknown presentation format')
    return dict(requested_format=preferred, actual_format='C', avatar_present=False,
                reason=None if preferred == 'C' else 'NO_VALIDATED_AVATAR_BACKEND',
                requires_real_licensed_demonstration=True,
                synthetic_presenter_image_is_not_lip_sync=True)


def load_avatar_engine(name):
    """Future adapter entry point; enabling requires real license/runtime/QA work.

    No arbitrary provider, external command, environment flag, still-photo pan,
    or paid API is accepted as a substitute for a validated implementation.
    """
    if name not in ENGINE_BLOCKERS:
        raise AvatarUnavailable('UNKNOWN_AVATAR_BACKEND')
    raise AvatarUnavailable(name + ': ' + '; '.join(ENGINE_BLOCKERS[name]))


if __name__ == '__main__':
    print(json.dumps(probe(), indent=2))
