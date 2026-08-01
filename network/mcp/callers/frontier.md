# Comfy Valheim MCP Caller

Connect to:

```text
http://127.0.0.1:8721/mcp
```

Required header:

```text
X-Comfy-Key: comfy-dev-local
```

The Valheim mod should use `valheim-mod-local` when we add an in-mod client.
Keep this gateway localhost-only and development-only. The legacy `:8720`
listener is not an accepted Baseline source until its endpoint identity is
verified.

