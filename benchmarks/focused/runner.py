"""Small focused-trial recorder. Does not solve the requested editing task."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

BASE=Path(__file__).resolve().parent
RUN=BASE/'RUN'


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()


def integrity():
    missing=[]
    for name,digest in read(BASE/'checksums.json').items():
        path=(BASE/name).resolve()
        if not path.is_relative_to(BASE.resolve()):raise ValueError('unsafe checksum path')
        if not path.is_file() or sha(path)!=digest:missing.append(name)
    if missing:raise ValueError('Frozen input/Skill changed: '+', '.join(missing[:8]))


def environment():
    result=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
                pillow=None,pillow_file=None)
    try:
        import PIL
        result.update(pillow=PIL.__version__,pillow_file=PIL.__file__)
    except ImportError:pass
    return result


def snapshots(arguments):
    paths=[]
    for index,value in enumerate(arguments[:-1]):
        if value in ('--out','--preview','--metadata','--image-out','--seams','--report'):
            paths.append(BASE/arguments[index+1])
        elif value=='--out-dir':
            paths.extend(BASE/arguments[index+1]/name for name in ('report.json','review.png','difference.png'))
    result={}
    for path in paths:
        resolved=path.resolve()
        if resolved.is_relative_to(RUN.resolve()):
            result[resolved.relative_to(BASE.resolve()).as_posix()]=sha(resolved) if resolved.is_file() else None
    return result


def tool(arguments):
    if not (RUN/'session.json').is_file():raise ValueError('Run start first')
    integrity()
    if not arguments:raise ValueError('tool requires pixel_art.py arguments')
    command=[sys.executable,'-B',str(BASE/'deterministic-pixel-art/scripts/pixel_art.py'),*arguments]
    before=snapshots(arguments);started=now();timer=time.perf_counter()
    result=subprocess.run(command,cwd=BASE,capture_output=True,text=True,encoding='utf-8',timeout=120)
    record=dict(started_utc=started,arguments=arguments,environment=environment(),
        elapsed_seconds=time.perf_counter()-timer,exit_code=result.returncode,
        stdout=result.stdout,stderr=result.stderr,outputs_before=before,outputs_after=snapshots(arguments))
    with (RUN/'commands.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
    return result.returncode


def check():
    integrity()
    sys.path.insert(0,str(BASE/'deterministic-pixel-art/scripts'))
    from PIL import Image
    from pixelart import render,verify_edit
    from pixelart.metadata import layout_record,merge_layout
    task=read(BASE/'task.json');checks=[]
    def add(name,passed,**facts):checks.append(dict(check=name,passed=bool(passed),**facts))
    def image(path):
        with Image.open(path) as opened:return opened.convert('RGBA')
    def editable(stem,baseline,region=None,mask=None):
        candidate=image(RUN/(stem+'.png'));rebuilt=render(read(RUN/(stem+'.json')))
        add(stem+'-rerenders',candidate.size==rebuilt.size and candidate.tobytes()==rebuilt.tobytes())
        if mask:
            with Image.open(BASE/mask) as allowed:
                difference=verify_edit(candidate,image(BASE/baseline),mask=allowed.copy())
        else:difference=verify_edit(candidate,image(BASE/baseline),regions=[region])
        add(stem+'-edit-boundary',difference['valid'] and difference['changed_rgba_pixels']>0,**difference)
        if stem!='hover':
            sidecar=read(RUN/'final-layout.json');merge_layout(candidate,metadata=sidecar)
            add('atlas-layout-preserved',sidecar['atlas']==read(BASE/'inputs/layout.json')['atlas'])
        return candidate
    try:
        if task['id']=='P1-W':
            editable('final','inputs/atlas.png',[32,0,16,16])
            hover=editable('hover','inputs/hover.png',mask='inputs/allowed-ring.png')
            with Image.open(BASE/'inputs/allowed-ring.png') as allowed:
                pixels=allowed.convert('L').tobytes();raw=hover.tobytes()
                add('every-ring-pixel-gold',all(raw[i*4:i*4+4]==bytes((245,194,107,255))
                    for i,value in enumerate(pixels) if value))
        elif task['id']=='P1-V':
            editable('final','inputs/materials.png',task['allowed_region'])
            for name in ('before-review','review'):
                report=read(RUN/name/'report.json')
                add(name+'-light-primary',report['facts']['primary_background']=='light')
                ink=report['facts'].get('silhouette_color')
                add(name+'-visible-silhouette',ink==[0,0,0,255])
                add(name+'-sheet-exists',(RUN/name/'review.png').is_file())
            add('visual-notes-present',(RUN/'visual-notes.md').is_file(),
                note='Presence is not independent visual acceptance; coordinator reviews actual observations.')
        else:
            portable=RUN/'portable.png';expected=render(read(BASE/'inputs/panel.json'))
            add('portable-rgba',image(portable).tobytes()==expected.tobytes())
            add('preview-and-review',(RUN/'portable-preview.png').is_file() and (RUN/'review/report.json').is_file())
            records=[json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
            rejected=[r for r in records if r['arguments'][:1]==['render'] and '--portable-output' in r['arguments']
                and '--force' not in r['arguments'] and r['exit_code']==2
                and r['outputs_before'].get('RUN/portable.png') is not None
                and r['outputs_before'].get('RUN/portable.png')==r['outputs_after'].get('RUN/portable.png')]
            add('no-clobber-demonstrated',bool(rejected))
            add('native-render-attempt-recorded',any(r['arguments'][:1]==['render']
                and '--portable-output' not in r['arguments'] and '--force' not in r['arguments'] for r in records))
            add('environment-notes-present',(RUN/'environment-notes.md').is_file(),
                note='Original mount identity and setup failures require manual verification.')
    except (OSError,ValueError,KeyError) as exc:
        add('required-artifacts',False,error=str(exc))
    add('feedback-present',(RUN/'feedback.md').is_file(),
        note='Coordinator still reviews whether feedback contains concrete observations.')
    result=dict(task=task['id'],passed=bool(checks) and all(c['passed'] for c in checks),checks=checks,
        checked_utc=now(),validation='Engineering contracts only; no automatic aesthetic or independent-agent acceptance.')
    save(RUN/'checks.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    start=sub.add_parser('start');start.add_argument('--model',required=True)
    execute=sub.add_parser('tool');execute.add_argument('arguments',nargs=argparse.REMAINDER)
    sub.add_parser('check');sub.add_parser('finish')
    args=parser.parse_args()
    if args.command=='start':
        integrity()
        if not args.model.strip():raise ValueError('model: use the platform-visible name')
        if RUN.exists():raise ValueError('RUN already exists; use a fresh extracted task folder')
        RUN.mkdir();save(RUN/'session.json',dict(task=read(BASE/'task.json')['id'],model=args.model,
            started_utc=now(),environment=environment(),token_usage=None,
            task_sha256=sha(BASE/'task.json'),skill_sha256=read(BASE/'task.json')['skill_zip_sha256']))
        print('RUN ready. Dependency setup may be completed before the recorded tool commands.');return 0
    if args.command=='tool':return tool(args.arguments)
    if not (RUN/'session.json').is_file():raise ValueError('Run start first')
    try:result=check()
    except ImportError as exc:
        save(RUN/'checks.json',dict(passed=False,checks=[dict(check='dependencies',passed=False,error=str(exc))]))
        print(json.dumps(dict(error=str(exc),note='Dependency failure preserved; finish can still archive RUN.')))
        result=1
    if args.command=='finish':
        destination=BASE/('submission-'+read(BASE/'task.json')['id']+'.zip')
        if destination.exists():raise ValueError('Submission already exists; preserve it and use a new task folder')
        paths=sorted(RUN.rglob('*'))
        if any(path.is_symlink() for path in paths):raise ValueError('RUN contains a symlink; keep regular result files')
        with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in paths:
                if path.is_file():archive.write(path,path.relative_to(BASE).as_posix())
        print(json.dumps(dict(submission=str(destination),complete=result==0,
            note='Failures remain submitable; include available conversation separately.')))
    return result


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,ImportError,subprocess.TimeoutExpired) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
