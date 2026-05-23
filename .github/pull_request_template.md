<!-- Thanks for contributing! See CONTRIBUTING.md for setup. -->

## Summary
<!-- One paragraph: what does this change do, and why? Link the issue if one exists. -->

## Test plan
- [ ] `pixi run -e dev lint check-format typecheck test validate-fixtures` all pass
- [ ] **If this change touches the importer or SQL assets:** I ran `pixi run -e dev e2e` against a real MIMIC-IV dataset on a server with `MIMIC_DATA_PATH` set, and the post-import `validate.sql` reported no row-count mismatches.
- [ ] If you added a user-facing change, you also ran `pixi run -e dev changie new` so the next release picks it up.

## Notes for reviewer
<!-- Anything the reviewer should know before reading the diff: tricky decisions, follow-ups, screenshots, etc. -->
