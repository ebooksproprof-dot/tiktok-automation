"""Replaceable CPU narration interface; no hosted API or paid fallback."""
import hashlib
import os
from pathlib import Path
import subprocess
import textwrap
import wave

VOICE = 'pt_BR-faber-medium'
VOICE_SHA = '858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7'


class PiperEngine:
    name = 'piper-1.3.0-pt_BR-faber-medium'

    def __init__(self, cache):
        os.environ['ORT_DISABLE_TELEMETRY'] = '1'
        import onnxruntime as rt
        rt.disable_telemetry_events()
        from piper import PiperVoice
        cache = Path(cache)
        cache.mkdir(parents=True, exist_ok=True)
        model = cache / (VOICE + '.onnx')
        if not model.exists() or not model.with_suffix('.onnx.json').exists():
            subprocess.run(['python3', '-m', 'piper.download_voices', '--data-dir', str(cache), VOICE],
                           check=True, timeout=240)
        if hashlib.sha256(model.read_bytes()).hexdigest() != VOICE_SHA:
            raise ValueError('Voice model checksum mismatch')
        self.voice = PiperVoice.load(str(model))

    def speak(self, text, path):
        from piper import SynthesisConfig
        with wave.open(str(path), 'wb') as output:
            self.voice.synthesize_wav(text, output, syn_config=SynthesisConfig(length_scale=1.2))


def load_engine(cache, engine='piper'):
    if engine == 'chatterbox-v3-pt-br':
        from chatterbox_v3 import ChatterboxBrazilEngine, IsolatedChatterboxEngine
        return (IsolatedChatterboxEngine if os.getenv('CHATTERBOX_PYTHON') else ChatterboxBrazilEngine)(cache)
    if engine == 'piper':
        return PiperEngine(cache)
    if engine == 'kokoro-female':
        from female_narration import KokoroFemaleEngine
        return KokoroFemaleEngine(cache)
    raise ValueError('Unsupported narration engine; no silent or paid fallback')


def sentences(lines):
    result, parts = [], []
    for line in lines:
        parts.append(line.strip())
        if line.rstrip().endswith(('.', '!', '?')):
            result.append(' '.join(parts)); parts = []
    if parts:
        result.append(' '.join(parts))
    return result


def synthesize(engine, lines, folder, target_seconds=None):
    """Full sentences for prosody; captions use measured utterance boundaries."""
    if hasattr(engine, 'synthesize'):
        return engine.synthesize(lines, folder, target_seconds)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    parts, timings, position, expected = [], [], 0.0, None
    for index, sentence in enumerate(sentences(lines)):
        path = folder / f'sentence-{index}.wav'
        engine.speak(sentence, path)
        with wave.open(str(path), 'rb') as inp:
            shape = (inp.getnchannels(), inp.getsampwidth(), inp.getframerate())
            if shape[:2] != (1, 2) or (expected and shape != expected):
                raise ValueError('Narration engine must return consistent mono PCM16')
            expected = shape
            rate = shape[2]
            pcm = inp.readframes(inp.getnframes())
            duration = inp.getnframes()/rate
        caption_lines = textwrap.wrap(sentence, width=29, break_long_words=False)
        # At most two caption lines at once; chunk duration proportional to spoken text.
        chunks = ['\n'.join(caption_lines[i:i+2]) for i in range(0, len(caption_lines), 2)]
        total = sum(len(x) for x in chunks)
        cursor = position
        for chunk in chunks:
            end = cursor + duration * len(chunk)/total
            timings.append((cursor, end, chunk)); cursor = end
        parts.append(pcm + bytes(int(rate*.08)*2))
        position += duration + .08
    if target_seconds is not None:
        return finish_30(folder, parts, rate, position, timings, engine, target_seconds)
    if not 15 <= position <= 27.7:
        raise ValueError(f'Narration length out of range: {position:.2f}')
    with wave.open(str(folder/'voice.wav'), 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
        out.writeframes(b''.join(parts))
    return position, timings


def finish_30(folder, parts, rate, position, timings, engine, target_seconds=30):
    """Measured speech only, +/-10% tempo; no padding, loops or truncation."""
    import json
    source = folder/'narration-source.wav'
    with wave.open(str(source), 'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
        out.writeframes(b''.join(parts))
    tempo = position/target_seconds
    if not .90 <= tempo <= 1.10:
        raise ValueError(f'Narration length requires script edit: {position:.2f}s; tempo={tempo:.3f}')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-af',
        f'atempo={tempo:.9f},loudnorm=I=-16:TP=-1.5:LRA=9',
        '-ar','48000','-ac','1','-c:a','pcm_s16le',str(folder/'voice.wav')], check=True, timeout=120)
    with wave.open(str(folder/'voice.wav'), 'rb') as inp:
        actual = inp.getnframes()/inp.getframerate()
    if abs(actual-target_seconds) > .10:
        raise ValueError('NORMALIZED_NARRATION_DURATION_MISMATCH')
    (folder/'narration.json').write_text(json.dumps({'engine':engine.name,'source_seconds':position,
        'normalized_seconds':actual,'tempo':tempo,'audio_content_verified':False,
        'timing_method':'measured utterances; proportional caption chunks, not word alignment'},indent=2))
    return actual, [(start/tempo,min(actual,end/tempo),text) for start,end,text in timings]
