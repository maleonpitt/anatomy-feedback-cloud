variable "aws_region" {
  description = "AWS region for the hypothetical deployment (placeholder)."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for resource names in this learning model."
  type        = string
  default     = "anatomy-feedback-api"
}

variable "vpc_id" {
  description = "Existing VPC ID (placeholder — replace in a real deployment)."
  type        = string
  default     = "vpc-PLACEHOLDER"
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB (minimum two AZs in production)."
  type        = list(string)
  default     = ["subnet-PUBLIC-A-PLACEHOLDER", "subnet-PUBLIC-B-PLACEHOLDER"]
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for backend EC2 instances."
  type        = list(string)
  default     = ["subnet-PRIVATE-A-PLACEHOLDER", "subnet-PRIVATE-B-PLACEHOLDER"]
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS listener (placeholder — not created here)."
  type        = string
  default     = "arn:aws:acm:us-east-1:000000000000:certificate/PLACEHOLDER"
}

variable "backend_ami_id" {
  description = "AMI for EC2 instances running the API container (placeholder)."
  type        = string
  default     = "ami-PLACEHOLDER"
}

variable "backend_instance_type" {
  description = "EC2 instance type for API hosts."
  type        = string
  default     = "t3.small"
}

variable "app_port" {
  description = "Port Uvicorn listens on inside EC2/Docker (matches backend/Dockerfile)."
  type        = number
  default     = 5000
}

variable "backend_instance_count" {
  description = "Number of EC2 API instances (EC2-A, EC2-B, ...)."
  type        = number
  default     = 2
}

variable "health_check_path" {
  description = "ALB target group health check path (FastAPI /health)."
  type        = string
  default     = "/health"
}

# --- Phase 7: frontend static hosting (separate from category-data S3) ---

variable "frontend_bucket_name" {
  description = "Private S3 bucket for React build artifacts (placeholder name)."
  type        = string
  default     = "anatomy-feedback-frontend-PLACEHOLDER"
}

variable "frontend_domain_name" {
  description = "Hypothetical CloudFront alias (e.g. app.example.com)."
  type        = string
  default     = "app.example.com"
}

variable "frontend_certificate_arn" {
  description = "ACM cert ARN in us-east-1 for CloudFront (placeholder)."
  type        = string
  default     = "arn:aws:acm:us-east-1:000000000000:certificate/FRONTEND-PLACEHOLDER"
}

variable "category_data_bucket_name" {
  description = "Placeholder for Phase 4 category CSV bucket (backend env CATEGORY_BUCKET_NAME — not the frontend bucket)."
  type        = string
  default     = "anatomy-feedback-categories-PLACEHOLDER"
}

# --- EKS / ECR practice (primary path; code-only — do not apply) ---

variable "aws_account_id_placeholder" {
  description = "Documented practice account ID (not used to call AWS)."
  type        = string
  default     = "423687459077"
}

variable "ecr_repository_name" {
  description = "ECR repository name for the FastAPI image."
  type        = string
  default     = "anatomy-feedback-api"
}

variable "eks_cluster_name" {
  description = "EKS cluster name."
  type        = string
  default     = "anatomy-feedback-eks"
}

variable "eks_kubernetes_version" {
  description = "Kubernetes version for the EKS control plane."
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_type" {
  description = "Instance type for the managed node group."
  type        = string
  default     = "t3.medium"
}

variable "eks_node_desired_size" {
  type    = number
  default = 2
}

variable "eks_node_min_size" {
  type    = number
  default = 1
}

variable "eks_node_max_size" {
  type    = number
  default = 3
}
