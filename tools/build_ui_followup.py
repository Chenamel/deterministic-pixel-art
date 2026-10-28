"""Build one UI task from an explicitly hashed candidate; coordinator notes stay outside."""
import argparse
from pathlib import Path

from build_long_term_trials import ROOT, encoded, frozen_files
from prepare_agent_trials import archive_bytes, sha


def build(skill_zip, out, expected):
    files = frozen_files(skill_zip, expected)
    if 'deterministic-pixel-art/scripts/recipes/label_atlas.py' not in files:
        raise ValueError('UI follow-up requires the font-helper candidate')
    files.update({'START_HERE.md': (ROOT/'benchmarks/long-term/UI01.md').read_bytes(),
                  'run.py': (ROOT/'benchmarks/long-term/runner.py').read_bytes(),
                  'task.json': encoded(dict(id='UI01', skill_zip_sha256=expected))})
    for name in ('Silkscreen-Regular.ttf', 'OFL.txt', 'source.json'):
        files['inputs/'+name] = (ROOT/'demos/pixel-ui/fonts'/name).read_bytes()
    files['checksums.json'] = encoded({name: sha(data) for name, data in sorted(files.items())})
    payload = archive_bytes({'UI01/'+name: data for name, data in files.items()})
    out.mkdir(parents=True, exist_ok=False)
    (out/'UI-followup.zip').write_bytes(payload)
    record = dict(task='UI01', recommended_environment='WorkBuddy / DeepSeek-V4.1-Flash, fresh session',
                  archive='UI-followup.zip', bytes=len(payload), sha256=sha(payload),
                  skill_zip_sha256=expected, external_runs=0)
    coordinator = out/'coordinator'; coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(record))
    (coordinator/'SHA256SUMS.txt').write_text(sha(payload)+'  UI-followup.zip\n', encoding='ascii')
    return record


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-zip', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.skill_zip, args.out, args.sha256), indent=2))
