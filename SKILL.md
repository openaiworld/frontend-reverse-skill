---
name: frontend-production-restore
description: Restore maintainable frontend source from production artifacts. Use when Codex is asked to recover, reconstruct, migrate, or analyze a lost-source frontend project from minified bundles, dist folders, index.html, chunks, source maps, static assets, screenshots, Electron/uTools/Chrome-extension packages, or when the user wants to rebuild an existing production React/Vue/SPA into another target stack such as Vue 3 or React.
---

# Frontend Production Restore

## Goal

Recover a maintainable frontend project from production evidence. Do not merely beautify minified JS; rebuild behavior, architecture, assets, and validation from evidence.

## Fast workflow

1. **Clarify target first.** Ask only when needed: preserve original stack, migrate to Vue 3/React, restore full app or one flow, required parity level, available screenshots/assets/runtime package.
2. **Inventory before reading.** Prefer commands and scripts over pasting bundles. Run:
   ```bash
   python3 ${CODEX_HOME:-$HOME/.codex}/skills/frontend-production-restore/scripts/scan_frontend_artifacts.py <artifact-dir> --out /tmp/frontend-restore-scan.md
   ```
   Then read the summary, not the entire bundle.
3. **Take the source-map shortcut when available.** If `.map` files or inline `sourceMappingURL` exist, extract first:
   ```bash
   python3 ${CODEX_HOME:-$HOME/.codex}/skills/frontend-production-restore/scripts/extract_sourcemap_sources.py <artifact-dir> --out /tmp/recovered-sources
   ```
   Use recovered source as evidence, then clean/rebuild into the requested target stack.
4. **Choose the branch by artifact type.** Different build tools, frameworks, and platforms need different tactics; read `references/artifact-matrix.md` when the path is not obvious.
5. **Use evidence order.** Source maps with `sourcesContent` > runtime behavior and screenshots > served assets/network/console > manifests/configs > bundle strings > inferred source shape.
6. **Apply the engineering gate before coding.** Build a standard frontend project in the user-approved stack; prefer mature libraries/component-library primitives for complex UI and behavior; avoid invented APIs, hardcoding, and large custom hooks/composables.
7. **Search by guessed keywords.** Infer likely class/function/field/API names from UI text, Chinese/English labels, errors, package clues, and domain concepts; then use `rg`, script output, source maps, and LICENSE files to confirm.
8. **Debug the original bundle without modifying it.** Serve the original `index.html`, inspect console errors, and add only reversible HTML/runtime mocks. Use `inject_runtime_mock.py` to create a debug copy when browser globals such as `utools`, `preload`, `ipcRenderer`, or extension APIs are missing.
9. **Restore by vertical slices.** App shell → data load/save → main UI flow → import/export/clipboard/assets → host integration. Avoid rebuilding by webpack module number.
10. **Create maintainable boundaries.** Use thin `runtime`/`bridge` facades for host APIs, `services/*` for app operations, and `core/*` for reusable pure logic. Keep compatibility shims during refactors.
11. **Validate continuously.** Prefer low-cost tests for pure transforms, render output, sanitizer/runtime contracts, then typecheck/lint/build and screenshot/manual parity smoke checks.

## Token-efficiency rules

- Never paste large bundles into context. Produce file lists, top strings, dependency clues, and targeted snippets.
- For Chinese projects, extract Chinese UI strings first; they are high-signal search keys. For English projects, extract quoted UI labels, route names, error messages, and aria/title strings.
- If screenshots are available, analyze layout, colors, icons, and visible text; use visible text and icon semantics as search terms.
- Prefer `package.json`, `manifest.json`, `plugin.json`, `LICENSE`, sourcemaps, and chunk names before deep deminification.

## Target-stack and library decision

- If the user wants parity, keep the closest stack unless there is a strong maintainability reason to modernize.
- If the user wants migration, treat production artifacts as behavior/spec, not source shape. Rebuild in the target stack while preserving assets, routes, data contracts, and runtime integration.
- Use user-approved libraries and component systems whenever they fit; do not hand-roll complex UI, hooks, composables, state, forms, tables, editors, charts, drag/drop, or i18n without a reason.
- If uncertain, restore one end-to-end flow first before committing to a full architecture.

## Resources

- Read `references/restore-workflow.md` for the detailed checklist and deliverables.
- Read `references/source-map-recovery.md` when sourcemaps exist or `sourceMappingURL` appears in bundles.
- Read `references/artifact-matrix.md` to branch by source-map quality, build tool, framework, and platform.
- Read `references/engineering-standards.md` before implementing restored project code or reviewing architecture.
- Read `references/browser-runtime-mock.md` when the original bundle needs browser/Electron/uTools/extension mocks.
- Use `scripts/scan_frontend_artifacts.py` for low-token artifact inventory and keyword extraction.
- Use `scripts/extract_sourcemap_sources.py` to recover source files from `.map` files with `sourcesContent`.
- Use `scripts/inject_runtime_mock.py` to create a reversible debug HTML copy with safe runtime mocks.
