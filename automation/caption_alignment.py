"""Use observed ASR word times only when the complete word sequence matches."""
import math
from audio_review import words
from caption_layout import layout


def align(lines, recognition, utterance_windows=None):
    expected=words(' '.join(lines));observed=[]
    for item in recognition.get('words',[]):
        for token in words(item.get('word','')):observed.append((token,float(item['start']),float(item['end'])))
    if (recognition.get('audio_content_verified') is not True
            or expected!=[token for token,_,_ in observed]):
        raise ValueError('WORD_ALIGNMENT_REQUIRES_EXACT_OBSERVED_CONTENT')
    if utterance_windows is not None:
        if len(utterance_windows)!=len(lines):raise ValueError('UTTERANCE_ALIGNMENT_WINDOWS_INCOMPLETE')
        previous=0.0
        for line,(start,end,text) in zip(lines,utterance_windows):
            if (words(line)!=words(text) or not all(math.isfinite(x) for x in (start,end))
                    or start<previous or end<=start):
                raise ValueError('UTTERANCE_ALIGNMENT_WINDOWS_INVALID')
            previous=end
    chunks=[]
    for line_index,line in enumerate(lines):
        current=''
        for word in line.split():
            proposed=(current+' '+word).strip()
            try:layout(proposed)
            except ValueError:
                if not current:raise
                chunks.append((current,line_index));current=word;layout(current)
            else:current=proposed
        if current:chunks.append((current,line_index))
    result=[];offset=0
    for text,line_index in chunks:
        count=len(words(text));first,last=observed[offset],observed[offset+count-1]
        start,end=first[1],last[2]
        if utterance_windows is not None:
            # The audio is a concatenation of preserved, hash-verified utterances.
            # ASR may extend a first word into the preceding inter-phrase pause.
            # Bound display times by that utterance's real audio interval; retain
            # every original observed word/time in the ASR report unchanged.
            floor,ceiling,_=utterance_windows[line_index]
            start=max(start,floor);end=min(end,ceiling)
        if end<=start:raise ValueError('ASR_WORD_TIME_RANGE_INVALID')
        if result and start<result[-1][1]:raise ValueError('ASR_WORD_TIME_OVERLAP')
        result.append([start,end,text]);offset+=count
    if offset!=len(observed):raise ValueError('ASR_WORD_ALIGNMENT_INCOMPLETE')
    return result
