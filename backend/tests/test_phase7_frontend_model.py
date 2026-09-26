"""Static checks for Phase 7 CloudFront + S3 frontend model (no AWS)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = REPO_ROOT / "infra"
FRONTEND_APP = REPO_ROOT / "frontend" / "src" / "App.js"
PHASE7_DOC = REPO_ROOT / "docs" / "PHASE_7_CLOUDFRONT.md"


@pytest.fixture
def frontend_tf() -> str:
    return (INFRA_DIR / "frontend.tf").read_text()


@pytest.fixture
def app_js() -> str:
    return FRONTEND_APP.read_text()


def test_frontend_uses_env_api_base_without_api_prefix(app_js):
    assert "process.env.REACT_APP_API_BASE_URL" in app_js
    assert "`${API_BASE_URL}/send-feedback`" in app_js
    assert "`${API_BASE_URL}/get-session-email`" in app_js
    assert "/api/" not in app_js


def test_no_hardcoded_live_domains_in_app_js(app_js):
    forbidden = ["heilab.pitt.edu", "app.example.com", "api.example.com"]
    for domain in forbidden:
        assert domain not in app_js


def test_frontend_tf_models_private_s3_and_cloudfront(frontend_tf):
    assert 'resource "aws_s3_bucket" "frontend"' in frontend_tf
    assert 'resource "aws_s3_bucket_public_access_block" "frontend"' in frontend_tf
    assert "block_public_acls       = true" in frontend_tf
    assert 'resource "aws_cloudfront_origin_access_control" "frontend"' in frontend_tf
    assert 'resource "aws_cloudfront_distribution" "frontend"' in frontend_tf
    assert "public-read" not in frontend_tf


def test_cloudfront_spa_fallback_to_index_html(frontend_tf):
    assert 'response_page_path    = "/index.html"' in frontend_tf
    assert "error_code            = 404" in frontend_tf
    assert "error_code            = 403" in frontend_tf
    assert 'response_code         = 200' in frontend_tf


def test_cloudfront_default_root_object(frontend_tf):
    assert 'default_root_object = "index.html"' in frontend_tf


def test_category_and_frontend_buckets_documented_separately(frontend_tf):
    variables = (INFRA_DIR / "variables.tf").read_text()
    assert "frontend_bucket_name" in variables
    assert "category_data_bucket_name" in variables
    assert "anatomy-feedback-frontend-PLACEHOLDER" in variables
    assert "anatomy-feedback-categories-PLACEHOLDER" in variables


def test_no_real_production_ids_in_frontend_infra(frontend_tf):
    combined = frontend_tf + (INFRA_DIR / "variables.tf").read_text()
    assert "heilab" not in combined.lower()
    assert "PLACEHOLDER" in combined


def test_phase7_documentation_exists():
    assert PHASE7_DOC.is_file()
    text = PHASE7_DOC.read_text()
    assert "CloudFront" in text
    assert "Nginx is not" in text or "Nginx is **not**" in text
    assert "/api" in text


def test_no_nginx_in_active_compose_or_repo():
    root_compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "feedback-nginx" not in root_compose
    assert "nginx" not in root_compose.lower()
    assert not (REPO_ROOT / "legacy").exists()
    assert not (REPO_ROOT / "nginx").exists()


def test_backend_alb_model_still_present():
    main_tf = (INFRA_DIR / "main.tf").read_text()
    assert 'resource "aws_lb" "api"' in main_tf
    assert 'resource "aws_lb_target_group" "api"' in main_tf
