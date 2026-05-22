# Release Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tag-triggered GitHub Actions release workflow that batches the changie unreleased fragments, builds Python sdist+wheel artifacts, and publishes a GitHub release — mirroring the structure of `agent-quota/.github/workflows/release.yml` but adapted for this Python/pixi project.

**Architecture:** Two-job workflow triggered on `v*` tag push. Job 1 (`release`) authenticates as a GitHub App, validates the tag is on `main`, validates pyproject.toml version matches the tag, runs the full pixi verification matrix (lint, typecheck, test), batch-merges any unreleased changie fragments back to main, and force-moves the tag to include the changelog commit. Job 2 (`build-publish`) checks out the (possibly moved) tag, builds sdist + wheel via a dedicated `release` pixi feature, computes sha256 checksums, and creates a GitHub release with `.changes/{version}.md` as the body.

**Tech Stack:** GitHub Actions, pixi (`prefix-dev/setup-pixi`), changie (`miniscruff/changie-action`), hatchling (PEP 517 build backend), `python-build`, GitHub App token via `actions/create-github-app-token`, `softprops/action-gh-release`.

---

## Prerequisites (Manual — user handles outside this plan)

1. **Create a GitHub App** scoped to this repo with `contents: write` permission. Install it on the repo. Record the App ID.
2. **Generate a private key** for the App; download the `.pem` file.
3. **Set repo variable** `RELEASE_APP_ID` = the App ID (Settings → Secrets and variables → Actions → Variables).
4. **Set repo secret** `RELEASE_APP_PRIVATE_KEY` = the full contents of the `.pem` file (Settings → Secrets and variables → Actions → Secrets).
5. **Branch protection on `main`**: ensure the App is in the bypass list (otherwise the App's push of the changelog commit in Task 7 will be rejected). For unprotected personal repos this is a non-issue.
6. **Tag protection / rulesets covering `v*`**: if you have a rule on `refs/tags/v*`, the App must be in its bypass list too — Task 7 does a `git push origin "$TAG" --force` to move the tag onto the changelog commit, and a protected-tag rule will block it.

These are documented at the bottom of the workflow file as a comment block (Task 9) and in CONTRIBUTING.md (Task 11).

---

## File Structure

- **Create:** `.github/workflows/release.yml` — the release workflow (built up incrementally over Tasks 4–9).
- **Modify:** `pyproject.toml` — add `[build-system]` (Task 1) and `[tool.pixi.feature.release.*]` (Task 2). Pixi will regenerate `pixi.lock` as a side effect.
- **Modify:** `CONTRIBUTING.md` — add a "Releasing" section (Task 11).
- **No** `scripts/install.sh` equivalent — Python packages are installed via `pip install`, not a curl-pipe-sh installer. The reference workflow's `sh -n scripts/install.sh` lint step has no analogue here.

---

## Decision Notes

- **Version source of truth:** `pyproject.toml` `[project] version` stays canonical (static). The workflow **validates** that the tag (with the leading `v` stripped) matches `pyproject.toml`'s version, failing fast if they diverge. The developer bumps the version manually before tagging — this matches the current manual process visible in `git log` (e.g. commit `07457a5 0.0.4 release`). A future enhancement could use `hatch-vcs` for fully dynamic versioning; it is out of scope here.
- **Artifact choice:** sdist (`pgmimic-<version>.tar.gz`) + wheel (`pgmimic-<version>-py3-none-any.whl`). These are the Python-native parallel to agent-quota's `.tar.gz` archive. No PyInstaller / single-binary build — `psycopg2` requires the system `libpq` and is not friendly to bundling.
- **Build backend:** `hatchling`. Modern, minimal config, ships with the `hatchling` PyPI package; no setuptools boilerplate.
- **Pixi for CI:** All Python work (verification + build) runs through `pixi run -e <env>`, mirroring the developer flow documented in `CONTRIBUTING.md`. A new `release` pixi feature owns the build toolchain (`python-build`, `hatchling`) so the default `dev` environment stays lean.
- **Action pinning:** Use major-version tag pins (`@v3`, `@v6`) to match agent-quota's style. (Full-SHA pinning is stricter for supply-chain security and could be a follow-up.)

---

## Task 1: Add `[build-system]` and declare runtime dependencies in pyproject.toml

**Why this matters:** Two distinct things:
1. Without `[build-system]`, `python -m build` cannot determine a backend and fails. `hatchling` will auto-discover the `pgmimic/` package because the dir name matches `[project].name`.
2. `[tool.pixi.dependencies]` only describes the *dev/conda* environment — it is NOT carried into wheel metadata. Without a `[project] dependencies` entry, a `pip install pgmimic` from the GitHub release artifact would have no `psycopg2` declared and fail at import time. We use `psycopg2-binary` for the wheel so pip consumers get a precompiled binary (no `libpq` + C toolchain required); the pixi `default` env keeps the conda-forge `psycopg2` build it already uses.

**Files:**
- Modify: `/home/schnetlerr/dev/PostgresMimicImporter.feat-gh-release/pyproject.toml` — add `dependencies` inside the existing `[project]` table, and append a new `[build-system]` table after it.

- [ ] **Step 1: Edit `pyproject.toml`** — add `dependencies` to the `[project]` table.

Replace this block (lines 1–8):

```toml
[project]
name = "pgmimic"
description = "MIMIC data importer for PostgreSQL"
authors = [{name = "Rudolf J", email = "r.schnetler@uq.edu.au"}]
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">= 3.10"
version = "0.0.4"
```

with:

```toml
[project]
name = "pgmimic"
description = "MIMIC data importer for PostgreSQL"
authors = [{name = "Rudolf J", email = "r.schnetler@uq.edu.au"}]
readme = "README.md"
license = {file = "LICENSE"}
requires-python = ">= 3.10"
version = "0.0.4"
dependencies = [
    "psycopg2-binary>=2.9,<3",
]
```

- [ ] **Step 2: Edit `pyproject.toml`** — insert the build-system table after the `[project]` table.

Add this block after the closing `]` of `dependencies` and before `[tool.pixi.workspace]`:

```toml

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 3: Verify the file parses**

The project's pinned Python is 3.10, which predates the stdlib `tomllib`. Use `pixi info` (which itself re-parses `pyproject.toml`) as a portable smoke test:

```bash
pixi info --json > /dev/null && echo "pyproject.toml parses"
```
Expected: prints `pyproject.toml parses`. If you have Python 3.11+ on `$PATH`, the stricter check is `python3.11 -c "import tomllib, pathlib; d = tomllib.loads(pathlib.Path('pyproject.toml').read_text()); print(d['project']['dependencies']); print(d['build-system'])"`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "Declare psycopg2-binary runtime dep and add hatchling build-system"
```

---

## Task 2: Add a `release` pixi feature with a build task

**Why this matters:** The CI job needs a reproducible toolchain to produce sdist + wheel. A dedicated `release` feature keeps `dev` lean (no `python-build` dependency creep) and gives developers a way to test the build locally (`pixi run -e release build-dist`).

**Files:**
- Modify: `/home/schnetlerr/dev/PostgresMimicImporter.feat-gh-release/pyproject.toml` — add a `[tool.pixi.feature.release.*]` set of tables, and register `release` in `[tool.pixi.environments]`.

- [ ] **Step 1: Edit `pyproject.toml`** — add the new feature dependencies.

Insert after `[tool.pixi.feature.types.dependencies]` block (around line 25–26):

```toml
[tool.pixi.feature.release.dependencies]
python-build = ">=1.2"
hatchling = ">=1.25"
```

- [ ] **Step 2: Edit `pyproject.toml`** — register the `release` env in `[tool.pixi.environments]`.

Replace this block (around line 28–32):

```toml
[tool.pixi.environments]
default = {solve-group = "default"}
dev = {features = ["lint", "test", "types"], solve-group = "default"}
lint = {features = ["lint"], solve-group = "default"}
test = {features = ["test"], solve-group = "default"}
types = {features = ["types"], solve-group = "default"}
```

with:

```toml
[tool.pixi.environments]
default = {solve-group = "default"}
dev = {features = ["lint", "test", "types"], solve-group = "default"}
lint = {features = ["lint"], solve-group = "default"}
test = {features = ["test"], solve-group = "default"}
types = {features = ["types"], solve-group = "default"}
release = {features = ["release"], solve-group = "default"}
```

- [ ] **Step 3: Edit `pyproject.toml`** — add the `build-dist` task.

Insert after `[tool.pixi.feature.types.tasks]` block (around line 45–46):

```toml
[tool.pixi.feature.release.tasks]
build-dist = {cmd = "python -m build --no-isolation --sdist --wheel --outdir dist", description = "Build sdist + wheel into ./dist (uses pixi-pinned hatchling, no PyPI fetch)"}
```

> **Why `--no-isolation`:** `python -m build` defaults to creating an isolated venv and pulling `hatchling` *from PyPI*, which would bypass the pixi-pinned version above. `--no-isolation` makes `build` use the active environment instead — which IS the `release` env when you run it via `pixi run -e release`.

- [ ] **Step 4: Refresh the lock and resolve the new env**

Run:
```bash
pixi install -e release
```
Expected: lockfile updates, `release` env is created. If you see a solver error, check that the `python-build` package is available on `conda-forge` (it is, as `python-build`).

- [ ] **Step 5: Smoke-test the local build**

Run:
```bash
rm -rf dist/
pixi run -e release build-dist
ls dist/
```
Expected: two files —
```
pgmimic-0.0.4-py3-none-any.whl
pgmimic-0.0.4.tar.gz
```

If hatchling complains about not finding the package, add this stanza to `pyproject.toml` near the `[build-system]` block:

```toml
[tool.hatch.build.targets.wheel]
packages = ["pgmimic"]
```

(This is only needed if auto-discovery fails. Run Step 5 first; only add the stanza if it errors.)

- [ ] **Step 6: Clean up artifacts and commit**

```bash
rm -rf dist/
echo "dist/" >> .gitignore   # only if not already ignored — check first with `grep -q '^dist/' .gitignore && echo present || echo missing`
git add pyproject.toml pixi.lock .gitignore
git commit -m "Add pixi release feature for sdist+wheel builds"
```

---

## Task 3: Create the release workflow skeleton

**Why this matters:** Establishing the file with the trigger and permissions first means every subsequent task is an additive edit, easy to review.

**Files:**
- Create: `/home/schnetlerr/dev/PostgresMimicImporter.feat-gh-release/.github/workflows/release.yml`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Write the skeleton**

Create `.github/workflows/release.yml` with this content:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  release:
    name: Prepare release
    runs-on: ubuntu-latest
    if: "!endsWith(github.actor, '[bot]')"

    steps:
      - name: Placeholder
        run: echo "release job — fleshed out in Tasks 4–7"

  build-publish:
    name: Build and publish
    runs-on: ubuntu-latest
    needs: release
    if: "!endsWith(github.actor, '[bot]')"

    steps:
      - name: Placeholder
        run: echo "build-publish job — fleshed out in Task 8"
```

- [ ] **Step 3: Validate YAML parses**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```
Expected: no output, exit code 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Add release workflow skeleton"
```

---

## Task 4: Implement Job 1 — App token, checkout, tag-on-main verification

**Files:**
- Modify: `.github/workflows/release.yml` — replace the `release` job's `steps:` block.

- [ ] **Step 1: Replace the `release` job's `steps:` block**

In `.github/workflows/release.yml`, replace the `release.steps:` content (currently the single Placeholder step) with:

```yaml
    steps:
      - name: Generate app token
        id: app-token
        uses: actions/create-github-app-token@v3
        with:
          app-id: ${{ vars.RELEASE_APP_ID }}
          private-key: ${{ secrets.RELEASE_APP_PRIVATE_KEY }}
          permission-contents: write

      - name: Check out code
        uses: actions/checkout@v6
        with:
          fetch-depth: 0
          token: ${{ steps.app-token.outputs.token }}

      - name: Verify tag points to a commit on main
        env:
          SHA: ${{ github.sha }}
        run: |
          git fetch origin main
          if ! git merge-base --is-ancestor "$SHA" origin/main; then
            echo "::error::Release tags must point to commits already on main."
            exit 1
          fi
```

- [ ] **Step 2: Validate YAML parses**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Wire up app token, checkout, and tag-on-main check in release job"
```

---

## Task 5: Implement Job 1 — changie state detection

**Files:**
- Modify: `.github/workflows/release.yml` — append to the `release` job's steps.

- [ ] **Step 1: Append the detection step** to the `release` job's `steps:` (after the `Verify tag points to a commit on main` step):

```yaml
      - name: Detect changelog state
        id: changelog
        env:
          TAG: ${{ github.ref_name }}
        run: |
          version="${TAG#v}"
          if [ -f ".changes/${version}.md" ]; then
            echo "mode=existing" >> "$GITHUB_OUTPUT"
            echo "Release notes already exist at .changes/${version}.md"
          elif [ -n "$(ls .changes/unreleased/ 2>/dev/null | grep -v .gitkeep)" ]; then
            echo "mode=batch" >> "$GITHUB_OUTPUT"
            echo "Unreleased fragments found — will batch"
          else
            echo "::error::No release notes and no unreleased changelog entries. Nothing to release."
            exit 1
          fi
```

- [ ] **Step 2: Append the version-match validation step** (this is the Python-specific guard that has no parallel in agent-quota):

```yaml
      - name: Verify pyproject.toml version matches tag
        env:
          TAG: ${{ github.ref_name }}
        run: |
          version="${TAG#v}"
          pyproject_version=$(python -c "import tomllib, pathlib; print(tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['version'])")
          if [ "$version" != "$pyproject_version" ]; then
            echo "::error::Tag ${TAG} does not match pyproject.toml version ${pyproject_version}. Bump pyproject.toml first."
            exit 1
          fi
          echo "Version match: ${pyproject_version}"
```

- [ ] **Step 3: Validate YAML parses**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```
Expected: no output, exit code 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Detect changelog state and verify pyproject version matches tag"
```

---

## Task 6: Implement Job 1 — pixi setup + verification matrix

**Files:**
- Modify: `.github/workflows/release.yml` — append more steps to the `release` job.

- [ ] **Step 1: Append the pixi setup step** (after the version-match step):

```yaml
      - name: Set up pixi
        uses: prefix-dev/setup-pixi@v0.8.1
        with:
          pixi-version: latest
          cache: true
          environments: dev release
```

- [ ] **Step 2: Append the verification step**:

```yaml
      - name: Run release verification checks
        run: |
          pixi run -e dev check-format
          pixi run -e dev lint
          pixi run -e dev typecheck
          pixi run -e dev test
          pixi run -e release build-dist
          test -n "$(ls dist/pgmimic-*.tar.gz 2>/dev/null)" || { echo "::error::missing sdist in dist/"; exit 1; }
          test -n "$(ls dist/pgmimic-*.whl 2>/dev/null)" || { echo "::error::missing wheel in dist/"; exit 1; }
          ls dist/
```

(The final two `test` lines are hard gates — the workflow fails fast in Job 1 if either artifact is missing rather than letting Job 2 discover it later. The trailing `ls dist/` is left in for human-friendly log output.)

- [ ] **Step 3: Validate YAML parses**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```
Expected: no output, exit code 0.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Add pixi setup and verification matrix (lint/typecheck/test/build) to release job"
```

---

## Task 7: Implement Job 1 — changie batch, commit, and force-move tag

**Files:**
- Modify: `.github/workflows/release.yml` — append the batch-mode steps to the `release` job.

- [ ] **Step 1: Append the changie install step** (all four following steps gate on `steps.changelog.outputs.mode == 'batch'` — keep that condition):

```yaml
      - name: Install changie
        if: steps.changelog.outputs.mode == 'batch'
        uses: miniscruff/changie-action@v3
        with:
          version: latest

      - name: Batch and merge changelog
        if: steps.changelog.outputs.mode == 'batch'
        env:
          TAG: ${{ github.ref_name }}
        run: |
          version="${TAG#v}"
          changie batch "$version"
          changie merge

      - name: Commit changelog updates
        if: steps.changelog.outputs.mode == 'batch'
        env:
          TAG: ${{ github.ref_name }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .changes/ CHANGELOG.md
          git commit -m "chore: update changelog for ${TAG}"
          git push origin HEAD:main

      - name: Move tag to include changelog commit
        if: steps.changelog.outputs.mode == 'batch'
        env:
          TAG: ${{ github.ref_name }}
        run: |
          git tag -f "$TAG"
          git push origin "$TAG" --force
```

- [ ] **Step 2: Validate YAML parses**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Batch changelog, commit to main, and force-move release tag"
```

---

## Task 8: Implement Job 2 — build, checksum, release notes, GitHub release

**Files:**
- Modify: `.github/workflows/release.yml` — replace the `build-publish` job's `steps:` block.

- [ ] **Step 1: Replace the `build-publish.steps:` block** with:

```yaml
    steps:
      - name: Check out code at updated tag
        uses: actions/checkout@v6
        with:
          ref: ${{ github.ref_name }}
          fetch-depth: 0

      - name: Set up pixi
        uses: prefix-dev/setup-pixi@v0.8.1
        with:
          pixi-version: latest
          cache: true
          environments: release

      - name: Build sdist + wheel
        run: |
          rm -rf dist/
          pixi run -e release build-dist

      - name: Generate checksums
        run: |
          cd dist
          sha256sum *.tar.gz *.whl > checksums.txt
          cat checksums.txt

      - name: Prepare release notes
        env:
          TAG: ${{ github.ref_name }}
        run: |
          version="${TAG#v}"
          cp ".changes/${version}.md" release-notes.md
          cat release-notes.md

      - name: Create GitHub release
        uses: softprops/action-gh-release@v3
        with:
          body_path: release-notes.md
          files: |
            dist/*.tar.gz
            dist/*.whl
            dist/checksums.txt
```

- [ ] **Step 2: Validate YAML parses**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "Build sdist+wheel, generate checksums, publish GitHub release"
```

---

## Task 9: Lint the workflow file

**Why this matters:** `actionlint` catches workflow-specific bugs (bad action references, shellcheck issues in `run:` blocks, expression typos) that plain YAML parsing misses.

**Files:**
- Modify: `.github/workflows/release.yml` only if lint surfaces issues.

- [ ] **Step 1: Run actionlint**

If `actionlint` is not on PATH, install it ad-hoc:

```bash
bash <(curl -sSf https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)
./actionlint .github/workflows/release.yml
```

Or, if you have Go installed:
```bash
go install github.com/rhysd/actionlint/cmd/actionlint@latest
actionlint .github/workflows/release.yml
```

Expected: no findings. If `actionlint` flags issues, fix them in-place and re-run. The most common findings on this style of workflow are:
- "shellcheck reported issue: SC2086: Double quote to prevent globbing and word splitting" → wrap variable expansions in `"..."`.
- "expression with invalid action reference" → fix the `uses:` pin.

- [ ] **Step 2: If you fixed anything, commit**

```bash
git add .github/workflows/release.yml
git commit -m "Address actionlint findings in release workflow"
```

(If actionlint reported no issues, skip the commit.)

---

## Task 10: Verify the full workflow file as a final read-through

**Why this matters:** This is the visual diff against the reference (`agent-quota/.github/workflows/release.yml`) — easier to spot drift while the file is fresh.

**Files:**
- Read: `.github/workflows/release.yml`
- Read (reference): `../agent-quota/.github/workflows/release.yml`

- [ ] **Step 1: Side-by-side diff against the reference**

```bash
diff -u ../agent-quota/.github/workflows/release.yml .github/workflows/release.yml || true
```

(The output will be long — that's fine. Read it and confirm the only intentional differences are: Go → pixi setup, `go test/go build` → pixi tasks, archive logic → sdist/wheel logic, install.sh dropped, `ldflags` dropped, version-match step added.)

- [ ] **Step 2: Confirm `if: !endsWith(github.actor, '[bot]')` guard is present on both jobs**

Run:
```bash
grep -c "endsWith(github.actor, '\[bot\]')" .github/workflows/release.yml
```
Expected: `2` (one per job).

- [ ] **Step 3: Confirm both jobs run on `ubuntu-latest`**

```bash
grep -c "ubuntu-latest" .github/workflows/release.yml
```
Expected: `2`.

- [ ] **Step 4: No commit needed** — this is read-only verification.

---

## Task 11: Document the release process in CONTRIBUTING.md

**Files:**
- Modify: `/home/schnetlerr/dev/PostgresMimicImporter.feat-gh-release/CONTRIBUTING.md` — append a "Releasing" section after the "Review Process" section.

- [ ] **Step 1: Append the new section** at the end of `CONTRIBUTING.md`:

```markdown

## Releasing

Releases are driven by tag pushes matching `v*` — the `.github/workflows/release.yml` workflow handles changelog batching, building artifacts, and publishing the GitHub release.

### One-time setup

The workflow authenticates as a dedicated GitHub App to push the changelog commit and force-move the release tag (a default `GITHUB_TOKEN` can't push to a branch-protected `main`). Maintainers need:

1. A GitHub App installed on the repo with `contents: write`.
2. Repo variable `RELEASE_APP_ID` set to the App ID.
3. Repo secret `RELEASE_APP_PRIVATE_KEY` set to the App's private key (`.pem` contents).

### Cutting a release

1. Add changie fragments for everything new since the last release: `pixi run -e dev changie new` (or run `changie new` directly if you have it on PATH). Commit them.
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
```

- [ ] **Step 2: Verify it renders sensibly**

```bash
grep -A 2 "## Releasing" CONTRIBUTING.md
```
Expected: the new heading and a paragraph beneath it.

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "Document release process in CONTRIBUTING.md"
```

---

## Task 12: Final review and prep for first release

- [ ] **Step 1: Confirm all commits are on `feat/gh-release` branch**

```bash
git log --oneline main..HEAD
```
Expected: a clean series of small commits (one per task) ending with the docs update.

- [ ] **Step 2: Push the branch and open a PR**

```bash
git push -u origin feat/gh-release
gh pr create --title "Add tag-triggered release workflow" --body "$(cat <<'EOF'
## Summary
- Add `.github/workflows/release.yml` that mirrors the `agent-quota` release flow, adapted for Python/pixi.
- Add a `release` pixi feature (`python-build` + `hatchling`) for building sdist + wheel.
- Add `[build-system]` to `pyproject.toml`.
- Document the release process in `CONTRIBUTING.md`.

## Test plan
- [ ] CI workflow file parses (validated locally with actionlint).
- [ ] `pixi run -e release build-dist` produces a valid sdist + wheel locally.
- [ ] After merge: set `RELEASE_APP_ID` + `RELEASE_APP_PRIVATE_KEY` repo secrets, then tag `v0.0.5` as a dry-run release to confirm the workflow runs end-to-end.
EOF
)"
```

- [ ] **Step 3: After merge — do a smoke release**

This is the only real end-to-end test for a GitHub Actions workflow. To execute it:

1. On `main`: bump `pyproject.toml` version to a fresh patch (e.g. `0.0.5`). Add at least one changie fragment if there aren't any. Commit, push.
2. Tag and push: `git tag v0.0.5 && git push origin v0.0.5`.
3. Watch the run: `gh run watch`.
4. Inspect the resulting release: `gh release view v0.0.5`.

If the smoke release fails, the most likely culprits (in order of probability) are:
- `RELEASE_APP_ID` / `RELEASE_APP_PRIVATE_KEY` not set or malformed (App private key needs the full PEM including BEGIN/END markers and newlines).
- App lacks `contents: write` or isn't installed on the repo.
- Branch protection on `main` blocks the App's push (add the App to the bypass list).
- `pixi.lock` not committed after Task 2 (`pixi install -e release` regenerates it; ensure it's committed).
- `hatchling` couldn't auto-discover `pgmimic/` (fall back to the `[tool.hatch.build.targets.wheel] packages = ["pgmimic"]` stanza noted in Task 2 Step 5).

---

## Self-Review

**1. Spec coverage:**
- Tag-triggered release: ✅ Task 3 (skeleton with `on: push: tags: v*`).
- Same release method as agent-quota: ✅ Tasks 4–8 mirror the reference workflow step-for-step.
- Changie management: ✅ Tasks 5 + 7 detect state and batch+merge fragments, with the same `existing` / `batch` / error modes.
- GH release: ✅ Task 8 uses `softprops/action-gh-release@v3` with `.changes/<version>.md` body and dist files.
- Python-specific adaptations (no Go): ✅ Tasks 1, 2, 6, 8 swap Go build for pixi + hatchling sdist/wheel.
- Bot setup (user does this manually): ✅ Prerequisites section + Task 11 documents it.

**2. Placeholder scan:** No "TBD" / "implement later" / "add error handling" / "similar to Task N" patterns. Each step contains exact commands and exact YAML/TOML content.

**3. Type / name consistency:**
- pixi env `release` is referenced consistently across Tasks 2, 6, 8, 11.
- pixi task `build-dist` is referenced consistently across Tasks 2, 6, 8.
- `.changes/${version}.md` (with the `v` stripped) used consistently in Tasks 5, 7, 8.
- Action versions consistent: `actions/create-github-app-token@v3`, `actions/checkout@v6`, `miniscruff/changie-action@v3`, `softprops/action-gh-release@v3`, `prefix-dev/setup-pixi@v0.8.1`.
- Step ordering across Tasks 4–7 is additive (each appends to the previous job's steps), with no contradictory edits.

**Open question to flag to the reviewer:** is `pixi.lock` likely to churn noisily when the `release` env is added, given the existing `solve-group = "default"`? Worth confirming with a local `pixi install -e release` and inspecting the diff before committing in Task 2.
