"""Portable checks for this skill's metadata and local references.

This project-local checker is not the official skill-creator validator. Pass that
validator to test_skill.py --validator when it is available.
"""
import re
import sys
from pathlib import Path

import yaml


def validate(folder):
    text = (folder / 'SKILL.md').read_text(encoding='utf-8')
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not match:
        raise ValueError('SKILL.md must start with YAML frontmatter')
    metadata = yaml.safe_load(match[1])
    if not isinstance(metadata, dict):
        raise ValueError('Frontmatter must be a mapping')
    name, description = metadata.get('name'), metadata.get('description')
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
        raise ValueError('Invalid skill name')
    if name != folder.name:
        raise ValueError('Skill folder must match its name')
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise ValueError('Description must be nonempty and at most 1024 characters')
    for target in re.findall(r'\]\(([^)]+)\)', text[match.end():]):
        if '://' not in target and not (folder / target).is_file():
            raise ValueError(f'Broken skill reference: {target}')
    print('Portable skill metadata and references valid')


if __name__ == '__main__':
    validate(Path(sys.argv[1]))
