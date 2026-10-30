"""Package native icon atlases and exact previews for independent image review."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image
from prepare_agent_trials import archive_bytes

ROOT = Path(__file__).resolve().parents[1]
BACKGROUNDS = {'dark': '182637', 'light': 'E9EDF2'}


def rgba(data):
    with Image.open(BytesIO(data)) as image:
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Expected a single-frame icon atlas')
        if image.size not in ((48, 12), (64, 16), (384, 96), (512, 128)):
            raise ValueError('Unexpected native atlas or preview size')
        return image.convert('RGBA')


def build(run_dir, out):
    run_dir, out = Path(run_dir), Path(out)
    if out.exists():
        raise FileExistsError(out)
    images = {}
    for group, stage, unit in [('directions', 'v1', 12), ('actions', 'v2', 16)]:
        native = (run_dir / stage / (group + '.png')).read_bytes()
        atlas = rgba(native)
        if atlas.size != (4 * unit, unit):
            raise ValueError('Unexpected native size: ' + group)
        images[group + '.png'] = native
        for background, color in BACKGROUNDS.items():
            composed = Image.alpha_composite(Image.new('RGBA', atlas.size, '#' + color), atlas)
            for scale in (1, 8):
                name = f'{group}-{background}-{scale}x.png'
                data = (run_dir / 'views' / name).read_bytes()
                view = rgba(data)
                expected = composed.resize((atlas.width * scale, atlas.height * scale), Image.Resampling.NEAREST)
                if view.size != expected.size or view.tobytes() != expected.tobytes():
                    raise ValueError('Preview must exactly match background and nearest-neighbor scale: ' + name)
                images[name] = data
    files = {
        'START_HERE.md': (ROOT / 'benchmarks/long-term/REVIEW.md').read_bytes(),
        'TASK.md': (ROOT / 'benchmarks/long-term/LT04-review.md').read_bytes(),
        **{'images/' + name: data for name, data in images.items()},
    }
    payload = archive_bytes({'LT04-review/' + name: data for name, data in files.items()})
    digest = lambda data: hashlib.sha256(data).hexdigest()
    manifest = dict(archive='LT04-review.zip', bytes=len(payload), sha256=digest(payload),
                    image_count=len(images), files={name: digest(data) for name, data in sorted(files.items())})
    out.mkdir(parents=True, exist_ok=False)
    (out / 'LT04-review.zip').write_bytes(payload)
    coordinator = out / 'coordinator'
    coordinator.mkdir()
    (coordinator / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (coordinator / 'SHA256SUMS.txt').write_text(digest(payload) + '  LT04-review.zip\n', encoding='ascii')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.run_dir, args.out), ensure_ascii=False, indent=2))
