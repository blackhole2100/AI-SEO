# Public + private repo workflow

claude-seo is mirrored across two GitHub remotes. This document is the
canonical reference for how work flows between them.

## Topology

```
                    LOCAL CHECKOUT
                    (single source of truth)
                       │
        ┌──────────────┼──────────────┐
        │                             │
        ▼                             ▼
  origin (public)              aimh (private)
  AgriciDaniel/claude-seo      AI-Marketing-Hub/claude-seo
  - Release destination        - Daily development
  - main = released history    - main = synced with public
  - Tags = release history     - v2 = active development
  - Users discover here        - Dependabot + CI run here
```

Both remotes share git history because they were initialized from the
same local repository. Neither is a GitHub fork of the other.

## Day-to-day development

```bash
# Work on the active development branch
git checkout v2

# ...make changes, run tests...
git add <files>
git commit -m "feat: ..."

# Push to the PRIVATE remote (default for in-progress work)
git push aimh v2
```

The private repo runs Dependabot, GitHub Actions CI, and any pre-release
test gates. No need to touch the public remote for routine work.

## Promoting a release to public

When `v2` (or whatever branch holds the next release) is ready to go public:

1. **Locally**: merge into main and tag.
   ```bash
   git checkout main
   git merge --ff-only v2          # fast-forward only — no merge commits
   git tag -a v2.0.1 -m "release: v2.0.1"
   ```

2. **Push to private first** (private should never lag public).
   ```bash
   git push aimh main
   git push aimh v2.0.1
   ```

3. **Push to public** in tag-before-merge order (avoids the curl|bash
   outage window where users pull a tag that doesn't yet point at code
   on main).
   ```bash
   git push origin v2.0.1          # tag first
   git push origin main            # then branch
   ```

4. **Create the GitHub release** on the public repo only.
   ```bash
   gh release create v2.0.1 \
     --repo AgriciDaniel/claude-seo \
     --notes-from-tag \
     --verify-tag
   ```

5. **Publish the release blog post**.
   ```
   /release-blog
   ```

## Verification commands

```bash
# Confirm both remotes are wired up
git remote -v

# Confirm both remotes see the same main HEAD (should match after a release)
git ls-remote --heads aimh main
git ls-remote --heads origin main

# List tags on each (private will lead during pre-release work)
git ls-remote --tags aimh | grep -v '\^{}' | awk '{print $2}'
git ls-remote --tags origin | grep -v '\^{}' | awk '{print $2}'

# Confirm private has a v2 branch ahead of release
git fetch aimh
git log --oneline aimh/main..aimh/v2
```

## Why two repos?

- The **public** repo is the user-facing artifact. Everything visible
  there is releasable, documented, and supported.
- The **private** repo is the workshop. Work-in-progress branches,
  experimental phases (J, K, future phases), pre-release security audits,
  and unfinished thoughts live here. Dependabot churn and CI noise stay
  off the public timeline.

Public is for users. Private is for the work that becomes users' next
upgrade.

## Common pitfalls

| Pitfall | Avoid by |
|---|---|
| Pushing a tag to `origin` before its commit reaches `origin/main` | Always tag-before-merge: push tag first, then branch |
| `git push --tags` without specifying remote | Be explicit: `git push aimh --tags` or `git push origin v2.0.1` |
| Force-pushing to either remote | Don't, except with explicit per-operation authorization |
| Letting `aimh/main` lag behind `origin/main` | Always push to `aimh` first, then `origin` on release |
| Confusing `aimh/v2` with `origin/v2` | `origin` should never have an unreleased `v2` branch |

## State at the time of writing (2026-05-18)

- `aimh/main` = `7676024` (v1.9.9 final)
- `origin/main` = `7676024` (v1.9.9 final) ← synced
- `aimh/v2` = `6778786` (v2.0.0 + Phase J/K/audit cleanup)
- `origin` has no `v2` branch and no `v2.0.0` tag — both are pre-release
- `v2.0.0` tag lives on `aimh` only

This is the expected pre-release shape: private leads, public stays at
the last released version.

## Email-privacy caveat (one-time)

Two very old tags (`v1.2.0`, `v1.4.0`) could not be pushed to the
private repo because the underlying commits use a private email address
that GitHub now blocks. These tags remain available on `origin` only.
Not a regression — those releases shipped on public and are reachable
there.
