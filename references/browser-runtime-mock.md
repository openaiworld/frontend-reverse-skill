# Browser Runtime Mock Notes

Use mocks only to render/debug the original production bundle without editing the bundle. Mocks are diagnostic scaffolding, not restored product logic.

## Minimal pattern

Inject before the production bundle in `index.html`:

```html
<script>
  window.__restoreMockLog = [];
  const record = (name, args) => {
    window.__restoreMockLog.push({ name, args: Array.from(args) });
    console.debug('[restore-mock]', name, ...args);
  };

  window.utools = window.utools || {
    db: {
      get: (...args) => (record('utools.db.get', args), null),
      put: (...args) => (record('utools.db.put', args), { ok: true }),
      remove: (...args) => (record('utools.db.remove', args), { ok: true })
    },
    showNotification: (...args) => record('utools.showNotification', args),
    onPluginEnter: (cb) => (record('utools.onPluginEnter', arguments), window.__onPluginEnter = cb)
  };

  window.preload = window.preload || new Proxy({}, {
    get(target, prop) {
      if (!(prop in target)) {
        target[prop] = (...args) => (record(`preload.${String(prop)}`, args), undefined);
      }
      return target[prop];
    }
  });
</script>
```

## Loop

1. Inject the smallest missing API.
2. Reload.
3. Let console errors tell the next missing method or return shape.
4. Replace `undefined` with realistic mock data only when the app logic requires it.
5. Keep a runtime map of API name, arguments, expected return, and evidence.
