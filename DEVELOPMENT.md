# Feature development workflow

Use `work/feature-series` as the integration branch for the current four-feature
batch. Keep `main` as the stable baseline until the batch is ready for release.

Each feature gets its own branch, created from the latest integration branch.
This lets later features use earlier changes while preserving a reviewable
commit history and an individual merge commit for each feature.

## Current batch

1. `feature/tie-probabilities`: category and overall matchup ties.
2. `feature/projection-correctness`: nonoverlapping player history, consistent
   shooting projections, and incomplete-data handling.
3. `feature/projection-assumptions`: smooth preseason decay, fixed game recency,
   and shooting accuracy weighted by attempts.
4. Fourth feature: choose a descriptive branch when defined.

The tie feature's implementation and tests belong in one feature commit. Keep
follow-up commits for a feature on its own branch until it is integrated.

## Start a feature

Start with a clean working tree:

```sh
git switch work/feature-series
git switch -c feature/<name>
```

Implement and validate the feature, then stage its specific files and commit.
Avoid mixing unrelated fixes into that feature's commits.

## Validate and integrate

Run the checks relevant to the feature. For changes across the model and UI:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/mypy . --ignore-missing-imports
.venv/bin/flake8 --select=F401 api cat5 processor tests
npm run build
git diff --check
```

Commit all intended changes before switching branches, then integrate:

```sh
git switch work/feature-series
git merge --no-ff feature/<name>
```

Keep feature branches until the batch has shipped. Use a normal merge commit
rather than a squash or rebase so the integration history keeps feature
boundaries. If a feature must be removed after integration, revert its merge
commit with `git revert -m 1 <merge-commit>` and rerun the affected checks.
Later features may depend on it and need adjustments.

## Publish and release

Branches and commits remain local until publishing is requested. When remote
review is wanted, push the integration branch and the relevant feature branch;
open feature PRs against `work/feature-series`. Do not merge an already integrated
feature a second time through a PR.

After all four features are complete, rerun the full checks on the integration
branch and review its complete diff against `main`. Publish one release PR from
`work/feature-series` to `main`. Keep unrelated work out of the batch.

Before that release, fetch `origin` and merge any new `origin/main` changes into
the integration branch, then rerun checks. Do not rewrite published history or
force-push. Deployment is a separate step from merging.
