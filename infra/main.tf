# ------------------------------------------------------------------------------
# Security groups — Internet → ALB (443) → Backend (app_port only from ALB SG)
# ------------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "ALB: HTTPS from internet (hypothetical public API)"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Forward to backend targets"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
    Tier = "alb"
  }
}

resource "aws_security_group" "backend" {
  name        = "${var.project_name}-backend-sg"
  description = "Backend EC2: app port from ALB SG only (not open to internet)"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Uvicorn/FastAPI from ALB only"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound (Graph, OpenAI, S3 via NAT in real deploy)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-backend-sg"
    Tier = "backend"
  }
}

# ------------------------------------------------------------------------------
# Target group — registers healthy EC2 targets; does NOT run FastAPI
# ------------------------------------------------------------------------------

resource "aws_lb_target_group" "api" {
  name        = "${var.project_name}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    enabled             = true
    path                = var.health_check_path
    protocol            = "HTTP"
    port                = "traffic-port"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }

  tags = {
    Name = "${var.project_name}-target-group"
  }
}

# ------------------------------------------------------------------------------
# Application Load Balancer — public subnets, TLS termination at listener
# ------------------------------------------------------------------------------

resource "aws_lb" "api" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  tags = {
    Name = "${var.project_name}-alb"
    Tier = "alb"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.api.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# ------------------------------------------------------------------------------
# Backend EC2 (private subnets) — Docker → Uvicorn → FastAPI
# Option A: ALB → Target Group → EC2 (chosen for Phase 6 learning model)
# ------------------------------------------------------------------------------

resource "aws_instance" "api" {
  count = var.backend_instance_count

  ami                    = var.backend_ami_id
  instance_type          = var.backend_instance_type
  subnet_id              = var.private_subnet_ids[count.index % length(var.private_subnet_ids)]
  vpc_security_group_ids = [aws_security_group.backend.id]

  # No public IP — traffic arrives via ALB in public subnets.
  associate_public_ip_address = false

  tags = {
    Name = "${var.project_name}-api-${count.index + 1}"
    Tier = "backend"
  }

  # Real deploy: user_data would pull/run backend image with Uvicorn on 0.0.0.0:5000
  # user_data = file("${path.module}/user_data.sh")
}

resource "aws_lb_target_group_attachment" "api" {
  count = var.backend_instance_count

  target_group_arn = aws_lb_target_group.api.arn
  target_id        = aws_instance.api[count.index].id
  port             = var.app_port
}
