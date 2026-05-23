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
