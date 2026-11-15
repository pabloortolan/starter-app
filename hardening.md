# GitHub repository hardening checklist

Security configuration for the `starter-app` repository: what to turn on in GitHub's settings, where to find it, and why.

> **Plan check first.** Several features depend on the GitHub plan and on whether the repository is **public** or **private**:
>
> | Feature                                                | Public repo (any plan) | Private repo, GitHub Free            | Private repo, GitHub Pro / Team      |
> | ------------------------------------------------------ | ---------------------- | ------------------------------------ | ------------------------------------ |
> | Rulesets / branch protection                           | ✅                     | ❌                                   | ✅                                   |
> | Secret scanning + push protection                      | ✅                     | ❌ (paid add-on, organizations only) | ❌ (paid add-on, organizations only) |
> | CodeQL code scanning, Security tab for SARIF           | ✅                     | ❌                                   | ❌ (paid add-on)                     |
> | Dependabot alerts / security updates / version updates | ✅                     | ✅                                   | ✅                                   |
> | Actions settings (permissions, SHA pinning)            | ✅                     | ✅                                   | ✅                                   |
>
> If the repository stays **private on GitHub Free**, the ruleset section below can't be enforced. In that case either make the repository public (if the code isn't sensitive), upgrade to GitHub Pro, or rely on discipline plus the CI checks. Gitleaks in CI is what replaces GitHub's secret scanning on a private repository.

Legend: 🔴 do first · 🟠 recommended · 🟢 nice to have

---

## 1. Your GitHub account

The account is the key to everything else. Settings live under **profile picture → Settings**.

- [ ] 🔴 **Two-factor authentication**, preferably with a **passkey** or security key rather than SMS. _Password and authentication._
- [ ] 🔴 **Review personal access tokens.** _Developer settings → Personal access tokens._ Delete unused ones. Every token must have an **expiration date** and the **minimum scopes** (for example, `read:packages` only for pulling images from ghcr.io).
- [ ] 🟠 **Review SSH keys**, active sessions, and authorized OAuth / GitHub Apps. Remove anything you don't recognize.
- [ ] 🟢 **Sign your commits** (SSH or GPG key) so GitHub shows them as _Verified_. Required if you enable "Require signed commits" in the ruleset.

---

## 2. Branch ruleset for `main`

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**

- **Name:** `protect-main`
- **Enforcement status:** Active
- **Bypass list:** leave **empty**, so the rules also apply to you as admin. An empty bypass list is what makes the protection real.
- **Target branches:** _Add target → Include default branch_

Rules to enable:

