"""Build task-only rc.5 trial packages with separate coordinator records."""
import argparse
import json
from pathlib import Path, PurePosixPath
import zipfile

from prepare_agent_trials import archive_bytes, sha

ROOT=Path(__file__).resolve().parents[1]
EXPECTED='2b9cb652fb9e4a50bd3e4d11e098003b86c6195a16c9b1730dbc6907839178a4'

def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def build(skill_zip,out,expected=EXPECTED):
    payload=skill_zip.read_bytes()
    if sha(payload)!=expected:raise ValueError('Frozen Skill ZIP SHA-256 mismatch')
    with zipfile.ZipFile(skill_zip) as bundle:
        entries=[e for e in bundle.infolist() if not e.is_dir()]
        if len({e.filename for e in entries})!=len(entries) or sum(e.file_size for e in entries)>16*1024*1024:
            raise ValueError('Duplicate entries or oversized Skill')
        for entry in entries:
            path=PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename or ':' in entry.filename:
                raise ValueError('Unsafe ZIP path')
            if not path.parts or path.parts[0]!='deterministic-pixel-art':raise ValueError('Unexpected Skill root')
        frozen={e.filename:bundle.read(e.filename) for e in entries}
    out.mkdir(parents=True,exist_ok=False)
    trials=[]
    for task,model,filename in [('LT01','GLM-5.3-Flash','LT01-AtlasEdit.zip'),
                                ('LT02','Deepseek-V4.1-Flash','LT02-Buttons.zip')]:
        files=dict(frozen)
        files['run.py']=(ROOT/'benchmarks/long-term/runner.py').read_bytes()
        files['START_HERE.md']=(ROOT/'benchmarks/long-term'/f'{task}.md').read_bytes()
        config=dict(id=task,skill_zip_sha256=expected)
        files['task.json']=encoded(config)
        if task=='LT01':
            files['inputs/atlas.png']=frozen['deterministic-pixel-art/assets/workflows/atlas-before.png']
            files['inputs/layout.json']=frozen['deterministic-pixel-art/assets/workflows/atlas-before-layout.json']
        else:
            for source,target in [('Silkscreen-Regular.ttf','Silkscreen-Regular.ttf'),('OFL.txt','OFL.txt'),
                                  ('source.json','font-source.json')]:
                files['inputs/'+target]=(ROOT/'demos/pixel-ui/fonts'/source).read_bytes()
        files['checksums.json']=encoded({name:sha(data) for name,data in sorted(files.items())})
        payload=archive_bytes({task+'/'+name:data for name,data in files.items()})
        (out/filename).write_bytes(payload)
        trials.append(dict(task=task,recommended_model=model,archive=filename,bytes=len(payload),sha256=sha(payload)))
    coordinator=out/'coordinator'
    coordinator.mkdir()
    (coordinator/'manifest.json').write_bytes(encoded(dict(
        distribution='20261028-task-only',skill_zip_sha256=expected,trials=trials,external_runs=0)))
    (coordinator/'SHA256SUMS.txt').write_text(''.join(f"{t['sha256']}  {t['archive']}\n" for t in trials),encoding='ascii')
    (coordinator/'README.md').write_text(
        '# 分发记录（不发送给被测模型）\n\n'
        '执行者只接收对应任务ZIP；模型分配与校验清单留在本目录。\n'
        '收到产物后，另行整理仅含需求和图片的看图包，再交给审阅者。\n',encoding='utf-8')
    print(json.dumps(dict(prepared=len(trials),external_runs=0,trials=trials),indent=2))
    return trials

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-zip',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    build(args.skill_zip,args.out)
