# Engineering Standards for Restored Frontend Projects

Use these standards as a quality gate before writing or accepting restored code. The goal is a normal, maintainable frontend project, not a one-off imitation of a bundle.

## First-principles rule

For every non-trivial implementation choice, answer briefly:

1. What observed behavior or artifact requires this?
2. What is the smallest standard frontend solution that satisfies it?
3. Which part is fact, and which part is an assumption to verify?

Correct false assumptions immediately when evidence contradicts them.

## Technology selection

- Follow the user-approved target stack first: Vue 3, React, TypeScript, Vite, component library, state library, router, test runner, etc.
- Prefer standard project scaffolds and idioms over custom build systems.
- If the user allows a component library, use it for dialogs, menus, forms, tables, layout primitives, icons, notifications, date pickers, and accessibility states.
- Prefer mature libraries for complex problems: router, state, data fetching/cache, forms, validation, drag-and-drop, virtual lists, charts, markdown/editor, i18n, auth, date/time, file upload, and testing.
- Do not add a dependency just to avoid a small, clear utility. KISS still wins for simple pure functions.

## Do not reinvent by default

Avoid writing large custom implementations for problems with widely adopted solutions:

- custom router instead of framework router
- custom form engine instead of a form/validation library when forms are complex
- custom table virtualization, drag/drop, markdown parser, rich editor, charting, date handling, upload manager, or i18n runtime
- custom hooks/composables that duplicate library APIs or framework primitives

If custom code is needed, keep it narrow, documented, and backed by evidence from the original behavior.

## Architecture boundaries

Use high cohesion and low coupling:

```text
src/
  runtime/      # platform bridge: Electron/uTools/extension/WebView/browser globals
  services/     # app use cases, data contracts, storage/API calls
  core/         # pure reusable domain/render/transform logic
  components/   # UI composed from target framework/library primitives
  composables/  # Vue-only reusable state/effects when needed
  hooks/        # React-only reusable state/effects when needed
  styles/       # design tokens, global styles, recovered assets
```

Rules:

- Keep platform globals out of components; call them through `runtime/*`.
- Keep business/use-case logic out of visual components; call `services/*`.
- Keep pure parsing/rendering/transforms in `core/*` with tests.
- Keep compatibility shims during migrations; remove only after callers are proven migrated.

## Hardcoding policy

Reject hardcoding unless it reflects verified product constants:

- Good: feature codes from `plugin.json`, route names from a recovered router, storage keys found in runtime.
- Bad: invented IDs, fake API shapes, guessed colors/sizes, arbitrary timeout values, mock data baked into production code.

When values are inferred, mark them as assumptions in docs or inline notes and verify with runtime or artifacts before treating them as final.

## Simplicity and maintainability

- Choose the simplest design that preserves verified behavior and leaves a clear extension seam.
- Avoid defensive abstractions for hypothetical future features.
- Do not create generic frameworks inside the restored app.
- Split files when a file mixes unrelated responsibilities or becomes hard to review, but do not split purely for aesthetics.
- Prefer readable names recovered from UI/domain evidence over minified or over-general names.

## Quality gate before delivery

A restored implementation is not ready until:

- target stack and major dependencies are user-approved or clearly inherited from artifacts
- no large custom subsystem exists where a standard library was allowed and appropriate
- components are mostly composition of standard primitives plus thin product logic
- runtime/platform dependencies are isolated behind facades
- pure core logic has focused tests
- assumptions and known differences are documented
- typecheck/lint/test/build or equivalent checks have run, unless explicitly out of scope
