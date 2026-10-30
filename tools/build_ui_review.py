"""Build an image-only UI review packet; producer feedback and coordinator facts stay outside."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image
from prepare_agent_trials import archive_bytes

ROOT = Path(__file__).resolve().parents[1]


def png(image):
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def rgba(path):
    with Image.open(path) as image:
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Review images must be single-frame')
        if image.width * image.height > 1024 * 1024:
            raise ValueError('Review input exceeds one million pixels')
        return image.convert('RGBA')


def build(run_dir, out, comparison_dir=None):
    native = run_dir/'consumer/consumer.png'
    zoom = run_dir/'consumer/consumer-3x.png'
    atlas = run_dir/'buttons/asset.png'
    consumer = rgba(native)
    width = consumer.width // 3
    if consumer.size != (3*width, 108) or not 24 <= width <= 112 or width % 2:
        raise ValueError('Expected three labels by six 18px states with uniform even width <=112')
    if rgba(zoom).tobytes() != consumer.resize((consumer.width*3, 324), Image.Resampling.NEAREST).tobytes() or rgba(zoom).size != (consumer.width*3,324):
        raise ValueError('Consumer 3x view is not exact nearest-neighbor scaling')
    if rgba(atlas).size != (3*width, 36):
        raise ValueError('Expected a three-column, two-row source atlas')
    images = {'consumer.png': native.read_bytes(), 'consumer-3x.png': zoom.read_bytes(), 'atlas.png': atlas.read_bytes()}
    for name, background, scale in [('consumer-target.png', '#1D293D', 1),
                                     ('consumer-target-3x.png', '#1D293D', 3),
                                     ('consumer-light-3x.png', '#E9EDF2', 3)]:
        view = Image.alpha_composite(Image.new('RGBA',consumer.size,background), consumer)
        images[name] = png(view.resize((view.width*scale,view.height*scale),Image.Resampling.NEAREST))
    comparison = ''
    if comparison_dir is not None:
        other = rgba(comparison_dir/'consumer.png')
        other_width = other.width // 3
        if other.size != (3*other_width,108) or not 24 <= other_width <= 112 or other_width % 2:
            raise ValueError('Comparison must use the same three-label/six-state layout')
        images[f'width-{other_width}.png'] = (comparison_dir/'consumer.png').read_bytes()
        images[f'width-{other_width}-3x.png'] = png(other.resize((other.width*3,324),Image.Resampling.NEAREST))
        comparison = (f'`width-{other_width}.png` 和其3倍图是同一需求下的{other_width}px宽版本；'
                      f'与{width}px版本比较可读性、留白和尺寸代价，说明各自更适合的场景。')
    task = (ROOT/'benchmarks/long-term/UI01-review.md').read_text(encoding='utf-8')
    task = task.replace('{{WIDTH}}', str(width)).replace('{{COMPARISON}}', comparison)
    files = {'START_HERE.md': (ROOT/'benchmarks/long-term/REVIEW.md').read_bytes(),
             'TASK.md': task.encode('utf-8')}
    files.update({'images/'+name: data for name,data in images.items()})
    payload = archive_bytes({'UI-review/'+name:data for name,data in files.items()})
    out.mkdir(parents=True, exist_ok=False)
    (out/'UI-review.zip').write_bytes(payload)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    manifest = dict(archive='UI-review.zip',bytes=len(payload),sha256=digest(payload),image_count=len(images),
                    files={name:digest(data) for name,data in sorted(files.items())},
                    description='Original producer images plus coordinator background/nearest-neighbor views; no producer feedback or prior findings in ZIP.')
    coordinator = out/'coordinator';coordinator.mkdir()
    (coordinator/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (coordinator/'SHA256SUMS.txt').write_text(digest(payload)+'  UI-review.zip\n',encoding='ascii')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--comparison-dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.run_dir,args.out,args.comparison_dir),ensure_ascii=False,indent=2))
