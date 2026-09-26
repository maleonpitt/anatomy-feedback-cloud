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
    assert (INFRA / "github_oidc.tf").is_file()
    assert (INFRA / "irsa_api.tf").is_file()
    assert (INFRA / "category_s3.tf").is_file()
    assert (INFRA / "secrets.tf").is_file()
    assert (INFRA / "eso_irsa.tf").is_file()
    ecr = (INFRA / "ecr.tf").read_text()
    eks = (INFRA / "eks.tf").read_text()
    oidc = (INFRA / "github_oidc.tf").read_text()
    secrets = (INFRA / "secrets.tf").read_text()
    assert 'resource "aws_ecr_repository"' in ecr
    assert 'resource "aws_eks_cluster"' in eks
    assert 'resource "aws_eks_node_group"' in eks
    assert "token.actions.githubusercontent.com" in oidc
    assert "github_deploy" in oidc
    assert 'resource "aws_secretsmanager_secret"' in secrets
    assert "REPLACE_ME_SET_AFTER_APPLY" in secrets


def test_k8s_manifests_cover_api_path():
    for name in (
        "namespace.yaml",
        "serviceaccount.yaml",
        "configmap.yaml",
        "deployment.yaml",
        "service.yaml",
        "ingress.yaml",
        "secret.example.yaml",
        "external-secret.yaml",
        "README.md",
    ):
        assert (K8S / name).is_file()

    deployment = (K8S / "deployment.yaml").read_text()
    assert "path: /health" in deployment
    assert "containerPort: 5000" in deployment
    assert "423687459077.dkr.ecr" in deployment
    assert "anatomy-feedback-api" in deployment
    assert "serviceAccountName: anatomy-feedback-api" in deployment

    sa = (K8S / "serviceaccount.yaml").read_text()
    assert "eks.amazonaws.com/role-arn" in sa

    ext = (K8S / "external-secret.yaml").read_text()
    assert "SecretsManager" in ext
    assert "anatomy-feedback/api" in ext
    assert "anatomy-feedback-api-secrets" in ext

    config = (K8S / "configmap.yaml").read_text()
    assert 'SKIP_AUTH: "false"' in config


def test_secrets_practice_doc_exists():
    doc = (REPO_ROOT / "docs" / "SECRETS_PRACTICE.md").read_text()
    assert "Secrets Manager" in doc
    assert "External Secrets" in doc
    assert "os.getenv" in doc


def test_cd_workflow_models_full_ship_path():
    cd = (REPO_ROOT / ".github" / "workflows" / "cd.yml").read_text()
    assert "workflow_dispatch" in cd
    assert "dry_run" in cd
    assert "amazon-ecr" in cd or "ECR" in cd
    assert "s3 sync" in cd
    assert "cloudfront" in cd.lower()
    assert "eks update-kubeconfig" in cd
    assert "configure-aws-credentials" in cd
    assert "id-token: write" in cd


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
