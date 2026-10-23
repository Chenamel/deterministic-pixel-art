"""Draw only the left 32x32 owner; no right source or finished PNG input."""
from _common import asset_files, emit, entry, parser, rect, spec
from _chunk_contract import PALETTE as P, deck


def make_spec():
    ops = [rect(24, 0, 8, 32, P['water']), rect(22, 0, 2, 32, P['dark']),
           rect(0, 14, 24, 8, P['stone'])]
    for x in range(0, 24, 6):
        ops.append(rect(x, 14, 1, 8, P['mortar']))
    for y in (5, 27):
        ops.append(rect(27, y, 5, 1, P['ripple']))
    deck(ops, 0, 24, 8)
    # Local landmark, away from all joining edges.
    ops.extend([rect(6, 5, 9, 6, P['dark']), rect(7, 6, 7, 4, P['wood']),
                rect(7, 6, 7, 1, P['light'])])
    return spec([32, 32], ops, P['ground'])


def main():
    args = parser(__doc__).parse_args()
    emit(args, asset_files(make_spec()))


if __name__ == '__main__':
    entry(main)
