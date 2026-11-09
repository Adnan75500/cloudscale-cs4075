variable "bedrock_model_id" {
  description = "Bedrock model ID with on-demand access in your region (check the Bedrock model catalog)"
  default     = "amazon.nova-lite-v1:0"
}

resource "aws_s3_bucket" "ml" {
  bucket        = "cloudscale-ml-${data.aws_caller_identity.me.account_id}"
  force_destroy = true
}

resource "aws_iam_role" "sagemaker" {
  name = "cloudscale-sagemaker-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "sagemaker" {
  name = "sagemaker-access"
  role = aws_iam_role.sagemaker.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.ml.arn, "${aws_s3_bucket.ml.arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"]
        Resource = "arn:aws:ecr:${var.region}:*:repository/sagemaker-scikit-learn"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.me.account_id}:log-group:/aws/sagemaker/*"
      },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
      }
    ]
  })
}

output "sagemaker_role_arn" {
  value = aws_iam_role.sagemaker.arn
}

output "ml_bucket" {
  value = aws_s3_bucket.ml.id
}