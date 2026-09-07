---
name: pyrogue-verify
description: Run PyRogue's locked, deterministic verification gate after code or configuration changes.
---

# PyRogue verification

Use the repository-owned gate instead of reconstructing a partial command list.

1. Read `AGENTS.md` and the relevant `SPEC.md` section.
2. Run `make verify` from the repository root.
3. Report each failed or skipped check exactly; do not call a partial pass complete.

The gate runs the high-confidence secret-pattern scan, Ruff, Ruff format, mypy, compileall, pytest, and the fixed-seed CLI suite. Use `CLI_TEST_SEED=<integer> make test-cli` only when reproducing a seed-specific issue.
