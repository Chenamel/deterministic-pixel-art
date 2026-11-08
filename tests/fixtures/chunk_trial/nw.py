from common import create, rect, P
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--flag', default='F5C26B')
args = p.parse_args()
s = create('nw')
rect(s, 22, 48, 42, 32, 'B18B65')
rect(s, 18, 30, 50, 20, '704942')
rect(s, 38, 64, 10, 16, '463D3A')
rect(s, 28, 55, 6, 6, '9DC4CA')
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(s), encoding='utf-8')
