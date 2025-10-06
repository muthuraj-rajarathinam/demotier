# Launch Template
resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-lt"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  key_name      = "DEMOEC2"
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  user_data = base64encode(templatefile("${path.module}/../scripts/install_app.sh.tpl", {
    db_endpoint = aws_db_instance.mysql.endpoint
    db_user     = var.db_username
    db_pass     = var.db_password
  }))
}

# Auto Scaling Group
resource "aws_autoscaling_group" "app_asg" {
  desired_capacity     = 2
  max_size             = 4
  min_size             = 2
  vpc_zone_identifier  = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.app_tg.arn]
}

# ALB
resource "aws_lb" "app_alb" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb_sg.id]
}

# Target Group
resource "aws_lb_target_group" "app_tg" {
  name     = "${var.project_name}-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/health"
    protocol            = "HTTP"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
  }
}

# Listener
resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

# AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "null_resource" "update_frontend_index" {
  # This ensures the provisioner runs after ALB creation
  triggers = {
    alb_dns = aws_lb.app_alb.dns_name
  }

  provisioner "local-exec" {
    command = "sed -i 's|__BACKEND_ALB_URL__|http://${aws_lb.app_alb.dns_name}|g' ../frontend/index.html"
  }
}