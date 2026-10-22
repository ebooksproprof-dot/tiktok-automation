"""Optional female pt-BR CPU narration. No hosted API, contract gate or paid fallback.

Kokoro-82M weights: Apache-2.0; kokoro-onnx wrapper: MIT. See VOICE-4.1.md.
Pinned assets are the maintainer's v1.0 int8 conversion and voice pack.
"""
import hashlib
from pathlib import Path
import urllib.request
import wave

VERSION = 'kokoro-onnx==0.6.1'
VOICE = 'pf_dora'
LANGUAGE = 'pt-br'
RELEASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
ASSETS = {
    'kokoro-v1.0.int8.onnx': (114119327, 'ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c'),
    'voices-v1.0.bin': (28214398, 'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'),
}


def verify(path, expected_size, expected_sha):
    with Path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if Path(path).stat().st_size != expected_size or digest != expected_sha:
        raise ValueError('Female voice asset checksum or size mismatch')


def acquire(cache):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    for name, (size, digest) in ASSETS.items():
        path = cache/name
        if path.exists():
            verify(path, size, digest)
            continue
        temporary = path.with_suffix(path.suffix+'.part')
        try:
            with urllib.request.urlopen(RELEASE+name, timeout=90) as response, temporary.open('wb') as out:
                downloaded = 0
                while chunk := response.read(1024*1024):
                    downloaded += len(chunk)
                    if downloaded > size:
                        raise ValueError('Female voice asset exceeds fixed size')
                    out.write(chunk)
            verify(temporary, size, digest)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return cache


class KokoroFemaleEngine:
    name = 'kokoro-onnx-0.6.1-v1.0-int8-pf_dora-pt-br'

    def __init__(self, cache):
        import importlib.metadata
        if importlib.metadata.version('kokoro-onnx') != '0.6.1':
            raise ValueError('Install pinned kokoro-onnx==0.6.1')
        import onnxruntime as rt
        from kokoro_onnx import Kokoro
        cache = acquire(cache)
        options = rt.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        session = rt.InferenceSession(str(cache/'kokoro-v1.0.int8.onnx'),
                                      sess_options=options, providers=['CPUExecutionProvider'])
        self.voice = Kokoro.from_session(session, str(cache/'voices-v1.0.bin'))

    def speak(self, text, path):
        if not isinstance(text, str) or not text.strip() or len(text) > 600:
            raise ValueError('Female narration requires one bounded nonempty sentence')
        import numpy as np
        audio, rate = self.voice.create(text, voice=VOICE, lang=LANGUAGE, speed=1.0)
        samples = np.asarray(audio)
        if rate != 24000 or samples.ndim != 1 or not len(samples) or not np.isfinite(samples).all():
            raise ValueError('Invalid female narration audio')
        pcm = (np.clip(samples, -1, 1)*32767).astype('<i2')
        with wave.open(str(path), 'wb') as out:
            out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
            out.writeframes(pcm.tobytes())
