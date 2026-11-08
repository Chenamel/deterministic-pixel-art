from common import create, rect, P
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--flag', default='F5C26B')
args = p.parse_args()
s = create('se')
rect(s, 66, 38, 2, 23, P['rail'])
rect(s, 68, 40, 8, 5, args.flag)
rect(s, 62, 60, 12, 2, P['joint'])
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(s), encoding='utf-8')