- [ ] 🔴 **Restrict deletions.** Nobody can delete `main`.
- [ ] 🔴 **Block force pushes.** History on `main` can't be rewritten.
- [ ] 🔴 **Require a pull request before merging.**
  - Required approvals: **0** while you work alone (GitHub doesn't let you approve your own pull request). Raise it to **1** as soon as someone else joins.
  - ✅ Dismiss stale pull request approvals when new commits are pushed.
  - ✅ Require conversation resolution before merging.
  - Allowed merge methods: **Squash** only.
- [ ] 🔴 **Require status checks to pass.**
  - Add every job from the CI as it appears in a pull request's check list: `test`, `gitleaks`, `build-scan-push`, plus your Bandit and Hadolint jobs. Use their exact names.
  - ✅ Require branches to be up to date before merging. The checks then always run against the latest `main`.
- [ ] 🟠 **Require linear history.** Pairs with squash merging and keeps `main`'s history a straight line.
- [ ] 🟢 **Require signed commits.** Only after setting up commit signing (section 1).

**Test it:** open a pull request with a failing test. The **Merge** button must be greyed out, including for you.

---

## 3. Tag ruleset (for when you start releasing versions)

**Settings → Rules → Rulesets → New ruleset → New tag ruleset**

- **Target:** tag pattern `v*`
- [ ] 🟢 **Restrict updates** and **Restrict deletions.** A published `v1.2.0` always points to the same code. This prevents exactly the attack used against `trivy-action` (tags moved to malicious commits).

---

## 4. General repository settings

**Settings → General**

- [ ] 🟠 **Pull Requests:** allow **squash merging** only. Untick merge commits and rebase merging.
- [ ] 🟠 **Automatically delete head branches** after merge.
- [ ] 🟠 **Always suggest updating pull request branches.**
- [ ] 🟢 **Allow auto-merge.** Needed later for auto-merging small Dependabot updates. Safe only once the ruleset is active.
- [ ] 🟢 **Features:** turn off what you don't use (Wikis, Discussions, Projects). Less surface, less to maintain.
- [ ] 🔴 **Danger Zone → visibility:** a deliberate decision, private or public (see the plan check above).

---

## 5. GitHub Actions settings

**Settings → Actions → General**

- [ ] 🔴 **Actions permissions:** choose _Allow pinned / select actions_ and allow only:
  - actions created by GitHub
  - specific actions: `docker/*`, `anchore/*`, `aquasecurity/*` (plus any other action your workflows actually use)
- [ ] 🔴 **Require actions to be pinned to a full-length commit SHA.** Any workflow step using `@v4`-style tags will fail. The pipeline already pins everything, so this enforces it for the future. It also checks actions _used inside_ other actions.
- [ ] 🔴 **Workflow permissions:** _Read repository contents and packages permissions_. The workflow file then grants extra rights per job (as `ci.yml` does with `packages: write`).
- [ ] 🟠 **Allow GitHub Actions to create and approve pull requests:** leave **unticked** unless you build an auto-fix workflow. Even then, prefer a dedicated GitHub App token.
- [ ] 🟠 **Fork pull request workflows:** keep the default (forks of a private repository don't run workflows). If the repository becomes public: _Require approval for all external contributors_.

**Secrets:** _Settings → Secrets and variables → Actions_

- [ ] 🟠 Store nothing here that `GITHUB_TOKEN` can already do. The pipeline currently needs **no** secrets, which is the ideal.
- [ ] 🟢 When cloud deployment arrives: use **OIDC** (short-lived credentials issued per run) instead of long-lived cloud keys stored as secrets.

---

## 6. Security features

**Settings → Advanced Security** (called _Code security_ on some accounts)

- [ ] 🔴 **Dependency graph:** on.
- [ ] 🔴 **Dependabot alerts:** on.
- [ ] 🔴 **Dependabot security updates:** on. Opens fix pull requests for vulnerable dependencies.
- [ ] 🟠 **Grouped security updates:** on. One pull request per ecosystem instead of one per package.
- [ ] 🔴 **Dependabot version updates:** configured in `.github/dependabot.yml` (pip, docker, github-actions).
- [ ] 🟢 **If the repository is public:** also enable **secret scanning**, **push protection**, **CodeQL** (default setup) and **private vulnerability reporting**. All free on public repositories.

---

## 7. Container images (ghcr.io)

**Your profile → Packages → `starter-app` → Package settings**

- [ ] 🟠 **Visibility:** private, unless you want anyone to pull it.
- [ ] 🟠 **Manage Actions access:** only the `starter-app` repository can write to the package.
- [ ] 🟢 **Clean up old versions** from time to time (every push to `main` adds a new image tagged with the commit SHA).

---

## 8. Files in the repository

- [ ] 🟠 **`SECURITY.md`** at the root: how to report a vulnerability and who to contact. GitHub links to it from the Security tab.
- [ ] 🟢 **`.github/CODEOWNERS`**: who must review which files. For example, make yourself owner of `.github/workflows/` and `Dockerfile`, so changes to the pipeline always need your review once others contribute.

---

## 9. Already done ✅

Hardening that's already in place in the code:

- Every action in `ci.yml` pinned to a full commit SHA, with the version as a comment
- Read-only default token (`permissions: contents: read`), write access only where needed
- Image published only from `main`, only after tests and all scans pass
- Gitleaks (secrets), Bandit (Python code), Hadolint (Dockerfile), Syft (SBOM), Trivy (image vulnerabilities)
- Container runs as a non-root user, with a health check
- Dependabot for pip, Docker base image and GitHub Actions

---

## Review routine

| When           | What                                                        |
| -------------- | ----------------------------------------------------------- |
| Weekly         | Merge or close Dependabot pull requests                     |
| Monthly        | Check Security → Dependabot alerts; check token expirations |
| Every 6 months | Re-read this checklist: GitHub adds settings regularly      |
