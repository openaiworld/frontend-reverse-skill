# Source Map Recovery

Use this path before heuristic deminification. If production artifacts include usable source maps, recover source files directly, then use bundles only to verify runtime behavior.

## Decision tree

1. Find maps:
   - `*.js.map`, `*.css.map`
   - `//# sourceMappingURL=...` or `/*# sourceMappingURL=... */`
   - inline `data:application/json;base64,...`
   - devtools/network-hidden maps that exist beside chunks
2. Inspect map quality:
   - `sourcesContent` present: recover files directly.
   - `sources` present but no `sourcesContent`: recover paths/module names, then use bundle snippets and sourcemap lookup to guide reconstruction.
   - indexed map with `sections`: extract each section recursively.
3. Recover to a separate folder. Do not overwrite a hand-restored project.
4. Classify recovered files:
   - real app source: `src/`, `pages/`, `components/`, `stores/`, `services/`
   - generated/framework wrappers: webpack bootstrap, Vite client, runtime helpers
   - vendor: `node_modules`, npm packages, minified workers
5. Rebuild a maintainable project from recovered source plus artifact evidence; do not blindly trust old path layout if the user wants migration or cleanup.

## Command

```bash
python3 ${CODEX_HOME:-$HOME/.codex}/skills/frontend-production-restore/scripts/extract_sourcemap_sources.py <artifact-dir-or-map> --out /tmp/recovered-sources
```

Outputs:

- recovered files grouped by map file
- `_sourcemap_sources.json` manifest with source paths, write status, and missing `sourcesContent`

## Notes by build tool

- **Webpack**: paths often start with `webpack://`, `webpack:///./src`, or include loader prefixes. Strip loaders and keep useful app paths.
- **Vite/Rollup**: paths are usually cleaner and may include original `src/*`; chunks map well to ESM modules.
- **Vue CLI/Nuxt**: `.vue` SFC source may be present in `sourcesContent`; otherwise scripts/styles/templates can be split in generated form.
- **Angular CLI**: maps may expose `webpack://` paths and TypeScript sources; component templates/styles may appear as separate virtual modules.
- **CSS preprocessors**: `.scss`, `.less`, `.styl` may recover from CSS maps even when JS maps are absent.
