"""Record real paired-task execution; requires only the Python standard library."""
import argparse
from datetime import datetime,timezone
import hashlib
from importlib.metadata import version,PackageNotFoundError
import json
from pathlib import Path
import platform
import subprocess
import sys
import time


def now():return datetime.now(timezone.utc).isoformat()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def main(argv=None):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='action',required=True)
    start=commands.add_parser('start');start.add_argument('--out',type=Path,required=True)
    start.add_argument('--task',required=True);start.add_argument('--package',choices=['A','B'],required=True)
    start.add_argument('--package-zip',type=Path,required=True);start.add_argument('--environment',required=True)
    start.add_argument('--mode',choices=['text_only','multimodal'],required=True);start.add_argument('--model',required=True)
    start.add_argument('--shim',action='store_true')
    run=commands.add_parser('run');run.add_argument('--out',type=Path,required=True)
    run.add_argument('command',nargs=argparse.REMAINDER)
    finish=commands.add_parser('finish');finish.add_argument('--out',type=Path,required=True)
    finish.add_argument('--candidates',type=int,choices=[1,2],required=True)
    finish.add_argument('--revisions',type=int,choices=[0,1,2],required=True)
    finish.add_argument('--tokens',type=int)
    finish.add_argument('--failure-stage',choices=['none','environment','localization','repair'],default='none')
    args=parser.parse_args(argv);folder=args.out.resolve();record=folder/'run.json'
    if args.action=='start':
        if record.exists():raise ValueError('run already exists; use a fresh conversation and directory')
        folder.mkdir(parents=True,exist_ok=True)
        try:pillow=version('Pillow')
        except PackageNotFoundError:pillow=None
        save(record,dict(version=1,task=args.task,package=args.package,
            package_sha256=digest(args.package_zip),environment=args.environment,mode=args.mode,
            model=args.model,python=platform.python_version(),pillow=pillow,platform=platform.platform(),
            shim=args.shim,started_at=now(),finished_at=None,tokens_total=None))
        (folder/'commands.jsonl').touch()
    else:
        data=json.loads(record.read_text(encoding='utf-8'))
        if data['finished_at'] is not None:raise ValueError('run is already finished')
        if args.action=='run':
            command=args.command[1:] if args.command[:1]==['--'] else args.command
            if not command:raise ValueError('provide an executable and arguments after --')
            log=folder/'commands.jsonl';index=len(log.read_text(encoding='utf-8').splitlines())+1
            started=now();timer=time.perf_counter()
            result=subprocess.run(command,cwd=folder,capture_output=True)
            elapsed=time.perf_counter()-timer
            stdout=folder/f'{index:03}.stdout.txt';stderr=folder/f'{index:03}.stderr.txt'
            stdout.write_bytes(result.stdout);stderr.write_bytes(result.stderr)
            item=dict(command=command,started_at=started,seconds=elapsed,exit_code=result.returncode,
                stdout=stdout.name,stderr=stderr.name,
                localization_sha256=digest(folder/'localization.json') if (folder/'localization.json').exists() else None)
            with log.open('a',encoding='utf-8') as handle:handle.write(json.dumps(item,ensure_ascii=False)+'\n')
            sys.stdout.write(result.stdout.decode('utf-8',errors='replace'))
            sys.stderr.write(result.stderr.decode('utf-8',errors='replace'))
            return result.returncode
        if args.tokens is not None and args.tokens<0:raise ValueError('tokens must be an actual nonnegative count or omitted')
        required=['commands.jsonl','localization.json','final.json','final.png']
        if args.failure_stage=='none' and not all((folder/name).is_file() for name in required):
            raise ValueError('successful finish requires localization.json, final.json, final.png and command log')
        artifacts={p.name:digest(p) for p in folder.iterdir() if p.is_file() and p.name!='run.json'}
        data.update(finished_at=now(),candidates=args.candidates,revisions=args.revisions,
                    tokens_total=args.tokens,failure_stage=args.failure_stage,artifacts=artifacts)
        save(record,data)
    print(json.dumps(dict(record=str(record),action=args.action)))
    return 0


if __name__=='__main__':raise SystemExit(main())
