# Contributing

Thank you for contributing.

## Before starting

- Search existing Issues and Pull Requests to avoid duplicate work.
- For non-trivial work, use an Issue to define the problem and acceptance criteria.
- Read `AGENTS.md`, the README, and relevant files under `docs/`.
- Keep changes focused on one Issue or clearly related outcome.
- Avoid unrelated cleanup and unnecessary dependencies.

## Development

Use the repository's canonical commands. Keep changes focused and avoid introducing new dependencies, abstractions, or automation without a demonstrated need.

Add or update tests when behavior changes. Update documentation when interfaces, workflows, configuration, or user-visible behavior changes.

## Pull requests

Open changes from a feature branch rather than working directly on `main`.

Pull Requests should:

- explain what changed and why;
- link the related Issue when one exists;
- record the checks actually run;
- identify breaking changes or migration steps;
- call out remaining risks or follow-up work.

Do not claim checks passed when they were not run.

## Commit messages

Use [Conventional Commits 1.0.0](https://www.conventionalcommits.org/ja/v1.0.0/) for commit messages.

The commit message format is:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Use these types as the default vocabulary:

- `feat`: add a new feature
- `fix`: fix a bug
- `refactor`: change code without changing behavior
- `docs`: change documentation
- `test`: add or change tests
- `chore`: make maintenance changes
- `ci`: change continuous integration configuration
- `build`: change the build system or dependencies
- `perf`: improve performance
- `revert`: revert a previous change

Use a scope when it adds useful context, for example `fix(forecast): handle missing observations`.

Mark a breaking change with `!` after the type or scope, or with a `BREAKING CHANGE:` footer.
