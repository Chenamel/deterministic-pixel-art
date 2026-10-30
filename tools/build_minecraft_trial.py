"""Build LT07 with task-only instructions and an exact development Skill snapshot."""
import argparse
import json
from pathlib import Path

from build_long_term_trials import ROOT, encoded, frozen_files
from prepare_agent_trials import archive_bytes, sha

EXPECTED='184e2c6ef44a0a3f3ec755a2a8c8a450787ac1944ae3a5b412ca1896ddefc0c6'


def build(skill_zip,out,expected=EXPECTED):
    skill_zip,out=Path(skill_zip),Path(out)
    files=frozen_files(skill_zip,expected)
    count=len(files)
    files.update({
        'START_HERE.md':(ROOT/'benchmarks/long-term/LT07.md').read_bytes(),
        'run.py':(ROOT/'benchmarks/long-term/minecraft_runner.py').read_bytes(),
        'recorder.py':(ROOT/'benchmarks/long-term/runner.py').read_bytes(),
        'task.json':encoded(dict(id='LT07',skill_zip_sha256=expected)),
        'inputs/brief.json':(ROOT/'benchmarks/long-term/minecraft-brief.json').read_bytes(),
    })
    files['checksums.json']=encoded({n:sha(data) for n,data in sorted(files.items())})
    payload=archive_bytes({'LT07/'+n:data for n,data in files.items()})
    out.mkdir(parents=True,exist_ok=False)
    (out/'LT07-Minecraft.zip').write_bytes(payload)
    record=dict(task='LT07',archive='LT07-Minecraft.zip',bytes=len(payload),sha256=sha(payload),
        skill_zip_sha256=expected,skill_build='unversioned guidance development snapshot; not a new RC',
        skill_files=count,packet_files=len(files),external_runs=0,
        recommended_environment='Doubao office tasks, new session',recommended_model='current platform-selected model; record actual displayed name or undisclosed')
    coordinator=out/'coordinator';coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(record))
    (coordinator/'SHA256SUMS.txt').write_text(sha(payload)+'  LT07-Minecraft.zip\n',encoding='ascii')
    (coordinator/'skill-input.zip').write_bytes(skill_zip.read_bytes())
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-zip',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--sha256',default=EXPECTED)
    args=parser.parse_args()
    print(json.dumps(build(args.skill_zip,args.out,args.sha256),indent=2))
