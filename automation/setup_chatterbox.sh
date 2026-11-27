#!/usr/bin/env bash
set -euo pipefail
# An absent identity is a visible hold, not permission to use a different voice.
if ! python -c 'import json; d=json.load(open("automation/voice_identity.json")); raise SystemExit(0 if d["status"]=="APPROVED" and d["commercial_synthesis_authorized"] and d["perceptual_review_approved"] else 2)'; then
  echo '::warning::CHATTERBOX_FEMALE_REFERENCE_AND_REVIEW_PENDING; no fallback voice enabled'
  exit 0
fi
umask 077
source_kind=$(python -c 'import json;print(json.load(open("automation/voice_identity.json")).get("reference_source",{}).get("kind","secret"))')
if [ "$source_kind" = 'kyutai_donation' ]; then
  reference_path=$(python -c 'import os,sys;sys.path.insert(0,"automation");from voice_candidate_review import reference;print(reference("unmute-lara",os.environ["RUNNER_TEMP"]+"/voice-private")[2])')
else
  : "${CHATTERBOX_REFERENCE_WAV_B64:?Approved voice requires encrypted reference secret}"
  reference_path="$RUNNER_TEMP/casasem-voice-reference.wav"
  printf '%s' "$CHATTERBOX_REFERENCE_WAV_B64" | base64 --decode > "$reference_path"
fi
export CHATTERBOX_REFERENCE_PATH="$reference_path"
python -c 'import sys;sys.path.insert(0,"automation");from chatterbox_v3 import identity;identity()'
python -m venv "$RUNNER_TEMP/chatterbox-v3"
"$RUNNER_TEMP/chatterbox-v3/bin/pip" install 'torch==2.8.0+cpu' 'torchaudio==2.8.0+cpu' --index-url https://download.pytorch.org/whl/cpu
"$RUNNER_TEMP/chatterbox-v3/bin/pip" install -r automation/requirements-chatterbox-v3.txt
printf 'CHATTERBOX_PYTHON=%s\nCHATTERBOX_REFERENCE_PATH=%s\n' "$RUNNER_TEMP/chatterbox-v3/bin/python" "$reference_path" >> "$GITHUB_ENV"

python -m venv "$RUNNER_TEMP/casasem-asr"
"$RUNNER_TEMP/casasem-asr/bin/pip" install 'faster-whisper==1.2.1'
printf 'ASR_PYTHON=%s\n' "$RUNNER_TEMP/casasem-asr/bin/python" >> "$GITHUB_ENV"
