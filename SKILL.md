---
name: frontend-production-restore
description: Restore maintainable frontend source from production artifacts. Use when recovering, reconstructing, or migrating a lost-source frontend project — including minified bundles, dist folders, source maps, static assets, screenshots, or packaged apps (Electron, uTools, Chrome extensions). Also use when rebuilding an existing production SPA into a new stack (e.g. Vue 3, React).
---

# Frontend Production Restore

## Goal

Recover a maintainable frontend project from production evidence. Do not merely beautify minified JS; rebuild behavior, architecture, assets, and validation from evidence.

---

## Workflow

### Step 1 · Clarify target

Ask only when genuinely ambiguous:
- Preserve original stack, or migrate to a new one (Vue 3 / React / other)?
- Full app restore, or one specific flow?
- Required parity level (pixel-perfect, functional, or behavioral)?
- Available evidence: screenshots, network logs, runtime package, source maps?

> **Engineering gate (decide before coding):** Choose a mature, user-approved stack and component library. Avoid hand-rolling complex UI, state, forms, tables, charts, drag-drop, or i18n without explicit reason. Commit to the stack before implementing.

---

### Step 2 · Inventory artifacts (low-token first)

Never paste large bundles into context. Produce file lists, string extracts, and targeted snippets.

```bash
python3 ${CODEX_HOME:-$HOME/.codex}/skills/frontend-production-restore/scripts/scan_frontend_artifacts.py \
  <artifact-dir> --out /tmp/frontend-restore-scan.md
```

**If the script is unavailable**, fall back to manual inventory:
```bash
find <artifact-dir> -type f | sort
# Then inspect: package.json, manifest.json, plugin.json, LICENSE, chunk filenames
```

Read the summary output, not the raw bundle.

---

### Step 3 · Take the source-map shortcut (when available)

If `.map` files or inline `sourceMappingURL` exist, extract first:

```bash
python3 ${CODEX_HOME:-$HOME/.codex}/skills/frontend-production-restore/scripts/extract_sourcemap_sources.py \
  <artifact-dir> --out /tmp/recovered-sources
```

**If the script is unavailable**, manually locate `sourceMappingURL` at the end of JS files and decode the base64 or fetch the `.map` file, then parse `sourcesContent` from the JSON.

Use recovered source as behavioral evidence, then clean and rebuild in the target stack.

> See `references/source-map-recovery.md` for detailed map recovery tactics.

---

### Step 4 · Choose branch by artifact type

| Artifact type | Primary tactic |
|---|---|
| Source maps with `sourcesContent` | Extract → clean → rebuild |
| Minified bundle, no maps | String/label extraction → infer shape |
| Screenshots + bundle | Visual layout analysis + label search |
| Packaged app (Electron/uTools/extension) | Unpack → inspect manifest → mock host APIs |

> See `references/artifact-matrix.md` for full branching logic.

---

### Step 5 · Apply evidence in priority order

When multiple evidence sources conflict, apply this order (highest wins):

1. Source maps with `sourcesContent`
2. Runtime behavior and screenshots
3. Served assets, network logs, console output
4. Manifests and config files (`package.json`, `manifest.json`)
5. Bundle strings (UI labels, route names, error messages, aria/title attrs)
6. Inferred source shape from bundle structure

**Conflict resolution:** If source map and screenshot disagree, trust the screenshot for layout/visual details and the source map for logic/data flow.

---

### Step 6 · Extract high-signal strings

Before deminifying, extract UI strings — they are the best search keys.

- **Chinese projects:** Extract Chinese UI strings first (`rg '[\u4e00-\u9fff]'`)
- **English projects:** Extract quoted labels, route names, error messages, aria/title strings

Use these as `rg` keywords to locate components, services, and data shapes in the bundle.

---

### Step 7 · Debug the original bundle (without modifying it)

Serve the original `index.html`, inspect console errors, and add only reversible mocks.

```bash
python3 ${CODEX_HOME:-$HOME/.codex}/skills/frontend-production-restore/scripts/inject_runtime_mock.py \
  <index.html> --out /tmp/debug-index.html
```

