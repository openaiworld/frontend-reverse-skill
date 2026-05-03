# Production Frontend Restore Workflow

## Clarify

Ask only for decisions that change the implementation path:

- Goal: exact parity, partial recovery, redesign, or migration to Vue 3/React/etc.
- Scope: whole app, main page, one feature, or component library.
- Evidence: dist folder, original package, source maps, screenshots, recordings, logs, network traces.
- Runtime: plain browser, Electron, uTools, Chrome extension, mobile webview, embedded iframe.
- Allowed engineering stack: framework, component library, state/data/form/router/test libraries, and whether migration is desired.

## Evidence checklist

1. Freeze originals: copy bundles/assets to an immutable artifact folder; record hashes.
2. Find management files first: `package.json`, lockfiles, `manifest.json`, `plugin.json`, `LICENSE`, `index.html`, sourcemaps, webpack/vite comments.
3. If source maps exist, inspect them before deeper bundle analysis. `sourcesContent` can turn a hard reverse-engineering task into a cleanup/rebuild task.
4. Inventory assets: JS chunks, CSS, images, fonts, workers, wasm, iframe pages, editor/vendor folders.
5. Extract strings: Chinese UI labels, English labels, errors, routes, storage keys, API paths, feature names.
6. Identify dependencies by evidence: LICENSE text, package banners, global names, chunk names, module signatures.
7. Run original in a browser or host-like debug shell; record console errors and missing globals.

## Branch by artifact quality

- **Source maps with `sourcesContent`**: extract source first, classify real app code vs vendor/generated wrappers, then rebuild cleanly.
- **Source maps without `sourcesContent`**: use source paths and mappings as a module index; combine with targeted bundle snippets.
- **No maps but runnable app**: use devtools, storage/network/IPC inspection, screenshots, and runtime mocks.
- **No maps and not runnable**: rely on manifest/config, bundle strings, assets, images, and UI reconstruction.
- **User requests migration**: treat recovered source as behavior evidence; do not preserve old framework shape if rebuilding as Vue 3/React/etc.

## Keyword strategy

- Start from visible UI text and screenshots.
- Add domain nouns and verbs from filenames, routes, API paths, localStorage keys, IndexedDB names, and error messages.
- Guess likely method names from behavior: `getList`, `saveNote`, `exportPdf`, `uploadImage`, `openFile`, `sync`, `search`, etc.
- For Chinese apps, search simplified/traditional variants when needed; Chinese labels often survive minification.
- For English apps, search title/aria/placeholder strings, route segments, enum-like constants, and error messages.

## Browser runtime debug loop

1. Serve original artifacts locally, for example `python3 -m http.server 8080` in the dist folder.
2. Open `index.html`, inspect console/network/storage.
3. Add a reversible mock only for the first missing global or API.
4. Reload and repeat until DOM renders enough to compare UI and behavior.
5. Record each mock as an observed runtime dependency, not as final business logic.

## Restore architecture

Use a standard target-stack project and simple architecture unless the user asks otherwise. Prefer official scaffolds and user-approved libraries over custom infrastructure. For complex UI or behavior, choose mature solutions before writing large custom hooks/composables/utilities:

- component libraries for layout, dialogs, menus, forms, tables, icons, notifications, accessibility states
- framework routers and state/data libraries for routing, app state, server cache, persistence
- established libraries for forms, validation, drag/drop, virtual lists, editors, markdown, charts, i18n, date/time, uploads

Use a simple target architecture unless the user asks otherwise:

```text
src/
  runtime/      # host APIs and browser/Electron/uTools/extension bridge
  services/     # app operations and data contracts
  core/         # pure reusable logic, parsers, renderers, transforms
  components/   # target framework UI
  styles/       # recovered tokens and global styles
  assets/       # copied verified static resources
```

For migrations, map production behavior to the new target stack:

- React source can be restored as Vue 3 if the user wants Vue 3.
- Vue source can be restored as React if the user wants React.
- Preserve observable behavior, data model, asset paths, and runtime APIs; do not preserve minified module shape.
- Keep platform globals behind `runtime/*`, use-case logic in `services/*`, pure transforms in `core/*`, and UI as thin composition of framework/component-library primitives.

## Implementation guardrails

- Do not invent API shapes, data models, constants, colors, spacing, or workflows without evidence.
- Do not hardcode values unless they are verified product constants from manifests, runtime, storage, or source maps.
- Do not write large bespoke systems when a user-approved standard library solves the problem.
- Keep code simple: avoid speculative abstractions and over-engineering.
- If evidence disproves an assumption, state the correction and update the implementation.

## Validation

Prefer cheap, repeatable checks:

- Pure transforms and renderers: unit tests.
- Runtime bridge: mocked success/failure contract tests.
- UI parity: screenshots or focused manual smoke checklist.
- Build health: install, typecheck, lint, test, build.
- Known differences: document explicitly with evidence and risk.

## Deliverables

Useful docs are allowed when they accelerate recovery:

- `docs/walkthrough.md`: evidence, stack, module map, differences.
- `docs/parity-checklist.md`: user flows and pass/fail status.
- `docs/runtime-map.md`: globals, storage, APIs, IPC, mocks.
- Keep docs concise and tied to evidence; avoid generic reports.
