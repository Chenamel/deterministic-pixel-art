"""Split a released agent bundle into 16 fresh-session ZIPs; never run agents."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text_arg(value):
    if not value.strip() or len(value) > 200 or any(ord(c) < 32 for c in value):
        raise argparse.ArgumentTypeError('use a nonempty, single-line value of at most 200 characters')
    return value


def template_path():
    here = Path(__file__).resolve().parent
    for path in (here.parent / 'benchmarks/prompts/paired-task.zh-CN.md',
                 here / 'prompts/paired-task.zh-CN.md'):
        if path.is_file():
            return path
    raise ValueError('prompt template not found; pass --template')


def archive_bytes(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data)
    return buffer.getvalue()


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--expected-sha256', help='release agent ZIP digest from SHA256SUMS.txt')
    parser.add_argument('--out', type=Path, required=True, help='new directory; existing directories are refused')
    parser.add_argument('--environment', type=text_arg, required=True)
    parser.add_argument('--model', type=text_arg, required=True)
    parser.add_argument('--mode', choices=['text_only', 'multimodal'], required=True)
    parser.add_argument('--order', choices=['forward', 'reverse'], default='forward')
    parser.add_argument('--template', type=Path)
    args = parser.parse_args()
    outer = args.bundle.read_bytes()
    if args.expected_sha256 and sha(outer) != args.expected_sha256.lower():
        raise ValueError('release agent ZIP checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(outer)) as bundle:
        infos = [item for item in bundle.infolist() if not item.is_dir()]
        names = [item.filename for item in infos]
        if len(set(names)) != len(names):
            raise ValueError('duplicate ZIP entries')
        for item in infos:
            path = PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in item.filename or ':' in item.filename:
                raise ValueError('unsafe ZIP entry')
        if sum(item.file_size for item in infos) > 16 * 1024 * 1024:
            raise ValueError('unexpected bundle size; use the released evaluation ZIP')
        files = {name: bundle.read(name) for name in names}
    checks = json.loads(files['checksums.json'])
    if set(files) != set(checks) | {'checksums.json'} or any(sha(files[n]) != h for n, h in checks.items()):
        raise ValueError('agent bundle internal checksum mismatch')
    if not {'packages/A.zip', 'packages/B.zip', 'runner.py', 'README.md'} <= set(files):
        raise ValueError('expected released agent bundle with A/B packages')
    tasks = sorted(name.split('/')[1] for name in files
                   if re.fullmatch(r'tasks/[a-z0-9-]+/request\.md', name))
    if len(tasks) != 8:
        raise ValueError('expected eight fixed tasks')
    template = (args.template or template_path()).read_text(encoding='utf-8')
    variables = {'ENVIRONMENT': args.environment, 'MODEL': args.model, 'MODE': args.mode,
                 'TASK': '', 'PACKAGE': ''}
    if set(re.findall(r'\{\{([A-Z_]+)\}\}', template)) != set(variables):
        raise ValueError('template must contain exactly ENVIRONMENT/MODEL/MODE/TASK/PACKAGE fields')
    output = args.out.resolve()
    if output.exists():
        raise ValueError('output already exists; choose a new directory')
    output.mkdir(parents=True)
    schedule = []
    for index, task in enumerate(tasks):
        labels = ('A', 'B') if (index + (args.order == 'reverse')) % 2 == 0 else ('B', 'A')
        for label in labels:
            variables.update(TASK=task, PACKAGE=label)
            prompt = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: variables[m[1]], template)
            session = dict(environment=args.environment, model=args.model, mode=args.mode,
                           task=task, package=label, package_sha256=sha(files[f'packages/{label}.zip']),
                           source_bundle_sha256=sha(outer), external_agent_executed=False)
            contents = {'PROMPT.md': prompt.encode('utf-8'), 'package.zip': files[f'packages/{label}.zip'],
                        'runner.py': files['runner.py'], 'protocol.md': files['README.md'],
                        'session.json': json.dumps(session, ensure_ascii=False, indent=2).encode('utf-8')}
            prefix = 'tasks/' + task + '/'
            contents.update({'task/' + name[len(prefix):]: data for name, data in files.items() if name.startswith(prefix)})
            contents['checksums.json'] = json.dumps({n: sha(data) for n, data in sorted(contents.items())}, indent=2).encode('utf-8')
            name = f'{len(schedule)+1:02}-{task}-{label}.zip'
            payload = archive_bytes(contents)
            (output / name).write_bytes(payload)
            schedule.append(dict(sequence=len(schedule)+1, task=task, package=label,
                                 session_zip=name, session_zip_sha256=sha(payload),
                                 prompt_sha256=sha(contents['PROMPT.md'])))
    with (output / 'schedule.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(schedule[0]))
        writer.writeheader()
        writer.writerows(schedule)
    (output / 'coordinator.json').write_text(json.dumps(dict(environment=args.environment,
        model=args.model, mode=args.mode, source_bundle_sha256=sha(outer), sessions=schedule,
        external_runs=0), ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'README.txt').write_text('每个 ZIP 用一个全新会话，只发该 ZIP，并让 AI 按 PROMPT.md 执行。\n'
        '按 schedule.csv 顺序分发；不要将整个目录、另一包、验收包或版本键交给被测 AI。\n'
        '每次收回 RUN ZIP 和原始可见会话；保留失败记录。生成分发包不等于完成测评。\n', encoding='utf-8')
    print(json.dumps(dict(prepared_sessions=len(schedule), external_runs=0, output=str(output)), ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
