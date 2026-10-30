"""Draw only the right 32x32 owner; --flag changes six by four pixels."""
from _common import asset_files, color, emit, entry, parser, rect, spec
from _chunk_contract import PALETTE as P, deck


def make_spec(flag='E4BB6B'):
    color(flag)
    ops = [rect(0, 0, 8, 32, P['water']), rect(8, 0, 2, 32, P['dark']),
           rect(8, 14, 24, 8, P['stone'])]
    for x in range(10, 32, 6):
        ops.append(rect(x, 14, 1, 8, P['mortar']))
    for y in (5, 27):
        ops.append(rect(0, y, 5, 1, P['ripple']))
    deck(ops, 32, 0, 8)
    ops.extend([rect(17, 4, 1, 8, P['dark']), rect(18, 4, 8, 6, P['dark']),
                rect(19, 5, 6, 4, flag)])
    return spec([32, 32], ops, P['ground'])


def main():
    cli = parser(__doc__)
    cli.add_argument('--flag', default='E4BB6B')
    args = cli.parse_args()
    emit(args, asset_files(make_spec(args.flag)))


if __name__ == '__main__':
    entry(main)
