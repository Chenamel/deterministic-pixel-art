"""Build one LT05 task packet; keep assignment/evidence outside the ZIP."""
import argparse
import json
from pathlib import Path

from build_long_term_trials import ROOT, encoded, frozen_files
from prepare_agent_trials import archive_bytes, sha

EXPECTED = 'b2dcbe96443b278e2b93ef6a9e28d250d025d4c5eb4a36f7395c747086b31086'


def build(skill_zip, out, expected=EXPECTED):
    skill_zip, out = Path(skill_zip), Path(out)
    files = frozen_files(skill_zip, expected)
    count = len(files)
    files.update({
        'START_HERE.md': (ROOT/'benchmarks/long-term/LT05.md').read_bytes(),
        'run.py': (ROOT/'benchmarks/long-term/sprite_runner.py').read_bytes(),
        'recorder.py': (ROOT/'benchmarks/long-term/runner.py').read_bytes(),
        'task.json': encoded(dict(id='LT05', skill_zip_sha256=expected)),
        'inputs/brief.json': (ROOT/'benchmarks/long-term/sprite-brief.json').read_bytes(),
    })
    files['checksums.json'] = encoded({name: sha(data) for name, data in sorted(files.items())})
    payload = archive_bytes({'LT05/'+name: data for name, data in files.items()})
    out.mkdir(parents=True, exist_ok=False)
    (out/'LT05-Sprite.zip').write_bytes(payload)
    record = dict(task='LT05', archive='LT05-Sprite.zip', bytes=len(payload), sha256=sha(payload),
                  skill_zip_sha256=expected, skill_build='unversioned development snapshot, not frozen rc.6',
                  skill_files=count, packet_files=len(files), external_runs=0,
                  recommended_environment='WorkBuddy, new session', recommended_model='GLM-5.3-Flash')
    coordinator = out/'coordinator'
    coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(record))
    (coordinator/'SHA256SUMS.txt').write_text(sha(payload)+'  LT05-Sprite.zip\n', encoding='ascii')
    (coordinator/'skill-input.zip').write_bytes(skill_zip.read_bytes())
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-zip', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sha256', default=EXPECTED)
    args = parser.parse_args()
    print(json.dumps(build(args.skill_zip, args.out, args.sha256), indent=2))
