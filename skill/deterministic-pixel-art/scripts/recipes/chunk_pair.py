"""Minimal two-owner scene: draw locally, then assemble without retouching."""
from _common import asset_files, emit, entry, make_preview, parser
from _chunk_contract import CONTRACT
import chunk_left
import chunk_right
from pixelart import assemble
from pixelart.assembly import seam_sheet
from pixelart.metadata import layout_record


def make_files(flag='E4BB6B'):
    files = {}
    sources = {}
    parts = []
    for name, data in [('left', chunk_left.make_spec()), ('right', chunk_right.make_spec(flag))]:
        local = asset_files(data)
        files.update({f'{name}/{key}': value for key, value in local.items()})
        path = f'{name}/asset.png'
        sources[path] = local['asset.png']
        parts.append(dict(name=name, image=path, at=CONTRACT['owners'][name][:2], mode='copy'))
    project = dict(version=1, size=CONTRACT['size'], require_coverage=True, parts=parts)
    image, report = assemble(project, sources)
    files.update({'asset.png': image, 'layout.json': layout_record(image),
                  'preview.png': make_preview(image, 4), 'project.json': project,
                  'assembly.json': report, 'seams.png': seam_sheet(image, report),
                  'contract.json': CONTRACT})
    return files


def main():
    cli = parser(__doc__)
    cli.add_argument('--flag', default='E4BB6B')
    args = cli.parse_args()
    emit(args, make_files(args.flag))


if __name__ == '__main__':
    entry(main)
