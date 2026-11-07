"""Pinned, local CPU visual review. No hosted inference, GPU or paid fallback.

This is an automated acceptance policy, not a claim of human editorial review.
Provider tags only nominate a family; sampled portrait frames must support it.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

MODEL = 'HuggingFaceTB/SmolVLM-500M-Instruct'
REVISION = 'a7da5b986cb59b408707209984f360a5f4ad7e47'
LICENSE = 'https://huggingface.co/' + MODEL + '/blob/' + REVISION + '/README.md'
PORTRAIT = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30'
FAMILIES = {
    'clothes': ({'ironing', 'iron', 'closet', 'wardrobe', 'hanger', 'hangers', 'folding', 'laundry'},
                {'iron', 'ironing', 'shirt', 'shirts', 'clothes', 'clothing', 'jacket', 'jackets', 'hanger', 'hangers', 'wardrobe', 'closet', 'garment'}),
    'dishes': ({'dish', 'dishes', 'dishwashing', 'tableware', 'plate', 'plates', 'utensils'},
               {'dish', 'dishes', 'plate', 'plates', 'cutlery', 'spoon', 'utensils', 'washing'}),
    'sweeping': ({'sweeping', 'broom', 'dustpan'}, {'broom', 'sweeping', 'dustpan', 'sweep'}),
    'wiping': ({'cloth', 'microfiber', 'wiping'}, {'cloth', 'wiping', 'wipe', 'cleaning', 'countertop', 'sponge'}),
    'books': ({'books', 'bookshelf', 'shelf', 'shelves', 'bookcase'}, {'books', 'book', 'shelf', 'shelves', 'bookcase', 'library'}),
    'handwashing': ({'handwashing'}, {'washing', 'wash', 'soap', 'sink', 'hands'}),
}
FORBIDDEN = {'porn', 'nude', 'naked', 'weapon', 'gun', 'blood', 'injury', 'waterfall', 'river', 'mountain',
             'ocean', 'flamingo', 'bird', 'duck', 'mosque', 'quran', 'cigarette', 'cigarettes', 'smoking',
             'ski', 'skiing', 'pulleys', 'tractor', 'bridge', 'campfire', 'fire', 'burns', 'construction', 'classroom'}


def words(text):
    return set(re.findall(r'[a-z]+', str(text).lower()))


def nominate(record):
    text = record.get('selection_reason', '')
    if 'ai generated' in text.lower() or 'ai-generated' in text.lower():
        return None
    tags = words(text)
    if tags & FORBIDDEN:
        return None
    # A botanical "broom" is not a housekeeping action.
    if tags & {'blossom', 'blossoms', 'flower', 'flowers', 'rain'}:
        return None
    if tags & {'hand', 'hands'} and tags & {'soap', 'washing'}:
        return 'handwashing'
    return next((name for name, (hints, _) in FAMILIES.items() if hints & tags), None)


def assess(family, captions):
    if family not in FAMILIES or len(captions) != 3:
        return False
    allowed = FAMILIES[family][1]
    tokens = [words(caption) for caption in captions]
    # Two frames are insufficient if the remaining sample shows unsafe content.
    return (not any(t & FORBIDDEN for t in tokens)
            and sum(bool(t & allowed) for t in tokens) >= 2)


def motion(path):
    result = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', str(path),
        '-vf', 'freezedetect=n=-50dB:d=1', '-an', '-threads', '2', '-f', 'null', '-'],
        capture_output=True, text=True, timeout=120)
    if result.returncode or 'freeze_start:' in result.stderr:
        raise ValueError('SOURCE_FROZEN_OR_UNDECODABLE')
    return {'decoder_pass': True, 'freeze_intervals_over_1s': 0, 'freeze_threshold_db': -50}


class Reviewer:
    def __init__(self, cache=None):
        import torch
        from transformers import AutoModelForVision2Seq, AutoProcessor
        torch.set_num_threads(2)
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(MODEL, revision=REVISION,
            cache_dir=cache, trust_remote_code=False)
        self.model = AutoModelForVision2Seq.from_pretrained(MODEL, revision=REVISION,
            cache_dir=cache, trust_remote_code=False, use_safetensors=True,
            torch_dtype=torch.float32, _attn_implementation='eager').eval()

    def review(self, path, record, folder):
        from PIL import Image
        family = nominate(record)
        if not family:
            raise ValueError('UNSUPPORTED_OR_UNSAFE_SOURCE_CONTEXT')
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=nw=1:nk=1', str(path)], timeout=30))
        captions, hashes = [], []
        started = time.monotonic()
        for index, fraction in enumerate((.15, .5, .85)):
            frame = folder/f'frame-{index}.jpg'
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(duration*fraction),
                '-i', str(path), '-frames:v', '1', '-vf', PORTRAIT+',scale=384:672',
                '-threads', '1', '-y', str(frame)], check=True, timeout=45)
            image = Image.open(frame).convert('RGB')
            prompt = self.processor.apply_chat_template([{'role': 'user', 'content': [
                {'type': 'image'}, {'type': 'text', 'text':
                 'Describe the visible objects and what the hands or people are doing. Only describe what you can see.'}]}],
                add_generation_prompt=True)
            inputs = self.processor(text=prompt, images=[image], return_tensors='pt')
            with self.torch.inference_mode():
                generated = self.model.generate(**inputs, max_new_tokens=48, do_sample=False)
            caption = self.processor.batch_decode(generated[:, inputs['input_ids'].shape[1]:],
                skip_special_tokens=True)[0].strip()
            captions.append(caption)
            hashes.append(hashlib.sha256(frame.read_bytes()).hexdigest())
            print('SEMANTIC_FRAME_COMPLETE='+record['provider_id']+'; SAMPLE='+str(index+1), flush=True)
        result = {'method': 'automated_cpu_portrait_frame_semantics', 'model': MODEL,
                  'revision': REVISION, 'model_license': LICENSE, 'model_license_id': 'Apache-2.0',
                  'family': family, 'captions': captions, 'frame_sha256': hashes,
                  'source_sha256': record['sha256'], 'accepted': assess(family, captions),
                  'review_seconds': round(time.monotonic()-started, 3),
                  'human_review': False, 'hosted_inference_calls': 0}
        (folder/'review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        if not result['accepted']:
            raise ValueError('PORTRAIT_VISUAL_CONTEXT_REJECTED')
        result.update(motion(path))
        return result
