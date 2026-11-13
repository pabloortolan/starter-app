#!/usr/bin/env python3
"""Turn the scanners' JSON reports into Markdown.

Used by .github/workflows/ci.yml (standard library only, no install needed):

  ci_report.py section <tool> <report.json>   one tool's findings (for the job summary)
  ci_report.py comment <reports-dir>          the full PR comment (job results come from $NEEDS)

<tool> is one of: hadolint, bandit, gitleaks, trivy, sbom.
"""
import json
import os
import sys
from pathlib import Path

MARKER = "<!-- ci-security-summary -->"  # lets the workflow find and update its own comment
MAX_ROWS = 30  # keep the comment readable (and under GitHub's 65k character limit)
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4,
                  "error": 0, "warning": 1, "info": 2, "style": 3}

# tool -> (title, report file name)
TOOLS = {
    "gitleaks": ("Gitleaks — secrets in git history", "gitleaks.json"),
    "hadolint": ("Hadolint — Dockerfile lint", "hadolint.json"),
    "bandit": ("Bandit — Python code (MEDIUM+)", "bandit.json"),
    "trivy": ("Trivy — image vulnerabilities (HIGH+, fixable)", "trivy.json"),
    "sbom": ("Syft — SBOM", "sbom.spdx.json"),
}

# job id -> label, in pipeline order
JOBS = {
    "test": "Tests",
    "gitleaks": "Gitleaks",
    "hadolint": "Hadolint",
    "bandit": "Bandit",
    "build-scan-push": "Build + Syft + Trivy",
}
RESULT_ICON = {"success": "✅", "failure": "❌", "cancelled": "⏹️", "skipped": "⏭️"}


def cell(value):
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + " --- |" * len(headers)]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"\n_…and {len(rows) - MAX_ROWS} more, see the job log._")
    return "\n".join(lines)


def by_severity(rows):
    return sorted(rows, key=lambda r: SEVERITY_ORDER.get(r[0], 9))


# ---- one parser per tool: JSON -> (headers, rows) -------------------------

def parse_hadolint(data):
    rows = [(f["level"], f["code"], f"{f['file']}:{f['line']}", f["message"]) for f in data]
    return ("Level", "Rule", "Location", "Message"), by_severity(rows)


def parse_bandit(data):
    rows = [(r["issue_severity"], r["test_id"], f"{r['filename']}:{r['line_number']}",
             r["issue_text"]) for r in data.get("results", [])]
    return ("Severity", "Rule", "Location", "Issue"), by_severity(rows)


def parse_gitleaks(data):
    rows = [(f["RuleID"], f"{f['File']}:{f['StartLine']}", f.get("Commit", "")[:7],
             f.get("Description", "")) for f in (data or [])]
    return ("Rule", "Location", "Commit", "Description"), rows


def parse_trivy(data):
    rows = []
    for result in data.get("Results") or []:
        for v in result.get("Vulnerabilities") or []:
            rows.append((v["Severity"], v["VulnerabilityID"], v["PkgName"],
                         v.get("InstalledVersion"), v.get("FixedVersion"), v.get("Title", "")))
    return ("Severity", "ID", "Package", "Installed", "Fixed in", "Title"), by_severity(rows)


PARSERS = {"hadolint": parse_hadolint, "bandit": parse_bandit,
           "gitleaks": parse_gitleaks, "trivy": parse_trivy}


def section(tool, path):
    title, _ = TOOLS[tool]
    out = [f"### {title}", ""]
    path = Path(path)
    if not path.is_file():
        out.append("⏭️ No report: the scan did not run (an earlier job failed, or the scanner crashed).")
        return "\n".join(out)
    try:
        data = json.loads(path.read_text() or "null")
    except json.JSONDecodeError:
        out.append("⚠️ The report could not be read, see the job log.")
        return "\n".join(out)

    if tool == "sbom":
        out.append(f"📦 {len(data.get('packages', []))} packages listed. "
                   "The full SBOM is under **Artifacts** on the workflow run.")
        return "\n".join(out)

    headers, rows = PARSERS[tool](data)
    if not rows:
        out.append("✅ No findings.")
    else:
        out += [f"⚠️ **{len(rows)} finding(s)**", "", table(headers, rows)]
    return "\n".join(out)


def comment(reports_dir):
    needs = json.loads(os.environ.get("NEEDS", "{}"))
    sha = os.environ.get("HEAD_SHA", "")[:7]
    run_url = os.environ.get("RUN_URL", "")

    out = [MARKER, "## 🔒 CI security summary", "",
           f"Commit `{sha}` · [workflow run]({run_url})", "",
           "| Job | Result |", "| --- | --- |"]
    for job, label in JOBS.items():
        result = needs.get(job, {}).get("result", "unknown")
        out.append(f"| {label} | {RESULT_ICON.get(result, '❔')} {result} |")
    for tool, (_, filename) in TOOLS.items():
        out += ["", section(tool, Path(reports_dir) / filename)]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "section" and sys.argv[2] in TOOLS:
        print(section(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "comment":
        print(comment(sys.argv[2]))
    else:
        sys.exit(__doc__)
