# Security & hardening — starter-app

Status as of 15 Nov 2026. Repository is **public**, so rulesets, secret scanning and CodeQL are free.

Legend: 🔴 do next · 🟠 recommended · 🟢 later

---

## ✅ Current setup

### Repository

- Public repository
- Ruleset on `main` (`Ruleset1`), no bypass:
  - Pull request required (0 approvals, squash merge only, stale approvals dismissed, conversations must be resolved)
  - Required checks: `test`, `gitleaks`, `bandit`, `hadolint`, `build-scan-push`
  - Linear history, deletion blocked, force push blocked
- Dependabot alerts + security updates enabled

### CI pipeline (`.github/workflows/ci.yml`)

- Runs on every pull request and on push to `main`
- `test`: pytest
- `gitleaks`: secrets in full git history (open-source CLI, checksum verified)
- `bandit`: Python code (fails on HIGH)
- `hadolint`: Dockerfile lint
- `build-scan-push`: build → Syft SBOM (artifact) → Trivy (fails on fixable HIGH/CRITICAL) → push to ghcr.io (`main` only)
- `pr-summary`: posts a results table on each pull request
- All actions pinned to full commit SHA
- Default token read-only; `packages: write` only on the build job

### Dependabot (`.github/dependabot.yml`)

- Weekly: pip (grouped), Docker base image, GitHub Actions

### Container image

- `apt-get upgrade` at build (Debian security fixes)
- Runs as non-root user, with health check
- Gunicorn with threads; Flask debug mode off by default

---

## 🔧 Improvements

### 🔴 Do next

- [ ] **Remove pip from the image**: `pip uninstall -y pip` after installing requirements (fixes the 5 Trivy findings on PR #3)
- [ ] **Align Python versions**: `python-version` in `ci.yml` = Python version in `Dockerfile`
- [ ] **Decide on Python 3.15** (PR #3): upgrade + align CI, or close it and ignore minor bumps in `dependabot.yml`
- [ ] **Check the ruleset**: target = default branch only; no stale checks (`build-and-push`, `Dependabot`, `.github/dependabot.yml`); rename to `protect-main`
- [ ] **Enforce SHA pinning**: Settings → Actions → General → _Require actions to be pinned to a full-length commit SHA_
- [ ] **Enable free public-repo features**: Settings → Advanced Security → secret scanning, push protection, CodeQL (default setup), private vulnerability reporting
- [ ] **Fix git identity**: `git config --global user.email` must match an email on the `pabloortolan` account (commits currently show `anchovies-world`)

### 🟠 Recommended

- [ ] **Commit signing** (SSH key, type _Signing Key_), then tick _Require signed commits_ in the ruleset
- [ ] **Ruleset**: tick _Require branches to be up to date before merging_
- [ ] **Actions allow-list**: Settings → Actions → General → allow only GitHub + `docker/*`, `anchore/*`, `aquasecurity/*`
- [ ] **Workflow permissions**: Settings → Actions → General → read-only; _Allow Actions to create/approve PRs_ unticked
- [ ] **Pin base image by digest**: `FROM python:X-slim@sha256:…` (Dependabot updates it)
- [ ] **Hadolint fixes**: `CMD` in JSON form (DL3025); numeric user `--uid 10001` + `USER 10001` (DL3066)
- [ ] **General settings**: squash merge only, auto-delete head branches, allow auto-merge
- [ ] **Auto-merge Dependabot patch updates** when all checks pass
- [ ] **Tag ruleset** `v*`: block updates and deletions
- [ ] **Package settings** (ghcr.io): choose visibility; restrict write access to this repository
- [ ] **Files**: `SECURITY.md` (how to report a vulnerability), `.github/CODEOWNERS`
- [ ] **Account**: 2FA with passkey; tokens with expiry and minimal scopes

### 🟢 Later

- [ ] **Multi-stage build** or distroless image: no shell or package manager at runtime
- [ ] **Artifact attestations**: sign the image and SBOM (`actions/attest-build-provenance`), free on public repos
- [ ] **Copa**: auto-patch OS vulnerabilities found by Trivy
- [ ] **Approvals = 1** once a second person contributes
- [ ] **OIDC** instead of stored cloud keys when deploying

---

## 🔁 Routine

- **Weekly**: merge or close Dependabot pull requests
- **Monthly**: review Security tab alerts; check token expirations
- **Every 6 months**: re-read this file
