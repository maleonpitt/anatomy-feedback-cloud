"""Phase 8 repository hygiene checks (static, no AWS)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_readme_exists():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "FastAPI" in readme
    assert "terraform apply" in readme.lower() or "not deployed" in readme.lower()


def test_modernization_summary_exists():
    doc = REPO_ROOT / "docs" / "MODERNIZATION_SUMMARY.md"
    assert doc.is_file()
    text = doc.read_text()
    assert "CloudFront" in text
    assert "MODELED" in text or "modeled" in text


def test_no_flask_monolith_in_active_backend():
    assert not (REPO_ROOT / "backend" / "app.py").exists()
    assert (REPO_ROOT / "backend" / "main.py").is_file()


def test_no_nginx_or_legacy_stack_in_repo():
    assert not (REPO_ROOT / "nginx").exists()
    assert not (REPO_ROOT / "legacy").exists()


def test_no_gunicorn_dependency():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text()
    assert "gunicorn" not in requirements.lower()
    assert "flask" not in requirements.lower()
    assert "fastapi" in requirements.lower()
    assert "uvicorn" in requirements.lower()


def test_frontend_api_paths_have_no_api_prefix():
    app_js = (REPO_ROOT / "frontend" / "src" / "App.js").read_text()
    assert "/api/" not in app_js
    assert "REACT_APP_API_BASE_URL" in app_js


def test_no_heilab_in_active_application_code():
    active_roots = [
        REPO_ROOT / "backend" / "main.py",
        REPO_ROOT / "backend" / "routers",
        REPO_ROOT / "backend" / "services",
        REPO_ROOT / "backend" / "core",
        REPO_ROOT / "frontend" / "src",
    ]
    for path in active_roots:
        if path.is_file():
            assert "heilab" not in path.read_text().lower()
        elif path.is_dir():
            for f in path.rglob("*.py"):
                assert "heilab" not in f.read_text().lower()


def test_infra_models_frontend_and_backend():
    assert (REPO_ROOT / "infra" / "main.tf").is_file()
    assert (REPO_ROOT / "infra" / "frontend.tf").is_file()
    variables = (REPO_ROOT / "infra" / "variables.tf").read_text()
    assert "frontend_bucket_name" in variables
    assert "category_data_bucket_name" in variables


def test_backup_archive_documented():
    """Historical backup is optional workspace material; document it in-repo docs."""
    summary = (REPO_ROOT / "docs" / "MODERNIZATION_SUMMARY.md").read_text()
    assert "anatomy-feedback-backup" in summary
    assert "historical" in summary.lower() or "Nothing unique is required" in summary

    readme = (REPO_ROOT / "README.md").read_text()
    # Cloud repo may point at v2 instead of the local backup folder.
    assert (
        "anatomy-feedback-backup" in readme
        or "anatomy-feedback-v2" in readme
        or "Related repos" in readme
    )
