"""Record single-version usability trials. Checks are not aesthetic or A/B evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

BASE = Path(__file__).resolve().parent
RUN = BASE / 'RUN'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def integrity():
    for name, digest in read(BASE / 'checksums.json').items():
        path = BASE / name
        if not path.resolve().is_relative_to(BASE.resolve()) or path.is_symlink():
            raise ValueError('Unsafe frozen input path')
        if not path.is_file() or sha(path) != digest:
            raise ValueError('Frozen task/Skill changed: '+name)

def environment():
    result = dict(python=sys.version, executable=sys.executable, platform=platform.platform(), pillow=None)
    try:
        import PIL
        result.update(pillow=PIL.__version__, pillow_file=PIL.__file__)
    except ImportError:
        pass
    return result

def artifacts():
    paths = sorted(RUN.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('RUN must contain regular files, no symlinks')
    files = [p for p in paths if p.is_file()]
    if len(files)>512 or sum(p.stat().st_size for p in files)>32*1024*1024:
        raise ValueError('RUN exceeds 512 files or 32 MiB; crop/remove unrelated files before archiving')
    return files

def snapshot():
    return {p.relative_to(RUN).as_posix():sha(p) for p in artifacts()
            if p.name not in ('commands.jsonl', 'session.json', 'checks.json')}

def execute(kind, arguments):
    integrity()
    if not arguments:
        raise ValueError('Expected command arguments')
    if kind=='tool':
        script=BASE/'deterministic-pixel-art/scripts/pixel_art.py'
    else:
        script=(BASE/arguments[0]).resolve()
        if not script.is_relative_to(BASE.resolve()) or script.suffix!='.py' or not script.is_file():
            raise ValueError('script: expected a .py file inside this extracted task')
        arguments=arguments[1:]
    command=[sys.executable,'-B',str(script),*arguments]
    before=snapshot();started=now();timer=time.perf_counter()
    try:
        result=subprocess.run(command,cwd=BASE,capture_output=True,timeout=120)
        code=result.returncode;stdout=result.stdout;stderr=result.stderr
    except subprocess.TimeoutExpired as exc:
        code=124;stdout=exc.stdout or b'';stderr=(exc.stderr or b'')+b'\nRecorder timeout after 120 seconds.'
    record=dict(kind=kind,arguments=command[2:],started_utc=started,environment=environment(),
                elapsed_seconds=time.perf_counter()-timer,exit_code=code,
                stdout=stdout.decode('utf-8',errors='replace'),stderr=stderr.decode('utf-8',errors='replace'),
                outputs_before=before,outputs_after=snapshot())
    with (RUN/'commands.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(record,ensure_ascii=False)+'\n')
    print(record['stdout'],end='');print(record['stderr'],end='',file=sys.stderr)
    return code

def check():
    integrity()
    checks=[]
    def add(name, passed, **facts):
        checks.append(dict(check=name,passed=bool(passed),**facts))
    try:
        sys.path.insert(0,str(BASE/'deterministic-pixel-art/scripts'))
        from PIL import Image, ImageDraw, ImageFont
        from pixelart import render, verify_edit, inspect_image, color
        from pixelart.metadata import merge_layout
        spec=read(RUN/'final.json');rebuilt=render(spec)
        with Image.open(RUN/'final.png') as source:
            image=source.convert('RGBA')
        add('spec-rerenders',image.size==rebuilt.size and image.tobytes()==rebuilt.tobytes())
        metadata=read(RUN/'final-layout.json');merge_layout(image,metadata=metadata)
        add('fresh-layout',metadata['atlas']==rebuilt.info.get('pixelart'))
        if read(BASE/'task.json')['id']=='LT01':
            with Image.open(BASE/'inputs/atlas.png') as opened:
                difference=verify_edit(image,opened.convert('RGBA'),regions=[[32,0,16,16]])
            add('only-target-changed',difference['valid'] and difference['changed_rgba_pixels']>0,**difference)
            add('original-layout-retained',metadata['atlas']==read(BASE/'inputs/layout.json')['atlas'])
        else:
            names=['normal','hover','focus','pressed','selected','disabled']
            cells=metadata['atlas']['cells']
            add('six-named-states',[c['name'] for c in cells]==names)
            add('uniform-even-width-18px',all(c['h']==18 and 24<=c['w']<=112 and c['w']%2==0
                                            and c['w']==cells[0]['w'] for c in cells))
            context=read(RUN/'context.json');inspect_image(image,context,metadata=metadata)
            font=ImageFont.truetype(str(BASE/'inputs/Silkscreen-Regular.ttf'),8)
            boxes={text:list(font.getbbox(text)) for text in ['START','LOOP','EXPORT MAP']}
            for cell in cells:
                regions=[r for r in context.get('regions',[]) if r.get('name')==cell['name']+'-text'
                         and r.get('role')=='reserved_text']
                if len(regions)!=1:
                    add(cell['name']+'-text-region',False);continue
                x,y,w,h=regions[0]['rect'];local_x=x-cell['x'];local_y=y-cell['y']
                fits=local_x>=23 and local_y>=4 and local_x+w<=cell['w']-2 and local_y+h<=14
                fits=fits and all(box[2]-box[0]+4<=w and box[3]-box[1]+4<=h for box in boxes.values())
                add(cell['name']+'-font-capacity',fits,font_size=8,label_bboxes=boxes,rect=[x,y,w,h])
            fit=read(RUN/'text-fit.json');labels=['START','LOOP','EXPORT MAP']
            add('font-size-record',fit.get('font_size')==8)
            instances=fit['instances'];keys=[(item['state'],item['label']) for item in instances]
            required={(state,label) for state in names for label in labels}
            if len(keys)!=18 or set(keys)!=required:raise ValueError('text-fit.instances: expected each state/label exactly once')
            width=cells[0]['w'];consumer=Image.new('RGBA',(3*width,6*18))
            for row,cell in enumerate(cells):
                for col,label in enumerate(labels):
                    consumer.paste(image.crop((cell['x'],cell['y'],cell['x']+width,cell['y']+18)),(col*width,row*18))
            pen=ImageDraw.Draw(consumer)
            for item in instances:
                row=names.index(item['state']);col=labels.index(item['label']);cell=cells[row]
                rect=next(r['rect'] for r in context['regions'] if r['name']==item['state']+'-text')
                x=col*width+rect[0]-cell['x'];y=row*18+rect[1]-cell['y'];w,h=rect[2:]
                origin=item['origin']
                if len(origin)!=2 or any(type(v) is not int for v in origin):raise ValueError('text origin: expected two integers')
                tx,ty=origin;box=boxes[item['label']]
                add(item['state']+'-'+item['label']+'-placement',
                    tx+box[0]>=x+2 and ty+box[1]>=y+2 and tx+box[2]<=x+w-2 and ty+box[3]<=y+h-2)
                ink=color(item.get('color','8997A5' if item['state']=='disabled' else 'E5ECEE'))
                if ink[3]!=255:raise ValueError('consumer text: use an opaque color')
                pen.text(origin,item['label'],font=font,fill=ink)
            for filename,expected in [('consumer.png',consumer),
                ('consumer-3x.png',consumer.resize((consumer.width*3,consumer.height*3),Image.Resampling.NEAREST))]:
                with Image.open(RUN/filename) as opened:actual=opened.convert('RGBA')
                add(filename+'-font-rebuild',actual.size==expected.size and actual.tobytes()==expected.tobytes())
        add('initial-notes-present',(RUN/'initial-notes.md').is_file())
        add('feedback-present',(RUN/'feedback.md').is_file())
    except (ImportError,OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        add('required-artifacts',False,error=str(exc))
    result=dict(task=read(BASE/'task.json')['id'],passed=bool(checks) and all(c['passed'] for c in checks),
                checks=checks,checked_utc=now(),scope='Engineering only; no model benefit, direction or aesthetic acceptance.')
    save(RUN/'checks.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1

def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    start=sub.add_parser('start');start.add_argument('--platform',required=True);start.add_argument('--model',required=True)
    for name in ('tool','script'):
        execute_cmd=sub.add_parser(name);execute_cmd.add_argument('arguments',nargs=argparse.REMAINDER)
    sub.add_parser('check')
    finish=sub.add_parser('finish');finish.add_argument('--status',choices=['complete','blocked','quota_limited'],required=True)
    args=parser.parse_args();integrity()
    if args.action=='start':
        if not args.platform.strip() or not args.model.strip():raise ValueError('Record actual platform/model')
        RUN.mkdir(exist_ok=False)
        save(RUN/'session.json',dict(task=read(BASE/'task.json')['id'],cohort='long-term-rc5-wave1',
            platform=args.platform,model=args.model,started_utc=now(),environment=environment(),tokens=None,
            task_sha256=sha(BASE/'task.json'),skill_zip_sha256=read(BASE/'task.json')['skill_zip_sha256']))
        (RUN/'commands.jsonl').touch();print('RUN ready');return 0
    if not (RUN/'session.json').is_file():raise ValueError('Run start first')
    if read(RUN/'session.json').get('finished_utc'):raise ValueError('Run already finished; use a fresh extraction')
    if args.action in ('tool','script'):return execute(args.action,args.arguments)
    code=check()
    if args.action=='finish':
        target=BASE/('submission-'+read(BASE/'task.json')['id']+'.zip')
        if target.exists():raise ValueError('Submission already exists; preserve it')
        session=read(RUN/'session.json');session.update(finished_utc=now(),submitted_status=args.status,
                                                     engineering_checks_passed=code==0)
        save(RUN/'session.json',session)
        with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in artifacts():bundle.write(path,'RUN/'+path.relative_to(RUN).as_posix())
        print(json.dumps(dict(submission=str(target),reported_status=args.status,engineering_checks_passed=code==0)))
    return code

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,ImportError,subprocess.TimeoutExpired) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
