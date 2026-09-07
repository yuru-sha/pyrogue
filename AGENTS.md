# AGENTS.md

Operational rules for agents working on PyRogue. Product requirements and implementation details belong in the referenced documents, not here.

## Sources of truth

At the start of a task, read the relevant documents:

- Requirements, scope, exclusions, and acceptance criteria: [SPEC.md](SPEC.md)
- Documentation index and historical-document policy: [docs/README.md](docs/README.md)
- Current architecture: [docs/architecture.md](docs/architecture.md)
- Development and verification commands: [docs/development.md](docs/development.md)
- Actual behavior: `src/pyrogue/` and `tests/`

`SPEC.md` is the product-requirements authority. When historical material in `docs/` conflicts with the implementation, do not treat it as current behavior. If the requirements must change, update `SPEC.md` and its acceptance criteria first.

## Workflow

1. Run `rtk git status --short --branch` and inspect the diff; preserve existing user changes.
2. Read the relevant `SPEC.md` section, current callers, and related tests.
3. Keep the change within the smallest scope required by the specification. Reuse existing types, helpers, and dependencies.
4. Run `make verify` after the change. If it fails, record the first failure and every check that was not run.
5. Inspect the final diff, worktree, verification results, and remaining risks before reporting completion.

## Safety boundaries

- Limit changes to this repository. Operate external services, GitHub, credentials, browsers, or physical devices only when explicitly requested and within the requested scope.
- Do not commit, push, create branches or pull requests, merge, or release until explicitly requested. These operations are also outside the `SPEC.md` scope.
- Do not run hard-to-recover operations such as `rm -rf`, force-pushes, history rewrites, or database resets. Identify the exact target and wait for explicit approval when such an operation is required.
- Never expose secrets, tokens, credentials, or personal data in output, logs, fixtures, commits, or external transmissions. `.env` may be used without displaying its values.
- Confirm that generated files, lockfiles, migrations, external links, and untracked files are in scope before modifying them.
- Follow the repository RTK convention and run shell commands through `rtk`. Use `apply_patch` for file edits.

Codex sandbox, approval, and network permissions are configured outside the repository and cannot be enforced by this file. Before unattended work, verify a safe profile with workspace-write, approval on-request, and networking disabled. Do not use options such as `--dangerously-bypass-approvals-and-sandbox`.

## Project constraints

- Use Python 3.12 or later and `uv.lock`. Recreate dependencies with `uv sync --locked --extra dev`.
- Follow the v0.3.0 game requirements in `SPEC.md`. Do not add features, dependencies, or abstractions outside the specification.
- The canonical rules path is `GameState` and `GameState.execute` in `src/pyrogue/core/rogue_game.py`. Do not add separate rules to the CLI or GUI.
- Use the seeded RNG owned by the game state and preserve determinism.
- When changing save formats or `GAME_VERSION`, update compatibility checks and tests together.

## Definition of done

Do not report completion until all of the following are true:

- The diff satisfies the applicable requirements and exclusions in `SPEC.md`.
- Focused tests and `make verify` pass.
- Affected boundaries such as seeds, save/load, win/loss, and shared CLI/GUI rules were checked.
- Documentation was updated for changed code, commands, or configuration.
- `git diff --check` passes, no secrets are present, and no unintended untracked or changed files remain.
- Any untested GUI, hardware, OS, or external-CI validation is explicitly reported as untested.

## Verification entry point

```bash
uv sync --locked --extra dev
make verify
```

`make verify` runs the high-confidence secret-pattern scan, Ruff, Ruff format, mypy, compileall, pytest, and the CLI smoke suite. It is not a complete secret scanner; use an organizational or CI scanner as well when available.

## Git and feedback

Do not reorganize, delete, or stash staged, unstaged, or untracked user changes. When a review finding or failure needs a permanent fix, use [docs/feedback.md](docs/feedback.md) to decide whether the guard belongs in a test, `make verify`, a hook, documentation, or a Skill without bloating this file.
