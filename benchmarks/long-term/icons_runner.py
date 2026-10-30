"""LT04 artifact contracts over the shared command recorder."""
import json
import os
from pathlib import Path
import sys

import recorder

BASE, RUN = recorder.BASE, recorder.RUN
_environment = recorder.environment


def environment():
    facts = _environment()
    facts.update(prefix=sys.prefix, base_prefix=sys.base_prefix,
                 portable_output_setting=os.environ.get('PIXELART_PORTABLE_OUTPUT'))
    return facts


def check():
    recorder.integrity()
    checks = []

    def add(name, passed, **facts):
        checks.append(dict(check=name, passed=bool(passed), **facts))

    def image(path):
        from PIL import Image
        with Image.open(path) as source:
            return source.convert('RGBA')

    try:
        sys.path.insert(0, str(BASE/'deterministic-pixel-art/scripts'))
        from pixelart import render, make_preview, verify_edit
        from pixelart.compat import pixels, require_pillow
        from pixelart.metadata import layout_record
        require_pillow()
        brief = recorder.read(BASE/'inputs/brief.json')
        assets, layouts, colors = {}, {}, set()
        for stage, group in [('v1', 'directions'), ('v1', 'actions'), ('v2', 'actions')]:
            key = stage+'/'+group
            folder = RUN/stage
            expected = render(recorder.read(folder/(group+'.json')))
            actual = image(folder/(group+'.png'))
            metadata = recorder.read(folder/(group+'-layout.json'))
            add(key+'-editable-rerenders', actual.size==expected.size and actual.tobytes()==expected.tobytes())
            expected_metadata = json.loads(json.dumps(layout_record(expected)))
            add(key+'-fresh-layout', metadata==expected_metadata)
            unit = brief[group]['cell_size']
            names = brief[group]['names']
            atlas = expected.info.get('pixelart')
            wanted = dict(cell_size=[unit, unit], columns=4, rows=1,
                cells=[dict(name=name, x=i*unit, y=0, w=unit, h=unit) for i, name in enumerate(names)])
            add(key+'-named-native-cells', actual.size==(unit*4, unit) and atlas==wanted)
            alpha = set(pixels(actual.getchannel('A')))
            add(key+'-binary-alpha', alpha<=set(brief['allowed_alpha']))
            signatures = []
            for index, name in enumerate(names):
                cell = actual.crop((index*unit, 0, (index+1)*unit, unit))
                values = list(pixels(cell))
                colors.update(p for p in values if p[3]>0)
                add(key+'/'+name+'-nonempty', any(p[3] for p in values))
                edge = [cell.getpixel((x, y))[3] for y in range(unit) for x in range(unit)
                        if min(x, y, unit-1-x, unit-1-y)<brief['transparent_border']]
                add(key+'/'+name+'-transparent-border', not any(edge))
                signatures.append(b''.join(bytes(p if p[3] else (0, 0, 0, 0)) for p in values))
            add(key+'-distinct-visible-cells', len(set(signatures))==len(names))
            assets[key], layouts[key] = actual, metadata
        add('shared-visible-color-budget', len(colors)<=brief['visible_color_limit'], count=len(colors))
        add('revision-layout-retained', layouts['v1/actions']['atlas']==layouts['v2/actions']['atlas'])
        difference = verify_edit(assets['v2/actions'], assets['v1/actions'],
                                 regions=[brief['revision']['allowed_region']])
        add('only-map-changed', difference['valid'] and difference['changed_rgba_pixels']>0, **difference)
        add('verification-report-matches', recorder.read(RUN/'change.json')==difference)
        for group, source in [('directions', assets['v1/directions']), ('actions', assets['v2/actions'])]:
            for background, color in brief['backgrounds'].items():
                for scale in brief['view_scales']:
                    name=f'{group}-{background}-{scale}x.png'
                    actual=image(RUN/'views'/name)
                    expected=make_preview(source, scale, color)
                    add(name+'-exact-preview', actual.size==expected.size and actual.tobytes()==expected.tobytes())
        records=[json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        session=recorder.read(RUN/'session.json')
        add('consistent-recorded-interpreter', bool(records) and all(
            r['environment']['executable']==session['environment']['executable'] and
            r['environment'].get('prefix')==session['environment'].get('prefix') for r in records))
        v1_hashes={f'v1/{group}.png':recorder.sha(RUN/'v1'/(group+'.png')) for group in ('directions','actions')}
        v2_hash=recorder.sha(RUN/'v2/actions.png')
        first_stage=[i for i, r in enumerate(records) if r['exit_code']==0 and
                     all(r['outputs_after'].get(n)==h for n,h in v1_hashes.items()) and
                     'v2/actions.png' not in r['outputs_after']]
        second_stage=[i for i, r in enumerate(records) if r['exit_code']==0 and
                      r['outputs_after'].get('v2/actions.png')==v2_hash and
                      all(r['outputs_after'].get(n)==h for n,h in v1_hashes.items())]
        add('v1-before-v2-recorded', bool(first_stage) and bool(second_stage) and min(first_stage)<max(second_stage))
        report_commands=[r for r in records if r['kind']=='tool' and r['arguments'][1:2]==['verify'] and r['exit_code']==0
                         and r['outputs_after'].get('change.json')==recorder.sha(RUN/'change.json')]
        add('tool-boundary-check-recorded', bool(report_commands))
    except (ImportError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        add('required-artifacts', False, error=str(exc))
    feedback=RUN/'feedback.md'
    add('feedback-present', feedback.is_file() and bool(feedback.read_text(encoding='utf-8').strip()))
    result=dict(task='LT04',passed=bool(checks) and all(c['passed'] for c in checks),checks=checks,
                checked_utc=recorder.now(),scope='Engineering contracts only; direction, object meaning, marker readability and aesthetics need image review.')
    recorder.save(RUN/'checks.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


def main():
    recorder.check=check
    recorder.environment=environment
    code=recorder.main()
    if sys.argv[1:2]==['start']:
        session=recorder.read(RUN/'session.json')
        session['cohort']='native-icons-dev-20261029'
        recorder.save(RUN/'session.json',session)
    return code


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ImportError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=False),file=sys.stderr)
        raise SystemExit(2)
