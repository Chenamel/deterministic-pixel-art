"""Build LT08 task-only packet; assignment stays in a sibling coordinator folder."""
import argparse
import json
from pathlib import Path
from build_long_term_trials import ROOT, encoded, frozen_files
from prepare_agent_trials import archive_bytes, sha

EXPECTED='184e2c6ef44a0a3f3ec755a2a8c8a450787ac1944ae3a5b412ca1896ddefc0c6'

def build(skill_zip,out,expected=EXPECTED):
    skill_zip,out=Path(skill_zip),Path(out)
    files=frozen_files(skill_zip,expected);count=len(files)
    files.update({
        'START_HERE.md':(ROOT/'benchmarks/long-term/LT08.md').read_bytes(),
        'run.py':(ROOT/'benchmarks/long-term/chunk_runner.py').read_bytes(),
        'recorder.py':(ROOT/'benchmarks/long-term/runner.py').read_bytes(),
        'task.json':encoded(dict(id='LT08',skill_zip_sha256=expected)),
        'inputs/brief.json':(ROOT/'benchmarks/long-term/chunk-brief.json').read_bytes(),
    })
    files['checksums.json']=encoded({n:sha(v) for n,v in sorted(files.items())})
    payload=archive_bytes({'LT08/'+n:v for n,v in files.items()})
    out.mkdir(parents=True,exist_ok=False);(out/'LT08-Chunks.zip').write_bytes(payload)
    record=dict(task='LT08',archive='LT08-Chunks.zip',bytes=len(payload),sha256=sha(payload),
        skill_zip_sha256=expected,skill_files=count,packet_files=len(files),external_runs=0,
        skill_build='unchanged unversioned development snapshot, not a new candidate',
        recommended_environment='WorkBuddy, new session',recommended_model='MiniMax-M3.1-Flash')
    coordinator=out/'coordinator';coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(record))
    (coordinator/'SHA256SUMS.txt').write_text(sha(payload)+'  LT08-Chunks.zip\n',encoding='ascii')
    (coordinator/'skill-input.zip').write_bytes(skill_zip.read_bytes())
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill-zip',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--sha256',default=EXPECTED);args=p.parse_args()
    print(json.dumps(build(args.skill_zip,args.out,args.sha256),indent=2))
