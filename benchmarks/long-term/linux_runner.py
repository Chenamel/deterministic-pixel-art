"""LT03 engineering checks over the shared recorder; not a drawing solution."""
import json
from pathlib import Path
import sys

import recorder

BASE, RUN = recorder.BASE, recorder.RUN
_environment = recorder.environment


def environment():
    facts = _environment()
    facts.update(prefix=sys.prefix, base_prefix=sys.base_prefix)
    return facts


def check():
    recorder.integrity()
    checks = []

    def add(name, passed, **facts):
        checks.append(dict(check=name, passed=bool(passed), **facts))

    def image(path):
        from PIL import Image
        with Image.open(path) as opened:
            return opened.convert('RGBA')

    try:
        sys.path.insert(0, str(BASE/'deterministic-pixel-art/scripts'))
        from PIL import Image
        from pixelart import render
        records = [json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        tools = [r for r in records if r['kind']=='tool']
        for name in ('rgba', 'rgb', 'indexed'):
            source = image(BASE/'inputs'/f'{name}.png')
            actual = image(RUN/'roundtrip'/f'{name}.png')
            spec = recorder.read(RUN/'roundtrip'/f'{name}.json')
            rebuilt = render(spec)
            add(name+'-lossless-rgba', source.size==actual.size and source.tobytes()==actual.tobytes())
            add(name+'-editable-rerenders', rebuilt.size==actual.size and rebuilt.tobytes()==actual.tobytes())
            # Command logs establish the actual Skill path, not just matching final artifacts.
            for command in ('import', 'render'):
                flag, suffix = ('--image', '.png') if command=='import' else ('--spec', '.json')
                expected = ('inputs/' if command=='import' else 'RUN/roundtrip/')+name+suffix
                add(name+'-'+command+'-recorded', any(r['arguments'][1:2]==[command] and
                    flag in r['arguments'] and r['arguments'][r['arguments'].index(flag)+1].replace('\\','/')==expected and
                    r['exit_code']==0 for r in tools))
        expected = render(recorder.read(BASE/'inputs/panel.json'))
        actual = image(RUN/'portable/panel.png')
        add('portable-panel-rgba', actual.size==expected.size and actual.tobytes()==expected.tobytes())
        scale=8
        background=Image.new('RGBA',actual.size,'#E9EDF2')
        preview=Image.alpha_composite(background,actual).resize((actual.width*scale,actual.height*scale),Image.Resampling.NEAREST)
        supplied=image(RUN/'portable/preview.png')
        add('portable-preview-background-scale', supplied.size==preview.size and supplied.tobytes()==preview.tobytes())
        native=[r for r in tools if r['arguments'][1:2]==['render'] and '--portable-output' not in r['arguments'] and
                '--force' not in r['arguments'] and '--out' in r['arguments'] and
                r['arguments'][r['arguments'].index('--out')+1].replace('\\','/')=='RUN/native/panel.png']
        add('native-attempt-recorded', bool(native), exit_codes=[r['exit_code'] for r in native])
        if any(r['exit_code']==0 for r in native):
            actual_native=image(RUN/'native/panel.png')
            add('native-panel-rgba',actual_native.size==expected.size and actual_native.tobytes()==expected.tobytes())
        rejected=[r for r in tools if r['arguments'][1:2]==['render'] and '--portable-output' in r['arguments'] and
                  '--force' not in r['arguments'] and r['exit_code']==2 and
                  r['outputs_before'].get('portable/panel.png') is not None and
                  r['outputs_before'].get('portable/panel.png')==r['outputs_after'].get('portable/panel.png') and
                  r['outputs_before']==r['outputs_after']]
        add('portable-no-clobber-recorded', bool(rejected))
        report=recorder.read(RUN/'review/report.json')
        with Image.open(RUN/'review/review.png') as sheet:
            sheet.load()
            add('review-sheet-readable',sheet.width>0 and sheet.height>0)
        add('review-report-present',isinstance(report,dict) and bool(report))
        add('consistent-interpreter',bool(records) and all(
            r['environment']['executable']==recorder.read(RUN/'session.json')['environment']['executable'] for r in records))
    except (ImportError,OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        add('required-artifacts',False,error=str(exc))
    for name in ('environment-notes.md','feedback.md'):
        add(name+'-present',(RUN/name).is_file() and bool((RUN/name).read_text(encoding='utf-8').strip()))
    result=dict(task='LT03',passed=bool(checks) and all(c['passed'] for c in checks),checks=checks,
                checked_utc=recorder.now(),scope='Engineering only. Actual Linux/mount identity and visual observations need coordinator review.')
    recorder.save(RUN/'checks.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


def main():
    recorder.check=check
    recorder.environment=environment
    code=recorder.main()
    if sys.argv[1:2]==['start']:
        session=recorder.read(RUN/'session.json')
        session['cohort']='linux-portable-rc6'
        recorder.save(RUN/'session.json',session)
    return code


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,ValueError,ImportError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
