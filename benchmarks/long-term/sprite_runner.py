"""LT05 artifact checks over the unchanged shared command recorder."""
import json
import os
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
        with Image.open(path) as opened:
            return opened.convert('RGBA')

    try:
        sys.path.insert(0, str(BASE/'deterministic-pixel-art/scripts'))
        from pixelart import render, make_preview, verify_edit
        from pixelart.compat import pixels, require_pillow
        require_pillow()
        brief = recorder.read(BASE/'inputs/brief.json')
        assets = {}
        for stage in ('v1', 'v2'):
            actual = image(RUN/stage/'sprite.png')
            expected = render(recorder.read(RUN/stage/'sprite.json'))
            add(stage+'-editable-rerenders', actual.size == expected.size and actual.tobytes() == expected.tobytes())
            add(stage+'-native-size', list(actual.size) == brief['size'])
            alpha = list(pixels(actual.getchannel('A')))
            add(stage+'-nonempty', any(alpha))
            add(stage+'-has-transparency', 0 in alpha)
            assets[stage] = actual
        region = brief['revision']['allowed_region']
        x, y, width, height = region
        source = tuple(bytes.fromhex(brief['revision']['base_before']))
        destination = tuple(bytes.fromhex(brief['revision']['base_after']))
        expected = assets['v1'].copy()
        count = 0
        for yy in range(y, y+height):
            for xx in range(x, x+width):
                if expected.getpixel((xx, yy)) == source:
                    expected.putpixel((xx, yy), destination)
                    count += 1
        add('v1-indicator-base-present', count > 0, pixels=count)
        add('v1-body-outside-indicator', any(p[3] for yy in range(expected.height) for xx in range(expected.width)
            if not (x <= xx < x+width and y <= yy < y+height) for p in [assets['v1'].getpixel((xx, yy))]))
        add('exact-indicator-color-edit', assets['v2'].size == expected.size and assets['v2'].tobytes() == expected.tobytes())
        difference = verify_edit(assets['v2'], assets['v1'], regions=[region])
        add('only-indicator-changed', difference['valid'] and difference['changed_rgba_pixels'] > 0, **difference)
        add('verification-report-matches', recorder.read(RUN/'change.json') == difference)
        for theme, color in brief['backgrounds'].items():
            for scale in brief['view_scales']:
                name = f'{theme}-{scale}x.png'
                actual = image(RUN/'views'/name)
                expected = make_preview(assets['v2'], scale, color)
                add(name+'-exact-preview', actual.size == expected.size and actual.tobytes() == expected.tobytes())
        records = [json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        session = recorder.read(RUN/'session.json')
        add('consistent-recorded-interpreter', bool(records) and all(
            row['environment']['executable'] == session['environment']['executable'] and
            row['environment'].get('prefix') == session['environment'].get('prefix') for row in records))
        v1 = {f'v1/sprite.{ext}': recorder.sha(RUN/'v1'/f'sprite.{ext}') for ext in ('json', 'png')}
        ready = [i for i, row in enumerate(records) if row['exit_code'] == 0 and
                 all(row['outputs_after'].get(name) == value for name, value in v1.items()) and
                 'v2/sprite.json' not in row['outputs_after'] and 'v2/sprite.png' not in row['outputs_after']]
        v2 = recorder.sha(RUN/'v2/sprite.png')
        second = [i for i, row in enumerate(records) if row['exit_code'] == 0 and row['outputs_after'].get('v2/sprite.png') == v2]
        add('v1-before-v2-recorded', bool(ready) and bool(second) and min(ready) < max(second))
        preserved = False
        if ready:
            first = min(ready)
            accepted = {name: value for name, value in records[first]['outputs_after'].items() if name.startswith('v1/')}
            preserved = all(all(snapshot.get(name) == value for name, value in accepted.items())
                            for row in records[first+1:] for snapshot in (row['outputs_before'], row['outputs_after']))
            preserved = preserved and all(recorder.snapshot().get(name) == value for name, value in accepted.items())
        add('v1-ready-files-preserved', preserved)
        add('tool-boundary-check-recorded', any(row['kind'] == 'tool' and row['arguments'][1:2] == ['verify'] and
            row['exit_code'] == 0 and row['outputs_after'].get('change.json') == recorder.sha(RUN/'change.json') for row in records))
    except (ImportError, OSError, ValueError, KeyError, TypeError, IndexError, RecursionError) as exc:
        add('required-artifacts', False, error=str(exc))
    feedback = RUN/'feedback.md'
    add('feedback-present', feedback.is_file() and bool(feedback.read_text(encoding='utf-8').strip()))
    result = dict(task='LT05', passed=bool(checks) and all(item['passed'] for item in checks), checks=checks,
                  checked_utc=recorder.now(), scope='Artifact and observed-stage checks only; object meaning, orientation, original authorship and visual quality need separate review.')
    recorder.save(RUN/'checks.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


def main():
    recorder.check = check
    recorder.environment = environment
    code = recorder.main()
    if sys.argv[1:2] == ['start']:
        session = recorder.read(RUN/'session.json')
        session['cohort'] = 'sprite-workflow-dev-20261029'
        recorder.save(RUN/'session.json', session)
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ImportError) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
