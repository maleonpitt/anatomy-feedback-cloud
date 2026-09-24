"""Static checks for Phase 6 ALB learning model (no AWS, no terraform apply)."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = REPO_ROOT / "infra"
DOCKERFILE = REPO_ROOT / "backend" / "Dockerfile"
PHASE6_DOC = REPO_ROOT / "docs" / "PHASE_6_ALB.md"


@pytest.fixture
def infra_main_tf() -> str:
    return (INFRA_DIR / "main.tf").read_text()


@pytest.fixture
def infra_variables_tf() -> str:
    return (INFRA_DIR / "variables.tf").read_text()


def test_health_endpoint_unchanged(client):
    """ALB target group expects existing FastAPI /health contract."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_dockerfile_uvicorn_binds_all_interfaces():
    content = DOCKERFILE.read_text()
    assert '"0.0.0.0"' in content
    assert '"5000"' in content
    assert "uvicorn" in content


def test_infra_directory_exists():
    assert INFRA_DIR.is_dir()
    for name in (
        "main.tf",
        "frontend.tf",
        "variables.tf",
        "outputs.tf",
        "versions.tf",
        "README.md",
    ):
        assert (INFRA_DIR / name).is_file()


def test_target_group_uses_health_path_and_app_port(infra_main_tf, infra_variables_tf):
    assert 'path                = var.health_check_path' in infra_main_tf
    assert 'default     = "/health"' in infra_variables_tf
    assert "port        = var.app_port" in infra_main_tf
    assert 'default     = 5000' in infra_variables_tf
    assert 'protocol    = "HTTP"' in infra_main_tf
    assert 'matcher             = "200"' in infra_main_tf


def test_backend_sg_allows_app_port_from_alb_only(infra_main_tf):
    assert "aws_security_group" in infra_main_tf
    assert "security_groups = [aws_security_group.alb.id]" in infra_main_tf
    backend_block = infra_main_tf.split('resource "aws_security_group" "backend"')[1]
    backend_ingress = backend_block.split("ingress {")[1].split("}")[0]
    assert "security_groups" in backend_ingress
    assert "0.0.0.0/0" not in backend_ingress


def test_alb_listener_https_443(infra_main_tf):
    assert 'resource "aws_lb_listener" "https"' in infra_main_tf
    assert "port              = 443" in infra_main_tf
    assert 'protocol          = "HTTPS"' in infra_main_tf
    assert "certificate_arn" in infra_main_tf


def test_ec2_private_no_public_ip(infra_main_tf):
    assert 'resource "aws_instance" "api"' in infra_main_tf
    assert "associate_public_ip_address = false" in infra_main_tf
    assert 'target_type = "instance"' in infra_main_tf


def test_no_real_production_resource_ids(infra_variables_tf):
    forbidden = [
        "app.heilab.pitt.edu",
        "vpc-0",
        "subnet-0",
        "i-0",
    ]
    combined = infra_variables_tf + (INFRA_DIR / "main.tf").read_text()
    for token in forbidden:
        assert token not in combined


def test_placeholders_used(infra_variables_tf):
    assert "PLACEHOLDER" in infra_variables_tf
    assert "vpc-PLACEHOLDER" in infra_variables_tf


def test_phase6_documentation_exists():
    assert PHASE6_DOC.is_file()
    text = PHASE6_DOC.read_text()
    assert "Target Group" in text
    assert "sticky sessions are not required" in text.lower() or "Sticky sessions are not required" in text
    assert "S3CategoryStore" in text or "S3" in text
