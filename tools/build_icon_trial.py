"""Build one LT04 creative-use packet, separate from coordinator-only records."""
import argparse
import json
from pathlib import Path

from build_long_term_trials import ROOT, encoded, frozen_files
from prepare_agent_trials import archive_bytes, sha

EXPECTED='f02be7f650df703b6935666988780154ede02851db014b903e6cae0c6cabd7ba'


def build(skill_zip, out, expected=EXPECTED):
    skill_zip, out = Path(skill_zip), Path(out)
    files=frozen_files(skill_zip,expected)
    count=len(files)
    files.update({'START_HERE.md':(ROOT/'benchmarks/long-term/LT04.md').read_bytes(),
                  'run.py':(ROOT/'benchmarks/long-term/icons_runner.py').read_bytes(),
                  'recorder.py':(ROOT/'benchmarks/long-term/runner.py').read_bytes(),
                  'task.json':encoded(dict(id='LT04',skill_zip_sha256=expected)),
                  'inputs/brief.json':(ROOT/'benchmarks/long-term/icon-brief.json').read_bytes()})
    files['checksums.json']=encoded({name:sha(data) for name,data in sorted(files.items())})
    payload=archive_bytes({'LT04/'+name:data for name,data in files.items()})
    out.mkdir(parents=True,exist_ok=False)
    (out/'LT04-Icons.zip').write_bytes(payload)
    record=dict(task='LT04',archive='LT04-Icons.zip',bytes=len(payload),sha256=sha(payload),
                skill_zip_sha256=expected,skill_build='unversioned development snapshot, not frozen rc.6',
                skill_files=count,packet_files=len(files),external_runs=0,
                recommended_environment='WorkBuddy, new session',recommended_model='Hy3',fallback_model='Space-Bunny')
    coordinator=out/'coordinator';coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(record))
    (coordinator/'SHA256SUMS.txt').write_text(sha(payload)+'  LT04-Icons.zip\n',encoding='ascii')
    (coordinator/'skill-input.zip').write_bytes(skill_zip.read_bytes())
    return record


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--skill-zip',type=Path,required=True)
    cli.add_argument('--out',type=Path,required=True)
    cli.add_argument('--sha256',default=EXPECTED)
    args=cli.parse_args()
    print(json.dumps(build(args.skill_zip,args.out,args.sha256),indent=2))
