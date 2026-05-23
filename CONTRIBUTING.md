# How to contribute

Thank you for your interest in our little project. I appreciate any support to help improve this project.

## How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes in the new branch.
4. Submit a [pull request (PR)](https://github.com/rudolfjs/PostgresMimicImporter/pull/new/master) to the main repository.

## Development environment

Pick whichever fits your setup — both run the same `pixi` tasks:

- **Devcontainer** — open the repo in VS Code, JetBrains Gateway, or GitHub Codespaces and choose *Reopen in Container*. The config in `.devcontainer/` builds a pixi-based image with `postgresql-client` and brings up Postgres 14 alongside, so the `dev` pixi env is ready and the importer can run end-to-end without any local Python or DB install.
- **Local pixi (+ direnv)** — install [pixi](https://pixi.sh); the committed `.envrc` auto-activates the `dev` env if you also use [direnv](https://direnv.net) (run `direnv allow` once after cloning). Without direnv, prefix dev commands with `pixi run -e dev`.

### Git hooks (optional but recommended)

After cloning, run once:

```bash
pixi run -e dev install-hooks
```

This installs [lefthook](https://lefthook.dev) git hooks. On `git push` they run the same fast suite CI runs (`lint`, `check-format`, `typecheck`, `test`, `validate-fixtures`) in parallel. Bypass an individual push with `git push --no-verify` — use sparingly.

`lefthook install` bakes the absolute path of the dev-env lefthook binary into `.git/hooks/pre-push`, so pushes work without `pixi shell` active. If you rebuild the pixi env (e.g. wipe `.pixi/` or change platforms), re-run `pixi run -e dev install-hooks` so the embedded path stays valid.

## Pull Request Guidelines

When [submitting a pull request](https://github.com/rudolfjs/PostgresMimicImporter/pull/new/master) please ensure that:

1. You clearly describe the problem you're solving or the feature you're adding, linking to [issue](https://github.com/rudolfjs/PostgresMimicImporter/issues).
2. You outline the changes you've made in detail.
3. You run the same gates CI runs before pushing:
   `pixi run -e dev lint check-format typecheck test validate-fixtures`.
   These cover [ruff](https://docs.astral.sh/ruff/) lint + format-check,
   [ty](https://docs.astral.sh/ty/) type-check, the `pytest` suite, and
   [Pandera](https://pandera.readthedocs.io)-based fixture validation. If you
   ran `pixi run -e dev install-hooks` they fire automatically on `git push`.
4. If your change touches the importer or SQL assets, also run
   `pixi run -e dev e2e` on a host that has real MIMIC-IV data and confirm the
   upstream `validate.sql` reports no row-count mismatches — this is the
   middle checkbox in the PR template.

## Review Process

Once you've submitted a pull request:

1. The project maintainers will review your changes.
2. Maintainers may ask for additional changes or clarifications.
3. Once approved, your contribution will be merged into the project.

## Releasing

Releases are driven by tag pushes matching `v*` — the `.github/workflows/release.yml` workflow handles changelog batching, building artifacts, and publishing the GitHub release.

### One-time setup

The workflow authenticates as a dedicated GitHub App to push the changelog commit and force-move the release tag (the default `GITHUB_TOKEN` cannot push to a branch-protected `main`). Maintainers need:

1. A GitHub App installed on the repo with `contents: write`.
2. Repo variable `RELEASE_APP_ID` set to the App ID.
3. Repo secret `RELEASE_APP_PRIVATE_KEY` set to the App's private key (`.pem` contents).
4. If `main` has branch protection or `refs/tags/v*` has tag protection, the App must be in the bypass list — otherwise the changelog push and the tag force-move will be rejected.

### Cutting a release

[changie](https://changie.dev) is not bundled with pixi (it ships as a single Go binary, not a conda package). Install it once via `brew install changie`, a downloaded release binary, or the [install instructions](https://changie.dev/guide/installation/) — the CI workflow installs its own copy, so this is only needed locally.

1. Add changie fragments for everything new since the last release: `changie new`. Commit them.
2. Bump `version` in `pyproject.toml` to the target version. Commit.
3. Tag and push: `git tag v<VERSION> && git push origin v<VERSION>`.
4. The release workflow will:
   - Verify the tag points to a commit on `main`.
   - Verify the tag matches `pyproject.toml`'s version.
   - Run lint, format check, typecheck, and tests.
   - Batch the unreleased fragments into `.changes/<VERSION>.md` and rebuild `CHANGELOG.md`.
   - Commit the changelog update back to `main` and force-move the tag to include that commit.
   - Build sdist + wheel, generate sha256 checksums, and create a GitHub release with the `.changes/<VERSION>.md` body and the dist files attached.

### Re-running a failed release

If the workflow fails mid-flight (e.g. tests broke), fix the issue on a PR, merge to `main`, and re-tag. If the changelog has already been batched (i.e. `.changes/<VERSION>.md` exists), the workflow will detect "existing" mode and skip the batch step.
