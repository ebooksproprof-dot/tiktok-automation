"""Optional, isolated EffectCraft 0.11.1 CPU proof; never required by daily render."""
import hashlib
import subprocess
from pathlib import Path

BINARY_SHA256 = 'fe78d8df0221d06d5519e02f3c382c1dfcd3241217a0e46644b4598a215b8d61'

def render(binary, project, output, composition='CasaSemEsforco Original'):
    binary = Path(binary).resolve()
    if hashlib.sha256(binary.read_bytes()).hexdigest() != BINARY_SHA256:
        raise ValueError('Unverified EffectCraft binary')
    subprocess.run([str(binary), 'render', '--project', str(project), '--comp', composition,
                    '--audio', 'off', '--out', str(output)], check=True, timeout=120)
    return Path(output)