**If the script is unavailable**, manually inject a `<script>` block before the bundle that stubs missing globals (`window.utools`, `window.preload`, `ipcRenderer`, extension APIs) with safe no-op implementations.

> See `references/browser-runtime-mock.md` for mock patterns.

---

### Step 8 · Restore by vertical slices

Implement in this order to validate incrementally:

1. App shell (layout, routing, navigation)
2. Data load / save (API calls, local storage, host bridge)
3. Main UI flow (primary user-facing features)
4. Import / export / clipboard / assets
5. Host integration (Electron IPC, uTools APIs, extension messaging)

Avoid rebuilding by webpack chunk number — it produces orphaned logic.

---

### Step 9 · Maintain clean boundaries

| Layer | Purpose |
|---|---|
| `runtime/` or `bridge/` | Thin facade for host APIs (Electron, uTools, extension) |
| `services/` | App-level operations (data fetch, persistence, transform) |
| `core/` | Reusable pure logic (utils, validators, formatters) |

Keep compatibility shims in place during refactors; remove after validation.

---

### Step 10 · Validate continuously

- **Low-cost first:** Unit tests for pure transforms and sanitizers; render output assertions
- **Mid-cost:** Typecheck (`tsc --noEmit`), lint, build
- **High-cost:** Screenshot comparison and manual parity smoke checks

---

## Failure paths and fallbacks

| Situation | Action |
|---|---|
| Source maps are corrupt or missing `sourcesContent` | Fall back to Step 5 evidence order; skip map extraction |
| Bundle is heavily obfuscated (mangled names, dead code injected) | Extract strings and screenshots only; rebuild from behavior spec |
| Screenshots insufficient (no UI evidence) | Ask user for one additional artifact before proceeding |
| Host API (uTools/Electron) calls fail at runtime | Use `inject_runtime_mock.py` or manual stubs; document assumptions |
| Target library unavailable or version conflict | Surface the conflict to user before implementing workaround |

---

## Multilingual project hints

- Chinese labels and route names are high-density search keys — extract them before any deminification attempt.
- English projects: prioritize aria labels, `data-testid`, route paths, and error message strings.
- For mixed-language projects (e.g. Chinese UI + English API keys), extract both layers separately.

---

## Example: successful restore

**Input:** `dist/` folder with `index.html`, `main.abc123.js`, `vendor.xyz.js`, two `.map` files, and three screenshots.

**Steps taken:**
1. Clarified: migrate to Vue 3, functional parity required.
2. Ran `scan_frontend_artifacts.py` → identified React 17 + Ant Design, 4 routes, REST API base URL.
3. Ran `extract_sourcemap_sources.py` → recovered 23 source files with full `sourcesContent`.
4. Extracted Chinese UI strings → confirmed 3 main views: 数据录入, 报表查看, 系统设置.
5. Built Vue 3 + Element Plus scaffold; restored slices in order: shell → data → main flow.
6. Validated with `tsc`, `eslint`, and manual screenshot comparison.

**Output:** Maintainable Vue 3 project with `runtime/`, `services/`, `core/` separation; all 3 views functional; host API calls stubbed with documented contracts.

---

## Resources

| Resource | When to read |
|---|---|
| `references/restore-workflow.md` | Full checklist and deliverable definitions |
| `references/source-map-recovery.md` | Source map decoding and repair |
| `references/artifact-matrix.md` | Branch by build tool, framework, platform |
| `references/engineering-standards.md` | Before implementing any restored code |
| `references/browser-runtime-mock.md` | Mocking Electron / uTools / extension globals |
| `scripts/scan_frontend_artifacts.py` | Low-token artifact inventory |
| `scripts/extract_sourcemap_sources.py` | Recover sources from `.map` files |
| `scripts/inject_runtime_mock.py` | Reversible debug HTML with runtime stubs |

> **If any reference file is missing**, the core workflow above is self-contained and sufficient to proceed. Treat missing references as optional depth, not blockers.
