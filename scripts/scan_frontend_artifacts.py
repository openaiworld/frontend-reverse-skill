#!/usr/bin/env python3
"""Scan production frontend artifacts and emit a compact restoration summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

TEXT_EXTS = {
    '.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx', '.css', '.html', '.htm',
    '.json', '.map', '.txt', '.md', '.svg', '.xml', '.webmanifest'
}
MANAGEMENT_NAMES = {
    'package.json', 'pnpm-lock.yaml', 'package-lock.json', 'yarn.lock',
    'manifest.json', 'plugin.json', 'license', 'license.txt', 'notice',
    'index.html', 'vite.config.js', 'vite.config.ts', 'webpack.config.js'
}
DEPENDENCY_HINTS = [
    'react', 'react-dom', 'vue', 'pinia', 'vuex', 'zustand', 'redux',
    'vite', 'webpack', 'rollup', 'electron', 'utools', 'chrome-extension',
    'antd', 'element-plus', '@mui', 'tailwind', 'bootstrap',
    'axios', 'fetch', 'graphql', 'apollo', 'monaco', 'ace', 'codemirror',
    'markdown-it', 'marked', 'katex', 'mermaid', 'echarts', 'd3', 'prism',
    'slate', 'prosemirror', 'tinymce', 'quill', 'dompurify'
]
DEFAULT_IGNORE_DIRS = {
    '.git', '.hg', '.svn', 'node_modules', '.pnpm-store', '.yarn', '.turbo',
    '.next', '.nuxt', '.svelte-kit', '.vite', 'coverage', '.cache'
}
API_HINT_RE = re.compile(
    r'\b(?:utools|preload|ipcRenderer|ipcMain|electron|chrome\.runtime|chrome\.storage|'
    r'localStorage|sessionStorage|indexedDB|fetch|axios|XMLHttpRequest|postMessage)\b'
)
CHINESE_RE = re.compile(r'[\u3400-\u9fff][\u3400-\u9fffA-Za-z0-9_，。！？、：；（）()【】\[\]《》“”"\'\-—…·\s]{0,80}')
QUOTED_RE = re.compile(r'''["'`]([^"'`\\]{3,100})["'`]''')
IMPORT_RE = re.compile(r'''(?:from\s+|import\s*\(|require\()\s*["']([^"']+)["']''')
DECL_RE = re.compile(r'\b(?:class|function|const|let|var)\s+([A-Za-z_$][\w$]{2,})')
METHOD_RE = re.compile(r'\.([A-Za-z_$][\w$]{3,})\s*\(')
CSS_CLASS_RE = re.compile(r'\.(-?[_a-zA-Z]+[_a-zA-Z0-9-]{2,})')
ROUTE_RE = re.compile(r'''["'`](/[#A-Za-z0-9_./:-]{2,80})["'`]''')
IDENTIFIER_NOISE = {
    'for', 'with', 'will', 'which', 'this', 'that', 'name', 'type',
    'from', 'return', 'function', 'undefined', 'null', 'true', 'false'
}
STRING_NOISE = {'use strict', 'token', 'defaultToken', 'include', 'regex'}


def iter_files(paths: Iterable[Path], ignore_dirs: set[str]) -> Iterable[Path]:
    """Yield files under input paths in deterministic order."""
    for path in paths:
        if path.is_file():
            yield path
        elif path.is_dir():
            stack = [path]
            while stack:
                current = stack.pop()
                children = sorted(current.iterdir(), key=lambda item: item.name)
                for child in children:
                    if child.is_dir():
                        if child.name not in ignore_dirs:
                            stack.append(child)
                    elif child.is_file():
                        yield child


def short_hash(path: Path) -> str:
    """Return a short SHA-256 hash for a file."""
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()[:12]


def read_text(path: Path, max_bytes: int) -> str | None:
    """Read likely text file content within the configured byte limit."""
    if path.suffix.lower() not in TEXT_EXTS and path.name.lower() not in MANAGEMENT_NAMES:
        return None
    if path.stat().st_size > max_bytes:
        return None
    data = path.read_bytes()
    if b'\x00' in data[:4096]:
        return None
    return data.decode('utf-8', errors='ignore')


def clean_text(value: str) -> str:
    """Normalize whitespace in extracted strings."""
    return re.sub(r'\s+', ' ', value).strip()


def is_english_ui_like(value: str) -> bool:
    """Return whether a quoted string is likely to be human-facing English."""
    lower = value.lower()
    if lower in STRING_NOISE:
        return False
    if any(char in value for char in '{}[]'):
        return False
    punctuation = sum(1 for char in value if not char.isalnum() and not char.isspace() and char not in "-_/.'!?()")
    if punctuation / max(len(value), 1) > 0.18:
        return False
    return bool(re.search(r'[A-Za-z]', value))


def top(counter: Counter[str], limit: int) -> list[tuple[str, int]]:
    """Return common values with noisy one-character entries removed."""
    return [(key, count) for key, count in counter.most_common(limit) if len(key.strip()) > 1]


def scan(paths: list[Path], max_file_mb: float, limit: int, ignore_dirs: set[str]) -> dict:
    """Scan artifacts and return a compact evidence summary."""
    max_bytes = int(max_file_mb * 1024 * 1024)
    files = []
    management = []
    by_ext: Counter[str] = Counter()
    chinese: Counter[str] = Counter()
    english: Counter[str] = Counter()
    imports: Counter[str] = Counter()
    identifiers: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    css_classes: Counter[str] = Counter()
    routes: Counter[str] = Counter()
    api_hints: dict[str, Counter[str]] = defaultdict(Counter)
    dependency_hints: Counter[str] = Counter()
    skipped_large = []

    for path in iter_files(paths, ignore_dirs):
        stat = path.stat()
        ext = path.suffix.lower() or '<none>'
        by_ext[ext] += 1
        file_info = {
            'path': str(path),
            'size': stat.st_size,
            'sha256': short_hash(path),
        }
        files.append(file_info)
        if path.name.lower() in MANAGEMENT_NAMES or path.suffix.lower() == '.map':
            management.append(file_info)
        if stat.st_size > max_bytes and path.suffix.lower() in TEXT_EXTS:
            skipped_large.append({'path': str(path), 'size': stat.st_size})

        text = read_text(path, max_bytes)
        if not text:
            continue

        lower = text.lower()
        for dep in DEPENDENCY_HINTS:
            if dep in lower:
                dependency_hints[dep] += 1
        for item in IMPORT_RE.findall(text):
            imports[item.split('/')[0] if item.startswith('@') is False else '/'.join(item.split('/')[:2])] += 1
        for item in CHINESE_RE.findall(text):
            cleaned = clean_text(item)
            if 2 <= len(cleaned) <= 80:
                chinese[cleaned] += 1
        for item in QUOTED_RE.findall(text):
            cleaned = clean_text(item)
            if is_english_ui_like(cleaned):
                english[cleaned] += 1
        for item in DECL_RE.findall(text):
            if item not in IDENTIFIER_NOISE:
                identifiers[item] += 1
        for item in METHOD_RE.findall(text):
            methods[item] += 1
        if path.suffix.lower() in {'.css', '.html', '.htm', '.svg'}:
            for item in CSS_CLASS_RE.findall(text):
                css_classes[item] += 1
        for item in ROUTE_RE.findall(text):
            routes[item] += 1
        for match in API_HINT_RE.finditer(text):
            api_hints[match.group(0)][str(path)] += 1

    largest = sorted(files, key=lambda item: item['size'], reverse=True)[:limit]
    return {
        'totals': {'files': len(files), 'bytes': sum(item['size'] for item in files)},
        'extensions': by_ext.most_common(),
        'largest_files': largest,
        'management_files': management[:limit * 2],
        'skipped_large_text_files': skipped_large[:limit],
        'dependency_hints': top(dependency_hints, limit),
        'imports': top(imports, limit),
        'chinese_strings': top(chinese, limit),
        'english_strings': top(english, limit),
        'routes': top(routes, limit),
        'identifiers': top(identifiers, limit),
        'methods': top(methods, limit),
        'css_classes': top(css_classes, limit),
        'api_hints': {key: counter.most_common(8) for key, counter in sorted(api_hints.items())},
    }


def markdown(summary: dict) -> str:
    """Render a scan summary as Markdown."""
    lines = ['# Frontend Artifact Scan', '']
    totals = summary['totals']
    lines.append(f"- Files: {totals['files']}")
    lines.append(f"- Bytes: {totals['bytes']}")

    def section(title: str, rows: list | dict, formatter) -> None:
        lines.extend(['', f'## {title}', ''])
        if not rows:
            lines.append('- (none)')
            return
        iterable = rows.items() if isinstance(rows, dict) else rows
        for row in iterable:
            lines.append(f'- {formatter(row)}')

    section('Extensions', summary['extensions'], lambda row: f'`{row[0]}`: {row[1]}')
    section('Largest files', summary['largest_files'], lambda row: f"`{row['path']}` ({row['size']} bytes, sha256 {row['sha256']})")
    section('Management/source-map candidates', summary['management_files'], lambda row: f"`{row['path']}` ({row['size']} bytes)")
    section('Skipped large text files', summary['skipped_large_text_files'], lambda row: f"`{row['path']}` ({row['size']} bytes)")
    section('Dependency hints', summary['dependency_hints'], lambda row: f'`{row[0]}` ({row[1]} files)')
    section('Imports/requires', summary['imports'], lambda row: f'`{row[0]}` ({row[1]})')
    section('Chinese strings', summary['chinese_strings'], lambda row: f'{row[0]} ({row[1]})')
    section('English UI-like strings', summary['english_strings'], lambda row: f'{row[0]} ({row[1]})')
    section('Routes/paths', summary['routes'], lambda row: f'`{row[0]}` ({row[1]})')
    section('Candidate declarations', summary['identifiers'], lambda row: f'`{row[0]}` ({row[1]})')
    section('Candidate method calls', summary['methods'], lambda row: f'`{row[0]}` ({row[1]})')
    section('CSS classes', summary['css_classes'], lambda row: f'`{row[0]}` ({row[1]})')
    section('Runtime/API hints', summary['api_hints'], lambda row: f"`{row[0]}` -> " + ', '.join(f"`{p}`:{c}" for p, c in row[1]))
    lines.append('')
    return '\n'.join(lines)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path, help='Artifact files or directories to scan')
    parser.add_argument('--out', type=Path, help='Write Markdown summary to this path')
    parser.add_argument('--json', type=Path, help='Optional JSON output path')
    parser.add_argument('--max-file-mb', type=float, default=8, help='Max text file size to parse')
    parser.add_argument('--top', type=int, default=40, help='Max rows per section')
    parser.add_argument(
        '--ignore-dir',
        action='append',
        default=[],
        help='Directory name to skip; can be repeated. Common build/cache directories are skipped by default.',
    )
    args = parser.parse_args()

    summary = scan(args.paths, args.max_file_mb, args.top, DEFAULT_IGNORE_DIRS | set(args.ignore_dir))
    output = markdown(summary)
    if args.out:
        args.out.write_text(output, encoding='utf-8')
    else:
        print(output)
    if args.json:
        args.json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
