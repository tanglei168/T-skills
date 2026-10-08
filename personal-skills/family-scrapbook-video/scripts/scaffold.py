#!/usr/bin/env python3
"""Copy the approved, media-free family style into a project."""
import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--replace', action='store_true',
                        help='Replace existing style assets with this baseline.')
    args = parser.parse_args()
    skill = Path(__file__).resolve().parents[1]
    project = args.project.expanduser().resolve()
    source = skill / 'assets'
    target = project / 'assets' / 'family-scrapbook'
    files = [(f, target / f.relative_to(source))
             for f in sorted(source.rglob('*')) if f.is_file()]
    conflicts = [dst for src, dst in files if dst.exists() and
                 (not dst.is_file() or dst.read_bytes() != src.read_bytes())]
    if conflicts and not args.replace:
        parser.error('Existing customized assets preserved. Choose another project '
                     'or use --replace to restore the baseline: ' +
                     ', '.join(str(x) for x in conflicts))
    if any(dst.exists() and not dst.is_file() for _, dst in files):
        parser.error('A destination is not a file; no assets were copied.')
    copied = 0
    for src, dst in files:
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    print(f'Family style ready: {target} ({copied} files copied)')
    print('Stylesheet: assets/family-scrapbook/layout.css')
    print('Specification: assets/family-scrapbook/style-spec.json')
    print('Original media and project timeline were not modified.')


if __name__ == '__main__':
    main()
