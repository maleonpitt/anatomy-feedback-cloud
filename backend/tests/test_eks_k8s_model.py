"""Static checks for EKS/ECR/K8s practice manifests (no AWS apply)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA = REPO_ROOT / "infra"
K8S = REPO_ROOT / "k8s"
DOCKERFILE = REPO_ROOT / "backend" / "Dockerfile"


def test_eks_and_ecr_terraform_exist():
    assert (INFRA / "ecr.tf").is_file()
    assert (INFRA / "eks.tf").is_file()
    assert (INFRA / "eks_iam.tf").is_file()
    ecr = (INFRA / "ecr.tf").read_text()
    eks = (INFRA / "eks.tf").read_text()
    assert 'resource "aws_ecr_repository"' in ecr
    assert 'resource "aws_eks_cluster"' in eks
    assert 'resource "aws_eks_node_group"' in eks


def test_k8s_manifests_cover_api_path():
    for name in (
        "namespace.yaml",
        "configmap.yaml",
        "deployment.yaml",
        "service.yaml",
        "ingress.yaml",
        "secret.example.yaml",
        "README.md",
    ):
        assert (K8S / name).is_file()

    deployment = (K8S / "deployment.yaml").read_text()
    assert "path: /health" in deployment
    assert "containerPort: 5000" in deployment
    assert "423687459077.dkr.ecr" in deployment
    assert "anatomy-feedback-api" in deployment

    config = (K8S / "configmap.yaml").read_text()
    assert 'SKIP_AUTH: "false"' in config


def test_dockerfile_k8s_ready():
    text = DOCKERFILE.read_text()
    assert "HEALTHCHECK" in text
    assert "0.0.0.0" in text
    assert "SKIP_AUTH=false" in text
    assert '"5000"' in text


def test_eks_practice_doc_forbids_apply():
    doc = (REPO_ROOT / "docs" / "EKS_PRACTICE.md").read_text()
    assert "terraform apply" in doc.lower() or "Do not" in doc
    assert "423687459077" in doc
    assert "ECR" in doc and "EKS" in doc


def test_no_real_secrets_in_k8s_example():
    secret = (K8S / "secret.example.yaml").read_text()
    assert "REPLACE_ME" in secret
    assert "sk-proj-" not in secret
    assert "AKIA" not in secret
