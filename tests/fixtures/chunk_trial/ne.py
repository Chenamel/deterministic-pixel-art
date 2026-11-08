from common import create, rect, P
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--flag', default='F5C26B')
args = p.parse_args()
s = create('ne')
rect(s, 70, 28, 3, 30, P['joint'])
rect(s, 62, 24, 20, 12, P['plank'])
rect(s, 65, 29, 12, 2, P['rail'])
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(s), encoding='utf-8')
