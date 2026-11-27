"""Pinned official Brazilian V3 loader. CPU only; never uses demo voice URLs."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import random
import sys
import wave

MODEL = 'ResembleAI/Chatterbox-Multilingual-pt-br'
MODEL_REVISION = 'b3952f18bc2eaa72b9bd7c17d2c4653bcad4770d'
BASE_REVISION = '5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18'
SPACE = 'ResembleAI/Chatterbox-Multilingual-TTS-pt-br'
CODE_REVISION = '9e515821e826e207cd617a0fdd0223899ed108ea'
NAME = 'chatterbox-multilingual-v3-pt-br@'+MODEL_REVISION[:12]
IDENTITY = Path(__file__).with_name('voice_identity.json')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(path=None):
    data = json.loads(Path(path or IDENTITY).read_text())
    if (data.get('status') != 'APPROVED' or data.get('locale') != 'pt-BR'
            or data.get('gender') != 'female' or data.get('commercial_synthesis_authorized') is not True
            or not data.get('rights_evidence') or not data.get('holder')
            or data.get('perceptual_review_approved') is not True):
        raise ValueError('CHATTERBOX_FEMALE_REFERENCE_AND_REVIEW_PENDING')
    reference = Path(os.environ.get('CHATTERBOX_REFERENCE_PATH', ''))
    if not reference.is_file() or digest(reference) != data.get('reference_sha256'):
        raise ValueError('CHATTERBOX_REFERENCE_MISSING_OR_HASH_MISMATCH')
    with wave.open(str(reference), 'rb') as inp:
        if inp.getnchannels() != 1 or inp.getsampwidth() != 2 or not 5 <= inp.getnframes()/inp.getframerate() <= 12:
            raise ValueError('CHATTERBOX_REFERENCE_EXPECTED_5_TO_12_SECONDS_MONO_PCM16')
    return data, reference


def acquire(cache):
    from huggingface_hub import hf_hub_download
    cache = Path(cache).resolve(); cache.mkdir(parents=True, exist_ok=True)
    lock = json.loads(Path(__file__).with_name('chatterbox_v3_sources.json').read_text())
    code = cache/'code'; code.mkdir(exist_ok=True)
    for filename, expected in lock['files'].items():
        destination = code/filename
        downloaded = destination if destination.exists() else Path(hf_hub_download(SPACE, filename, repo_type='space', revision=CODE_REVISION))
        if digest(downloaded) != expected:
            raise ValueError('CHATTERBOX_PINNED_CODE_HASH_MISMATCH')
        destination = code/filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists(): destination.symlink_to(downloaded)
        if digest(destination) != expected: raise ValueError('CHATTERBOX_CACHED_CODE_CHANGED')
    weights = cache/'weights'; weights.mkdir(exist_ok=True)
    for repo, revision, files in [
        (MODEL, MODEL_REVISION, ['t3_pt_br.safetensors','s3gen_v3.pt','grapheme_mtl_merged_expanded_v1.json']),
        ('ResembleAI/chatterbox', BASE_REVISION, ['ve.pt','conds.pt'])]:
        for filename in files:
            destination = weights/filename
            downloaded = destination if destination.exists() else Path(hf_hub_download(repo, filename, revision=revision))
            if not destination.exists(): destination.symlink_to(downloaded)
    if digest(weights/'t3_pt_br.safetensors') != '074aaf65255eb9cb960288f7cc72e09d3b5008f6e0b14868c0d4e5b0bd7cbb6c':
        raise ValueError('CHATTERBOX_T3_HASH_MISMATCH')
    sys.path.insert(0, str(code))
    module = importlib.import_module('chatterbox.src.chatterbox.tts')
    # Same pinned architecture/checkpoints as the official from_local; assign
    # tensors directly to avoid a second 2.1GB copy on 7GB Actions runners.
    import torch
    import gc
    ve = module.VoiceEncoder()
    ve.load_state_dict(torch.load(weights/'ve.pt', weights_only=True, map_location='cpu'), assign=True)
    cfg = module.T3ConfigMultilingual(); cfg.text_tokens_dict_size = 2454
    t3 = module.T3(cfg)
    t3.load_state_dict(module.load_safetensors(weights/'t3_pt_br.safetensors'), assign=True)
    gc.collect()
    s3gen = module.S3Gen()
    s3gen.load_state_dict(torch.load(weights/'s3gen_v3.pt',weights_only=True,map_location='cpu',mmap=True), strict=False, assign=True)
    tokenizer = module.MTLTokenizer(str(weights/'grapheme_mtl_merged_expanded_v1.json'))
    conds = module.Conditionals.load(weights/'conds.pt')
    return module.ChatterboxTTS(t3.eval(),s3gen.eval(),ve.eval(),tokenizer,'cpu',conds=conds)


class ChatterboxBrazilEngine:
    name = NAME

    def __init__(self, cache):
        self.identity, reference = identity()  # Rights gate precedes downloads/inference.
        self.cache = Path(cache)/'chatterbox-v3'
        import torch
        torch.set_num_threads(2)
        self.model = acquire(self.cache)
        self.model.prepare_conditionals(str(reference), exaggeration=.5)
        self.voice_id = self.identity['reference_sha256']

    def speak(self, text, path):
        if not isinstance(text, str) or not text.strip() or len(text) > 300:
            raise ValueError('CHATTERBOX_SENTENCE_MUST_HAVE_1_TO_300_CHARACTERS')
        import numpy as np
        import torch
        import soundfile as sf
        # Stable settings + reference. Cache key includes exact text, model and voice.
        key = hashlib.sha256((self.name+self.voice_id+text+'seed14-cfg.5-temp.8-exp.5').encode()).hexdigest()
        cached = self.cache/'utterances'/(key+'.wav')
        cached.parent.mkdir(parents=True, exist_ok=True)
        from narration_store import restore, persist
        if not cached.exists():
            restore(key, cached)
        if not cached.exists():
            random.seed(14); np.random.seed(14); torch.manual_seed(14)
            with torch.inference_mode():
                wav = self.model.generate(text, language_id='pt', exaggeration=.5, cfg_weight=.5, temperature=.8)
            temp = cached.with_suffix('.partial.wav')
            sf.write(temp, wav.squeeze().cpu().numpy(), self.model.sr, subtype='PCM_16')
            temp.replace(cached)
        persist(key, cached)  # Before any later compositor can fail.
        import shutil
        shutil.copyfile(cached, path)


class IsolatedChatterboxEngine:
    name = NAME

    def __init__(self, cache):
        self.identity, _ = identity()
        self.voice_id = self.identity['reference_sha256']
        self.cache = Path(cache).resolve()

    def synthesize(self, lines, folder, target_seconds):
        import subprocess
        folder = Path(folder).resolve(); folder.mkdir(parents=True, exist_ok=True)
        request = folder/'script.json'; request.write_text(json.dumps(lines,ensure_ascii=False))
        subprocess.run([os.environ['CHATTERBOX_PYTHON'],str(Path(__file__).with_name('chatterbox_worker.py')),
            '--cache',str(self.cache),'--folder',str(folder),'--lines',str(request)],check=True,timeout=1800)
        result=json.loads((folder/'isolated-result.json').read_text())
        return result['duration'], result['timings']
