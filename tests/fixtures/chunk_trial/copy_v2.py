from pathlib import Path
import shutil

r = Path(__file__).resolve().parent
(r / 'v2/chunks').mkdir(parents=True)
for n in ('nw', 'ne', 'sw'):
    for ext in ('.json', '.png'):
        shutil.copyfile(r / 'v1/chunks' / (n + ext), r / 'v2/chunks' / (n + ext))
shutil.copyfile(r / 'v1/project.json', r / 'v2/project.json')
