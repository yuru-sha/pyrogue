# Contributing

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
