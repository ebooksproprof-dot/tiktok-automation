"""Use observed ASR word times only when the complete word sequence matches."""
from audio_review import words
from caption_layout import layout


def align(lines, recognition):
    expected=words(' '.join(lines));observed=[]
    for item in recognition.get('words',[]):
        for token in words(item.get('word','')):observed.append((token,float(item['start']),float(item['end'])))
    if (recognition.get('audio_content_verified') is not True
            or expected!=[token for token,_,_ in observed]):
        raise ValueError('WORD_ALIGNMENT_REQUIRES_EXACT_OBSERVED_CONTENT')
    chunks=[]
    for line in lines:
        current=''
        for word in line.split():
            proposed=(current+' '+word).strip()
            try:layout(proposed)
            except ValueError:
                if not current:raise
                chunks.append(current);current=word;layout(current)
            else:current=proposed
        if current:chunks.append(current)
    result=[];offset=0
    for text in chunks:
        count=len(words(text));first,last=observed[offset],observed[offset+count-1]
        start,end=first[1],last[2]
        if end<=start:raise ValueError('ASR_WORD_TIME_RANGE_INVALID')
        if result and start<result[-1][1]:raise ValueError('ASR_WORD_TIME_OVERLAP')
        result.append([start,end,text]);offset+=count
    if offset!=len(observed):raise ValueError('ASR_WORD_ALIGNMENT_INCOMPLETE')
    return result
