---
name: verify-pyrogue
description: Run PyRogue's locked, deterministic verification gate after code or configuration changes and record each invocation beneath artifacts/verify-pyrogue/<RUN_ID>/.
---

# PyRogue verification

Use the repository-owned gate instead of reconstructing a partial command list.

1. Read `AGENTS.md` and the relevant `SPEC.md` section.
2. Pick a run identifier (`RUN_ID`, ISO-8601 UTC timestamp recommended, e.g. `2026-10-03T120000Z`) and export it for the session.
3. Run `make verify` from the repository root, redirecting combined stdout and stderr to `artifacts/verify-pyrogue/<RUN_ID>/verify.log` so the captured command output is auditable per run.
4. Write any failed-or-skipped check reports next to the log under `artifacts/verify-pyrogue/<RUN_ID>/`; do not call a partial pass complete.

The gate runs the high-confidence secret-pattern scan, Ruff, Ruff format, mypy, compileall, pytest, and the fixed-seed CLI suite. Use `CLI_TEST_SEED=<integer> make test-cli` only when reproducing a seed-specific issue.
