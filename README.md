## release-readiness-core

Project-agnostic deterministic release-readiness engine and adapters.

### Quickstart

```bash
uv sync
uv run release-readiness --input-json '[{"key":"go-test","status":"PASS"}]'
```

### Install from Git (SHA-pinned)

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
```

### Development

```bash
uv run pytest
uv build
```

