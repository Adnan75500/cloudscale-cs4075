
data "aws_caller_identity" "me" {}

# ---- S3 bucket for application code ----
resource "aws_s3_bucket" "code" {
  bucket        = "cloudscale-code-${data.aws_caller_identity.me.account_id}"
  force_destroy = true
}

resource "aws_s3_object" "app" {
  bucket = aws_s3_bucket.code.id
  key    = "app.zip"
  source = "${path.module}/../build/app.zip"
  etag   = filemd5("${path.module}/../build/app.zip")
}

# ---- EC2 IAM role ----
resource "aws_iam_role" "ec2" {
  name = "cloudscale-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_app" {
  name = "cloudscale-app-access"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [

      {
        Effect = "Allow"

        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan",
          "dynamodb:DeleteItem"
        ]

        Resource = aws_dynamodb_table.listings.arn
      },

      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.code.arn}/app.zip"
      },
      {
        Effect = "Allow"

        Action = [
          "s3:PutObject"
        ]

        Resource = "${aws_s3_bucket.media.arn}/uploads/*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "cloudscale-ec2-profile"
  role = aws_iam_role.ec2.name
}

# ---- Launch template ----
resource "aws_launch_template" "app" {
  name_prefix            = "cloudscale-"
  image_id               = data.aws_ssm_parameter.al2023.value
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.app.id]
  update_default_version = true

  user_data = base64encode(templatefile("${path.module}/app_userdata.sh.tpl", {
    code_bucket = aws_s3_bucket.code.id
    region      = var.region
    env         = local.app_env
  }))

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2.name
  }

  metadata_options {
    http_tokens = "required"
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "cloudscale-app"
    }
  }
}

# ---- Application Load Balancer ----
resource "aws_lb" "app" {
  name               = "cloudscale-alb"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "app" {
  name     = "cloudscale-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 15
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# ---- Auto Scaling Group ----
resource "aws_autoscaling_group" "app" {
  name                      = "cloudscale-asg"
  min_size                  = 2
  desired_capacity          = 2
  max_size                  = 4
  vpc_zone_identifier       = aws_subnet.private[*].id
  target_group_arns         = [aws_lb_target_group.app.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "cloudscale-app"
    propagate_at_launch = true
  }

  depends_on = [
    aws_route_table_association.private,
    aws_s3_object.app
  ]
}

# ---- CPU target tracking ----
resource "aws_autoscaling_policy" "cpu" {
  name                   = "cpu-target-50"
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }

    target_value = 50
  }
}
