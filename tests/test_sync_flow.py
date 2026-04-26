"""Tests for scripts/sync_flow.py"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
SCRIPT = REPO_ROOT / "scripts" / "sync_flow.py"
REF_DIR = REPO_ROOT / "skills" / "seo-flow" / "references"


def test_dry_run_exits_zero():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, f"Dry run failed:\n{result.stderr}"


def test_dry_run_produces_valid_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, f"Dry run failed:\n{result.stderr}"
    data = json.loads(result.stdout)
    assert "added" in data, "JSON missing 'added' key"
    assert "updated" in data, "JSON missing 'updated' key"
    assert "unchanged" in data, "JSON missing 'unchanged' key"


def test_dry_run_does_not_write_files():
    files_before = set(REF_DIR.rglob("*.md"))
    subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        capture_output=True, cwd=REPO_ROOT
    )
    files_after = set(REF_DIR.rglob("*.md"))
    assert files_before == files_after, (
        f"Dry run created unexpected files: {files_after - files_before}"
    )


def test_real_sync_produces_prompts_per_stage():
    """After a real sync, every FLOW stage directory must contain at least one prompt file."""
    prompts_dir = REF_DIR / "prompts"
    if not prompts_dir.exists():
        return  # sync not yet run — skip silently

    expected_stages = ["find", "leverage", "optimize", "win", "local"]
    missing = [
        stage for stage in expected_stages
        if not (prompts_dir / stage).exists() or not list((prompts_dir / stage).glob("*.md"))
    ]
    assert not missing, f"Stages with no prompts after sync: {missing}"

    prompt_files = [f for f in prompts_dir.rglob("*.md") if f.name != "README.md"]
    assert len(prompt_files) > 0, "Sync produced no prompt files"


def test_synced_files_have_attribution_headers():
    """Every synced prompt file must start with the CC BY 4.0 attribution comment."""
    prompts_dir = REF_DIR / "prompts"
    if not prompts_dir.exists():
        return  # sync not yet run — skip silently

    attribution_prefix = "<!-- Source: github.com/AgriciDaniel/flow"
    failures = []
    for md_file in prompts_dir.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        content = md_file.read_text(encoding="utf-8")
        if not content.startswith(attribution_prefix):
            failures.append(str(md_file.relative_to(REPO_ROOT)))

    assert not failures, (
        "Files missing attribution headers:\n" + "\n".join(failures)
    )
