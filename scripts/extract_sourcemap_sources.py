#!/usr/bin/env python3
"""Extract original files from source maps that contain sourcesContent."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import posixpath
import re
from pathlib import Path
from typing import Any, Iterable

MAP_COMMENT_RE = re.compile(r'sourceMappingURL=([^\s*]+)')
DATA_URL_RE = re.compile(r'^data:application/json(?:;charset=[^;,]+)?;base64,(.+)$', re.I)
IGNORE_DIRS = {'node_modules', '.git', '.next', '.nuxt', 'dist', 'build', 'coverage'}


def iter_inputs(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield source map files and JS/CSS files that may reference maps."""
    for path in paths:
        if path.is_file():
            yield path
        elif path.is_dir():
            stack = [path]
            while stack:
                current = stack.pop()
                for child in sorted(current.iterdir(), key=lambda item: item.name):
                    if child.is_dir() and child.name not in IGNORE_DIRS:
                        stack.append(child)
                    elif child.is_file() and child.suffix.lower() in {'.map', '.js', '.css'}:
                        yield child


def load_map_from_file(path: Path) -> tuple[str, dict[str, Any]] | None:
    """Load a source map from a .map file or a JS/CSS sourceMappingURL comment."""
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return None

    if path.suffix.lower() == '.map':
        try:
            return str(path), json.loads(text)
        except json.JSONDecodeError:
            return None

    matches = MAP_COMMENT_RE.findall(text[-4096:])
    if not matches:
        return None
    ref = matches[-1].strip().strip('"\'')
    data_match = DATA_URL_RE.match(ref)
    if data_match:
        try:
            raw = base64.b64decode(data_match.group(1)).decode('utf-8', errors='ignore')
            return f'{path}#inline', json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return None
    map_path = (path.parent / ref).resolve()
    if map_path.exists():
        return load_map_from_file(map_path)
    return None


def strip_loader_prefix(source: str) -> str:
    """Remove webpack loader prefixes from a source path."""
    return source.split('!')[-1]


def normalize_source_path(source: str) -> Path:
    """Normalize a source map source entry into a safe relative output path."""
    source = strip_loader_prefix(source).replace('\\', '/')
    source = source.split('?', 1)[0].split('#', 1)[0]
    source = re.sub(r'^[A-Za-z][A-Za-z0-9+.-]*://', '', source)
    source = re.sub(r'^[A-Za-z]:', '', source)
    source = source.lstrip('/')
    while source.startswith('./'):
        source = source[2:]
    normalized = posixpath.normpath(source or 'unknown-source')
    parts = [part for part in normalized.split('/') if part not in {'', '.', '..'}]
    if not parts:
        parts = ['unknown-source']
    if parts[-1].startswith('<') and parts[-1].endswith('>'):
        parts[-1] = parts[-1].strip('<>') or 'virtual-source'
    return Path(*parts)


def unique_path(path: Path) -> Path:
    """Return a non-existing path by adding a numeric suffix when needed."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    index = 2
    while True:
        candidate = path.with_name(f'{stem}.{index}{suffix}')
        if not candidate.exists():
            return candidate
        index += 1


def map_output_group(map_id: str) -> str:
    """Create a stable directory name for one map."""
    base = Path(map_id.split('#', 1)[0]).name or 'inline-map'
    suffix = ''
    if '#' in map_id:
        suffix = '-' + re.sub(r'[^A-Za-z0-9_.-]+', '_', map_id.split('#', 1)[1])
    safe = re.sub(r'[^A-Za-z0-9_.-]+', '_', base + suffix)[:80] or 'source-map'
    digest = hashlib.sha1(map_id.encode('utf-8')).hexdigest()[:8]
    return f'{safe}-{digest}'


def extract_map(map_id: str, data: dict[str, Any], out_dir: Path, manifest: list[dict[str, Any]]) -> None:
    """Extract one source map, including indexed map sections."""
    if isinstance(data.get('sections'), list):
        for index, section in enumerate(data['sections']):
            section_map = section.get('map')
            if isinstance(section_map, dict):
                extract_map(f'{map_id}#section-{index}', section_map, out_dir, manifest)
        return

    sources = data.get('sources') or []
    contents = data.get('sourcesContent') or []
    group = out_dir / map_output_group(map_id)
    group.mkdir(parents=True, exist_ok=True)

    for index, source in enumerate(sources):
        content = contents[index] if index < len(contents) else None
        record = {'map': map_id, 'source': source, 'hasContent': content is not None}
        if content is None:
            manifest.append(record)
            continue
        target = unique_path(group / normalize_source_path(str(source)))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content), encoding='utf-8')
        record['written'] = str(target)
        manifest.append(record)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path, help='Map files, JS/CSS files, or directories')
    parser.add_argument('--out', type=Path, required=True, help='Output directory for recovered sources')
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    seen: set[str] = set()
    map_count = 0

    for path in iter_inputs(args.paths):
        loaded = load_map_from_file(path)
        if not loaded:
            continue
        map_id, data = loaded
        if map_id in seen:
            continue
        seen.add(map_id)
        map_count += 1
        extract_map(map_id, data, args.out, manifest)

    manifest_path = args.out / '_sourcemap_sources.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    written = sum(1 for item in manifest if item.get('written'))
    missing = sum(1 for item in manifest if not item.get('hasContent'))
    print(f'maps={map_count} sources={len(manifest)} written={written} missingContent={missing}')
    print(manifest_path)


if __name__ == '__main__':
    main()
