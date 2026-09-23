# GitHub Release Procedure

Release bodies start with a fixed-format hand-written summary and verification details, followed by GitHub's automatically generated notes. Categories and excluded labels for the generated notes are managed in `.github/release.yml`.

Release titles and bodies must be written in English. Use a title such as `vX.Y.Z — Short English Summary`.

## Before releasing

1. Confirm that the changes for the release are merged into `main`.
2. Review the diff from the previous release and confirm the version number.
3. If the tag does not exist, create and push an annotated tag from the intended commit.

```bash
tag=vX.Y.Z
git tag -a "$tag" -m "$tag"
git push origin "$tag"
```

When using an existing tag, do not recreate it. Confirm only that it points to the intended commit.

## Prepare the release body

Copy the template to a temporary file and edit it according to the comments.

```bash
release_notes_file="$(mktemp)"
cp .github/release-notes-template.md "$release_notes_file"
${EDITOR:-vi} "$release_notes_file"
```

Run the later commands that use `release_notes_file` in the same shell.

Checklist:

- `Overview` explains the key user-facing points of the release.
- `Compatibility & Migration` states whether compatibility changes or migration work are required.
- `Verification` lists only checks that were actually performed.
- `Known Issues` says `None` when there are no known issues.
- No template comments or unfilled placeholders remain in the published body.

## Create the Release

Use `--verify-tag` to confirm the existing tag and `--notes` to prepend the hand-written body to the automatically generated notes.

```bash
tag=vX.Y.Z
release_notes="$(<"$release_notes_file")"
gh release create "$tag" \
  --verify-tag \
  --title "$tag" \
  --generate-notes \
  --notes "$release_notes"
```

After creation, verify the publication status and URL.

```bash
gh release view "$tag" \
  --json name,tagName,isDraft,isPrerelease,publishedAt,url
```

Remove the temporary file after verification.

```bash
rm "$release_notes_file"
```
