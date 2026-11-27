"""Second observed ASR pass for disputes; neither pass is replaced by the script."""
import argparse
import json
from pathlib import Path
from audio_review import review


def resolve(primary, secondary):
    if primary.get('audio_content_verified') is True:
        return {'status':'PRIMARY_EXACT_CONTENT_MATCH','audio_content_verified':True}
    # A confident contradictory first recognition stays unresolved. A second
    # exact match alone is insufficient to erase high-confidence contradictions.
    from audio_review import words
    disputed={token for mismatch in primary.get('mismatches',[]) for token in mismatch.get('recognized',[])}
    probabilities={}
    for word in primary.get('words',[]):
        for token in words(word.get('word','')):
            probabilities.setdefault(token,[]).append(word.get('probability',1))
    all_disputed_low=bool(disputed) and all(token in probabilities and max(probabilities[token])<.5 for token in disputed)
    has_omission=any(m.get('operation')=='delete' for m in primary.get('mismatches',[]))
    secondary_confidence=[w.get('probability',0) for w in secondary.get('words',[])]
    if (secondary.get('audio_content_verified') is True and all_disputed_low and not has_omission
            and secondary_confidence and min(secondary_confidence)>=.65):
        return {'status':'LOW_CONFIDENCE_PRIMARY_SECONDARY_EXACT_MATCH','audio_content_verified':True,
                'method':'Two observed transcripts preserved; secondary supports all scripted words'}
    return {'status':'AUDITORY_REVIEW_REQUIRED','audio_content_verified':False,
        'reason':'ASR conflict or content mismatch; neither transcript is ground truth'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audio',type=Path,required=True);p.add_argument('--script',type=Path,required=True)
    p.add_argument('--primary',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    script=json.loads(args.script.read_text());expected=' '.join(script) if isinstance(script,list) else script
    primary=json.loads(args.primary.read_text());secondary=review(args.audio,expected,model='medium')
    decision=resolve(primary,secondary)
    args.output.write_text(json.dumps({'primary':primary,'secondary':secondary,'decision':decision},ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if decision['audio_content_verified'] else 2)
