# Artifact Matrix

Use this matrix to choose the restoration path instead of applying one fixed workflow.

## By evidence quality

| Evidence | Best path |
|---|---|
| Source maps with `sourcesContent` | Extract sources first, then rebuild/clean and validate against runtime. |
| Source maps without `sourcesContent` | Use paths, symbols, and generated positions as a module map; reconstruct selectively. |
| Source maps absent, readable chunks | Extract strings/imports/runtime APIs; recover by vertical user flows. |
| Only screenshots/assets | Rebuild UI from visual analysis and visible text; treat behavior as unknown until runtime/API evidence appears. |
| Original app can run | Instrument browser/devtools, storage, network, IPC; use runtime as strongest evidence. |

## By build tool

| Build output clue | What to inspect |
|---|---|
| Vite/Rollup | `assets/*.js`, ESM imports, `manifest.json`, `import.meta`, clean sourcemaps. |
| Webpack | runtime bootstrap, numeric module IDs, `webpack://` sourcemaps, splitChunks, LICENSE. |
| Parcel | hashed assets, inline runtimes, bundle graph comments, HTML transforms. |
| Vue CLI/Nuxt | `app.*.js`, `chunk-vendors`, `.vue` sourcemap paths, SSR/static folders. |
| Next.js | `.next/static`, route manifests, server/client split, RSC/SSR boundaries. |
| Angular CLI | `main.*.js`, `polyfills`, lazy chunks, component template/style artifacts. |

## By framework

| Framework clue | Restore focus |
|---|---|
| React | components, hooks, state stores, JSX/SWC/Babel transforms, router boundaries. |
| Vue 2/3 | SFC template/script/style, composables, Pinia/Vuex, router, directives. |
| Svelte | compiled component boundaries, stores, transitions, generated CSS. |
| Angular | modules/components/services, DI, templates, RxJS flows. |
| Plain JS/jQuery | DOM selectors, event delegation, global state, plugin initialization order. |

## By platform

| Platform | Extra evidence |
|---|---|
| Browser SPA | routes, storage, service worker, API calls, env vars, CSP. |
| Electron | preload, IPC, file dialogs, shell, app paths, native modules. |
| uTools | `plugin.json`, `preload`, `utools.db`, plugin enter/out events, feature codes. |
| Chrome extension | `manifest.json`, background/service worker, content scripts, permissions, storage. |
| Mobile WebView | injected bridge, user agent, deep links, safe-area, offline cache. |
| Embedded widget/iframe | host `postMessage`, sizing protocol, allowed origins, iframe assets. |

## Practical rule

Always pick the strongest available evidence path first:

`source map recovery` -> `runtime/devtools instrumentation` -> `manifest/config/dependency evidence` -> `string/API search` -> `visual reconstruction`.
