"""Inventory document references and README structure without changing the Skill.

Existence is not proof of a reference's intended meaning. Example outputs and
unresolved context are kept in the inventory rather than counted as valid links.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


TEXT_SUFFIXES = {'.md', '.json', '.txt', '.yaml', '.yml', '.html', '.css', '.js'}
PATH_TOKEN = re.compile(
    r'(?<![\w:/\\])(?:<[^>\n]+>[/\\])?'
    r'(?:[\w.$*{}@+\-]+[/\\])*[\w.$*{}@+\-]+\.'
    r'(?:md|py|jsonl?|png|jpe?g|svg|gif|webp|zip|ya?ml|txt|toml|html|js|css|ttf|csv|sha256)'
    r'(?::\d+)?', re.IGNORECASE)
ROOT_NAMES = {'docs', 'src', 'skill-content', 'skill', 'recipes', 'tools',
              'benchmarks', 'quality', 'baselines', 'examples', 'specs', 'tests', '.github'}


def references(text):
    """Yield explicit Markdown/HTML links and recognizable path occurrences."""
    occupied = []
    patterns = [
        ('markdown', r'!?\[[^\]\n]*\]\(([^)\n]+)\)'),
        ('definition', r'^\s*\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)'),
        ('html', r'(?:href|src)\s*=\s*[\"\']([^\"\']+)[\"\']'),
    ]
    for kind, pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            start, end = match.span(1)
            if any(a <= start < b for a, b in occupied):
                continue
            occupied.append((start, end))
            target = match[1].strip()
            if target.startswith('<') and '>' in target:
                target = target[1:target.index('>')]
            else:
                target = re.split(r'\s+[\"\']', target, maxsplit=1)[0]
            yield start, target, kind
    # Do not reinterpret substrings of absolute paths or URLs as relative files.
    for match in re.finditer(r'https?://[^\s<>\"`]+|[A-Za-z]:[\\/][^\n\"`]+', text):
        occupied.append(match.span())
    for match in PATH_TOKEN.finditer(text):
        if not any(a <= match.start() < b for a, b in occupied):
            yield match.start(), match[0], 'file-reference'
    for match in re.finditer(r'(?<!`)`([^`\n]+)`(?!`)', text):
        target = match[1]
        if target.endswith('/') and re.fullmatch(r'(?:[.\w\-]+/)+', target):
            yield match.start(1), target, 'directory-reference'


def resolve_reference(root, source, target, kind):
    raw = target
    target = unquote(target).replace('\\', '/')
    if re.match(r'^[A-Za-z]:/', target) or target.startswith(('/', '~/', '//')):
        return dict(status='absolute-not-in-relative-scope', target=raw)
    if target.startswith('<skill>/'):
        target = 'skill/deterministic-pixel-art/' + target[len('<skill>/'):]
    if urlsplit(target).scheme:
        return dict(status='external-not-in-relative-scope', target=raw)
    filename = target.partition('#')[0].partition('?')[0]
    filename = re.sub(r':\d+$', '', filename)
    if not filename:
        return dict(status='same-document-fragment', target=raw, exists=source.is_file())
    if any(c in filename for c in '*{}$<>') or 'YYYYMMDD' in filename or '...' in filename:
        return dict(status='unverified-template', target=raw)
    candidates = [source.parent / filename]
    is_skill = source.is_relative_to(root / 'skill-content')
    if kind == 'file-reference' or kind == 'directory-reference':
        candidates.append(root / filename)
    if is_skill:
        relative_folder = source.parent.relative_to(root / 'skill-content')
        candidates.append(root / 'skill/deterministic-pixel-art' / relative_folder / filename)
        candidates.append(root / 'skill/deterministic-pixel-art' / filename)
        if '/' not in filename:
            candidates.append(root / 'skill/deterministic-pixel-art/scripts/recipes' / filename)
    # These two immutable reports name legacy paths relative to the original
    # project; baselines/manifest.json explicitly declares that retained layout.
    if source.name in ('metrics.json', 'first-pass-metrics.json') and source.parent == root / 'docs/measurements':
        candidates.extend([root / 'baselines/rendered' / filename,
                           root / 'baselines/snapshot' / filename])
        if filename.startswith('pixelart/') or filename == 'pixel_art.py':
            candidates.append(root / 'src' / filename)
    if source.name in ('lt06-results-20261030.zh-CN.md', 'lt06-results-20261030.json') and filename == 'src/gen_chest.py':
        candidates.append(root / 'evaluation/lt06-results-20261030/submission/RUN' / filename)
    for candidate in candidates:
        # Normalize '..' before existence checks, including when an intermediate
        # directory is absent. OS/pathlib versions differ on unnormalized stat.
        candidate = candidate.resolve()
        if candidate.exists():
            resolved = candidate
            relative = resolved.relative_to(root.resolve()).as_posix() if resolved.is_relative_to(root.resolve()) else str(resolved)
            return dict(status='exists', target=raw, exists=True, resolved=relative,
                        basis='distributed-skill' if relative.startswith('skill/') else 'document-or-repository')
    first = filename.split('/')[0]
    if kind in ('markdown', 'definition', 'html') or first in ROOT_NAMES:
        status = 'broken'
    elif first in ('evaluation', 'output', 'dist', 'RUN') or first.startswith('v1') or first.startswith('v2'):
        status = 'absent-generated-or-local-evidence'
    else:
        status = 'unverified-context'
    return dict(status=status, target=raw, exists=False,
                attempted=[str(p.relative_to(root)) if p.is_relative_to(root) else str(p) for p in candidates])


def readme_structure(path):
    sections = []
    current = None
    fence = None
    table_rows = []

    def finish_table():
        if table_rows and current is not None:
            data = [r for r in table_rows if not re.fullmatch(r'[|\s:\-]+', r)]
            current['tables'].append(max(0, len(data) - 1))
        table_rows.clear()

    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.lstrip().startswith(('```', '~~~')):
            finish_table()
            if fence is None:
                fence = line.lstrip()[:3]
                if current is not None:
                    current['code'].append([])
            elif line.lstrip().startswith(fence):
                fence = None
            continue
        if fence:
            if current is not None:
                current['code'][-1].append(line.rstrip())
            continue
        heading = re.match(r'^(#{1,6})\s+(.+?)\s*#*$', line)
        if heading:
            finish_table()
            current = dict(level=len(heading[1]), title=heading[2], line=number, code=[], tables=[])
            sections.append(current)
        elif line.strip().startswith('|'):
            table_rows.append(line.strip())
        else:
            finish_table()
    finish_table()
    return sections


def compare_readmes(english, chinese):
    left, right = readme_structure(english), readme_structure(chinese)
    rows = []
    for index in range(max(len(left), len(right))):
        a = left[index] if index < len(left) else None
        b = right[index] if index < len(right) else None
        rows.append(dict(index=index, english=a, chinese=b,
                         missing_section=a is None or b is None,
                         heading_level_matches=bool(a and b and a['level'] == b['level']),
                         code_matches=bool(a and b and a['code'] == b['code']),
                         table_rows_match=bool(a and b and a['tables'] == b['tables'])))
    return dict(english_sections=len(left), chinese_sections=len(right), sections=rows,
                structural_matches=all(not r['missing_section'] and r['heading_level_matches'] and r['code_matches'] and r['table_rows_match'] for r in rows),
                limitation='Section pairing is positional. Translation meaning requires human/agent review, not this structural check.')


def skill_reference_graph(folder):
    entry = folder / 'SKILL.md'
    available = {p.relative_to(folder).as_posix() for p in (folder / 'references').glob('*.md')}
    direct = set()
    all_edges = {}
    for path in [entry, *sorted((folder / 'references').glob('*.md'))]:
        edges = set()
        for _, target, kind in references(path.read_text(encoding='utf-8')):
            if kind not in ('markdown', 'definition', 'html'):
                continue
            name = target.partition('#')[0]
            if not name or urlsplit(name).scheme:
                continue
            candidate = (path.parent / name).resolve()
            if candidate.is_relative_to(folder.resolve()):
                relative = candidate.relative_to(folder.resolve()).as_posix()
                if relative.startswith('references/') and relative.endswith('.md'):
                    edges.add(relative)
        key = path.relative_to(folder).as_posix()
        all_edges[key] = sorted(edges)
        if path == entry:
            direct = edges
    reachable, pending = set(), list(direct)
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        pending.extend(all_edges.get(name, []))
    return dict(entry=str(entry), available=sorted(available), directly_referenced=sorted(direct),
                missing=sorted(reachable - available), not_directly_referenced=sorted(available - direct),
                unreachable=sorted(available - reachable), edges=all_edges,
                limitation='Reference reachability, not proof that every file is needed or instructionally effective.')


def audit(root, excluded=()):
    root = Path(root).resolve()
    files = sorted({p for name in ('docs', 'skill-content') for p in (root / name).rglob('*') if p.is_file()}
                   | {root / 'README.md', root / 'README.zh-CN.md'})
    rows, inventory = [], []
    for path in files:
        name = path.relative_to(root).as_posix()
        if name in excluded:
            inventory.append(dict(file=name, disposition='audit-output-checked-separately'))
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            inventory.append(dict(file=name, disposition='binary-no-text-reference-parser'))
            continue
        try:
            text = path.read_text(encoding='utf-8-sig')
        except UnicodeError:
            inventory.append(dict(file=name, disposition='unverified-encoding'))
            continue
        inventory.append(dict(file=name, disposition='scanned'))
        seen = set()
        for start, target, kind in references(text):
            key = (start, target)
            if key in seen:
                continue
            seen.add(key)
            row = dict(source=name, line=text.count('\n', 0, start) + 1, kind=kind)
            row.update(resolve_reference(root, path, target, kind))
            rows.append(row)
    return dict(scope=['docs/', 'skill-content/', 'README.md', 'README.zh-CN.md'],
                files=inventory, file_count=len(inventory), references=rows,
                counts=dict(Counter(r['status'] for r in rows)),
                readmes=compare_readmes(root / 'README.md', root / 'README.zh-CN.md'),
                skill_references={name: skill_reference_graph(root / name) for name in ('skill-content', 'skill/deterministic-pixel-art')},
                limitations=['Recognizes Markdown inline/definition links, HTML href/src, filename tokens and backticked directories.',
                             'Natural-language implicit references without recognizable paths are unverified.',
                             'Remote URLs and absolute paths are inventoried but outside relative-file existence scope.',
                             'Existence is local; ignored files may be unavailable in a public checkout.',
                             'Markdown section anchors are not checked by this inventory.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--exclude', action='append', default=[])
    args = parser.parse_args()
    result = audit(args.root, args.exclude)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(files=result['file_count'], counts=result['counts'], readme_structure_matches=result['readmes']['structural_matches'])))
