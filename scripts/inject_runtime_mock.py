#!/usr/bin/env python3
"""Create a debug HTML copy with a minimal frontend runtime mock injected."""

from __future__ import annotations

import argparse
from pathlib import Path

MOCK = r'''<script data-frontend-restore-runtime-mock>
(() => {
  const root = window;
  const log = (name, args) => {
    root.__restoreMockLog = root.__restoreMockLog || [];
    root.__restoreMockLog.push({ name, args: Array.from(args || []) });
    console.debug('[restore-mock]', name, ...(args || []));
  };

  const ok = { ok: true };
  root.utools = root.utools || {
    db: {
      get: (...args) => (log('utools.db.get', args), null),
      put: (...args) => (log('utools.db.put', args), ok),
      remove: (...args) => (log('utools.db.remove', args), ok),
      allDocs: (...args) => (log('utools.db.allDocs', args), [])
    },
    onPluginEnter: (callback) => (log('utools.onPluginEnter', []), root.__restoreOnPluginEnter = callback),
    onPluginOut: (callback) => (log('utools.onPluginOut', []), root.__restoreOnPluginOut = callback),
    showNotification: (...args) => log('utools.showNotification', args),
    shellOpenExternal: (...args) => log('utools.shellOpenExternal', args),
    copyText: (...args) => log('utools.copyText', args)
  };

  root.preload = root.preload || new Proxy({}, {
    get(target, prop) {
      if (!(prop in target)) {
        target[prop] = (...args) => (log(`preload.${String(prop)}`, args), undefined);
      }
      return target[prop];
    }
  });

  root.chrome = root.chrome || {
    runtime: { sendMessage: (...args) => (log('chrome.runtime.sendMessage', args), Promise.resolve(undefined)) },
    storage: { local: { get: (...args) => (log('chrome.storage.local.get', args), Promise.resolve({})), set: (...args) => (log('chrome.storage.local.set', args), Promise.resolve()) } }
  };
})();
</script>'''


def inject(html: str, mock: str) -> str:
    """Inject mock script before the first production script when possible."""
    if 'data-frontend-restore-runtime-mock' in html:
        return html
    lower = html.lower()
    head_index = lower.find('<head')
    if head_index >= 0:
        close = lower.find('>', head_index)
        if close >= 0:
            return html[: close + 1] + '\n' + mock + '\n' + html[close + 1 :]
    script_index = lower.find('<script')
    if script_index >= 0:
        return html[:script_index] + mock + '\n' + html[script_index:]
    return mock + '\n' + html


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('html', type=Path, help='Original index.html or HTML file')
    parser.add_argument('--out', type=Path, help='Output debug HTML path; default adds .restore-debug before suffix')
    args = parser.parse_args()

    source = args.html.read_text(encoding='utf-8', errors='ignore')
    output_path = args.out or args.html.with_name(f'{args.html.stem}.restore-debug{args.html.suffix}')
    output_path.write_text(inject(source, MOCK), encoding='utf-8')
    print(output_path)


if __name__ == '__main__':
    main()
