"""CPU ASR content gate. Does not claim a human naturalness assessment."""
import argparse
import difflib
import json
from pathlib import Path
import re
import unicodedata


def words(text):
    return re.findall(r'[a-z0-9]+',''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c)))


def compare(expected, observed):
    a,b=words(expected),words(observed)
    matcher=difflib.SequenceMatcher(a=a,b=b,autojunk=False)
    matched=sum(x.size for x in matcher.get_matching_blocks())
    coverage=matched/max(1,len(a)); precision=matched/max(1,len(b))
    return {'expected_words':len(a),'recognized_words':len(b),'word_coverage':coverage,
        'word_precision':precision,'audio_content_verified':bool(a) and coverage>=.92 and precision>=.92}


def review(audio, expected, model='small'):
    from faster_whisper import WhisperModel
    asr=WhisperModel(model,device='cpu',compute_type='int8',cpu_threads=2,num_workers=1)
    segments,info=asr.transcribe(str(audio),language='pt',beam_size=5,word_timestamps=True,condition_on_previous_text=False)
    segments=list(segments); transcript=' '.join(s.text.strip() for s in segments)
    result=compare(expected,transcript)
    result.update(transcript=transcript,language=info.language,asr_model='Systran/faster-whisper-'+model,
        naturalness_verified=False,method='automatic ASR agreement; not a perceptual pronunciation rating',
        words=[{'start':w.start,'end':w.end,'word':w.word,'probability':w.probability} for s in segments for w in (s.words or [])])
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audio',type=Path,required=True)
    p.add_argument('--script',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();script=json.loads(args.script.read_text());expected=' '.join(script) if isinstance(script,list) else script
    result=review(args.audio,expected);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if result['audio_content_verified'] else 2)
