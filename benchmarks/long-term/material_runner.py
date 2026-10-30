"""LT06 artifact contracts over the unchanged shared command recorder."""
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
        from pixelart import render, make_preview
        from pixelart.compat import pixels, require_pillow
        from pixelart.metadata import layout_record
        require_pillow()
        brief = recorder.read(BASE/'inputs/brief.json')
        actual = image(RUN/'materials.png')
        expected = render(recorder.read(RUN/'materials.json'))
        add('editable-rerenders', actual.size == expected.size and actual.tobytes() == expected.tobytes())
        add('fresh-layout', recorder.read(RUN/'layout.json') == json.loads(json.dumps(layout_record(expected))))
        width, height = brief['cell_size']
        names = brief['names']
        columns = brief['columns']
        wanted = dict(cell_size=[width, height], columns=columns, rows=1,
                      cells=[dict(name=name, x=i*width, y=0, w=width, h=height) for i, name in enumerate(names)])
        add('named-native-cells', actual.size == (columns*width, height) and expected.info.get('pixelart') == wanted)
        alphas, visible = [], []
        for i, name in enumerate(names):
            cell = actual.crop((i*width, 0, (i+1)*width, height))
            alpha = cell.getchannel('A').tobytes()
            alphas.append(alpha)
            add(name+'-nonempty', any(alpha))
            add(name+'-has-transparency', 0 in alpha)
            visible.append(b''.join(bytes(p if p[3] else (0, 0, 0, 0)) for p in pixels(cell)))
        add('shared-pixel-alpha', len(set(alphas)) == 1)
        add('distinct-visible-materials', len(set(visible)) == len(names))
        preview_files = []
        for theme, background in brief['backgrounds'].items():
            for scale in brief['view_scales']:
                name = f'views/{theme}-{scale}x.png'
                preview = image(RUN/name)
                expected_preview = make_preview(actual, scale, background)
                add(name+'-exact-preview', preview.size == expected_preview.size and preview.tobytes() == expected_preview.tobytes())
                preview_files.append(name)
        records = [json.loads(line) for line in (RUN/'commands.jsonl').read_text(encoding='utf-8').splitlines()]
        session = recorder.read(RUN/'session.json')
        add('consistent-recorded-interpreter', bool(records) and all(
            row['environment']['executable'] == session['environment']['executable'] and
            row['environment'].get('prefix') == session['environment'].get('prefix') for row in records))
        final = {name: recorder.sha(RUN/name) for name in ('materials.json', 'materials.png', 'layout.json')}
        add('final-render-recorded', any(row['kind'] == 'tool' and row['arguments'][1:2] == ['render'] and
            row['exit_code'] == 0 and all(row['outputs_after'].get(name) == digest for name, digest in final.items())
            for row in records))
        add('final-previews-recorded', all(any(row['kind'] == 'tool' and row['arguments'][1:2] == ['preview'] and
            row['exit_code'] == 0 and row['outputs_before'].get(name) != recorder.sha(RUN/name) and
            row['outputs_after'].get(name) == recorder.sha(RUN/name) for row in records) for name in preview_files))
    except (ImportError, OSError, ValueError, KeyError, TypeError, IndexError, RecursionError) as exc:
        add('required-artifacts', False, error=str(exc))
    feedback = RUN/'feedback.md'
    add('feedback-present', feedback.is_file() and bool(feedback.read_text(encoding='utf-8').strip()))
    result = dict(task='LT06', passed=bool(checks) and all(item['passed'] for item in checks), checks=checks,
                  checked_utc=recorder.now(),
                  scope='Artifact contracts and recorded tool calls only. Object identity, structural alignment, material cues, source reuse and visual quality need separate review.')
    recorder.save(RUN/'checks.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


def main():
    recorder.check = check
    recorder.environment = environment
    code = recorder.main()
    if sys.argv[1:2] == ['start']:
        session = recorder.read(RUN/'session.json')
        session['cohort'] = 'materials-workflow-dev-20261030'
        recorder.save(RUN/'session.json', session)
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ImportError) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
