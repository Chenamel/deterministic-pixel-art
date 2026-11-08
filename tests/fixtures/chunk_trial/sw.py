from common import create, rect, P
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--flag', default='F5C26B')
args = p.parse_args()
s = create('sw')
rect(s, 23, 37, 17, 11, 'A4A59A')
rect(s, 26, 35, 12, 3, 'C4C5B5')
rect(s, 45, 50, 8, 6, '858D84')
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(s), encoding='utf-8')
