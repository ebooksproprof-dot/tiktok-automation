#!/usr/bin/env python3
"""Create two new CasaSemEsforço shorts in GitHub Actions; no fake posting consent."""
import datetime as dt
import json
import os
import pathlib
import random
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "rendered" / "daily"
QUEUE = ROOT / "automation" / "queue.json"
ASSETS = ROOT / "tmp" / "daily"
ASSETS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

SOURCE = {
  "piso": "https://videos.pexels.com/video-files/9473227/9473227-uhd_2160_3840_24fps.mp4",
  "pia": "https://videos.pexels.com/video-files/9472849/9472849-uhd_2160_3840_24fps.mp4",
  "espelho": "https://videos.pexels.com/video-files/9462884/9462884-uhd_2160_3840_24fps.mp4",
}
IDEAS = [
 ("piso", "PISO SEM BRILHO?", "MENOS PRODUTO", "PANO BEM TORCIDO", "SALVE A DICA", "Piso opaco? Teste menos produto e um pano bem torcido."),
 ("pia", "PIA COM MARCAS?", "ENXAGUE BEM", "FINALIZE SECO", "SIGA PARA MAIS", "Pia com marcas? Enxague bem e finalize com pano seco."),
 ("espelho", "ESPELHO MANCHADO?", "POUCA SOLUCAO", "PANO SECO", "SALVE ESTA DICA", "Espelho manchado? Use pouca solucao e finalize seco."),
 ("piso", "ERRO NA FAXINA", "EXCESSO DE SABAO", "ENXAGUE O PISO", "SIGA PARA MAIS", "Excesso de produto pode deixar residuos no piso."),
 ("pia", "BRILHO NA PIA", "RETIRE RESIDUOS", "SEQUE COM PANO", "SALVE PARA TESTAR", "A etapa de secagem pode ajudar a reduzir marcas."),
 ("espelho", "VIDRO COM MARCAS?", "USE POUCO", "SEQUE AO FINAL", "SALVE ESTE PASSO", "Use produtos apropriados e evite excesso no vidro."),
]
def run(args):
    subprocess.run(args, check=True)
def get_clip(key):
    target = ASSETS / (key + ".mp4")
    if target.exists() and target.stat().st_size > 100000:
        return target
    req = urllib.request.Request(SOURCE[key], headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, target.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk: break
            f.write(chunk)
    return target

def escape(s):
    return s.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace(",", r"\,").replace("%", r"\%")

def main():
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).date()
    seed = (today - dt.date(2026, 10, 15)).days
    rng = random.Random(seed)
    candidates = list(range(len(IDEAS)))
    rng.shuffle(candidates)
    selected = candidates[:2]
    queue = json.loads(QUEUE.read_text(encoding="utf8"))
    existing = {p["id"] for p in queue["posts"]}
    rendered = []
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    for slot, idx in enumerate(selected):
        key, hook, step1, step2, cta, title = IDEAS[idx]
        post_id = f"casasem-{today.isoformat()}-{slot + 1}"
        if post_id in existing:
            print(f"Already queued: {post_id}")
            continue
        source = get_clip(key)
        output = OUT / (post_id + ".mp4")
        # Cinematic vertical cut from real footage, not static slides.
        filters = ["scale=720:1280:force_original_aspect_ratio=increase",
                   "crop=720:1280", "fps=24", "eq=contrast=1.06:saturation=1.08"]
        for t, text, size in [(0,hook,52),(4.5,step1,52),(10,step2,52),(15.5,cta,48)]:
            end = min(t + 4.0, 19)
            filters.append(f"drawtext=fontfile={font}:text='{escape(text)}':fontsize={size}:fontcolor=white:borderw=5:bordercolor=black@0.85:x=(w-text_w)/2:y=210:enable='between(t,{t},{end})'")
        filters.append(f"drawtext=fontfile={font}:text='CASA SEM ESFORCO':fontsize=28:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=1120")
        run(["ffmpeg","-y","-stream_loop","-1","-i",str(source),"-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=44100",
             "-t","20","-vf",",".join(filters),"-c:v","libx264","-preset","veryfast","-crf","24","-pix_fmt","yuv420p",
             "-r","24","-c:a","aac","-b:a","64k","-shortest","-movflags","+faststart",str(output)])
        probe = subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size",
                                          "-of","json",str(output)],text=True)
        meta = json.loads(probe)["format"]
        if float(meta["duration"]) < 18 or int(meta["size"]) < 100000:
            raise RuntimeError(f"Failed render validation {output}: {meta}")
        # No fabrication of TikTok user approval or post-specific consent.
        hour = 10 if slot == 0 else 18
        scheduled = dt.datetime.combine(today, dt.time(hour), dt.timezone(dt.timedelta(hours=-3))).astimezone(dt.timezone.utc)
        queue["posts"].append({"id":post_id,
            "video_url":f"https://raw.githubusercontent.com/ebooksproprof-dot/tiktok-automation/main/public/rendered/daily/{output.name}",
            "title":title + " #CasaSemEsforco #DicasDeLimpeza",
            "scheduled_at":scheduled.isoformat().replace("+00:00","Z"),
            "privacy_level":"PUBLIC_TO_EVERYONE",
            "disable_duet":False,"disable_comment":False,"disable_stitch":False,
            "approved":False,"consented_at":None})
        rendered.append(output)
        print(f"RENDERED {output} {meta}")
    if rendered:
        QUEUE.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(f"NEW_VIDEO_COUNT={len(rendered)}")
if __name__ == "__main__":
    main()
