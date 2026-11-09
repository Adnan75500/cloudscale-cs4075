data "archive_file" "thumb" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/thumbnail"
  output_path = "${path.module}/../build/thumbnail.zip"
}

data "archive_file" "notifier" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/notifier"
  output_path = "${path.module}/../build/notifier.zip"
}

data "archive_file" "pillow" {
  type        = "zip"
  source_dir  = "${path.module}/../build/pillow-layer"
  output_path = "${path.module}/../build/pillow-layer.zip"
}

resource "aws_lambda_layer_version" "pillow" {
  layer_name               = "cloudscale-pillow"
  filename                 = data.archive_file.pillow.output_path
  source_code_hash         = data.archive_file.pillow.output_base64sha256
  compatible_runtimes      = ["python3.12"]
  compatible_architectures = ["x86_64"]
}

locals {
  lambda_assume = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# ---------- Thumbnail Lambda ----------
resource "aws_cloudwatch_log_group" "thumb" {
  name              = "/aws/lambda/cloudscale-thumbnail"
  retention_in_days = 14
}

resource "aws_iam_role" "thumb" {
  name               = "cloudscale-thumb-role"
  assume_role_policy = local.lambda_assume
}

resource "aws_iam_role_policy" "thumb" {
  name = "thumb-access"
  role = aws_iam_role.thumb.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.media.arn}/uploads/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.media.arn}/thumbs/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.thumb.arn}:*"
      }
    ]
  })
}

resource "aws_lambda_function" "thumb" {
  function_name    = "cloudscale-thumbnail"
  role             = aws_iam_role.thumb.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.thumb.output_path
  source_code_hash = data.archive_file.thumb.output_base64sha256
  layers           = [aws_lambda_layer_version.pillow.arn]
  memory_size      = 512
  timeout          = 30
  depends_on       = [aws_cloudwatch_log_group.thumb, aws_iam_role_policy.thumb]
}

resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.thumb.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.media.arn
}

resource "aws_s3_bucket_notification" "media" {
  bucket = aws_s3_bucket.media.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.thumb.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }
  depends_on = [aws_lambda_permission.s3_invoke]
}

# ---------- SQS + SNS ----------
resource "aws_sqs_queue" "dlq" {
  name                      = "cloudscale-responses-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "responses" {
  name                       = "cloudscale-responses"
  visibility_timeout_seconds = 180
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sns_topic" "responses" {
  name = "cloudscale-response-notifications"
}

# ---------- Notifier Lambda ----------
resource "aws_cloudwatch_log_group" "notifier" {
  name              = "/aws/lambda/cloudscale-notifier"
  retention_in_days = 14
}

resource "aws_iam_role" "notifier" {
  name               = "cloudscale-notifier-role"
  assume_role_policy = local.lambda_assume
}

resource "aws_iam_role_policy" "notifier" {
  name = "notifier-access"
  role = aws_iam_role.notifier.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.responses.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.responses.arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.notifier.arn}:*"
      }
    ]
  })
}

resource "aws_lambda_function" "notifier" {
  function_name    = "cloudscale-notifier"
  role             = aws_iam_role.notifier.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.notifier.output_path
  source_code_hash = data.archive_file.notifier.output_base64sha256
  timeout          = 30
  environment {
    variables = {
      TOPIC_ARN = aws_sns_topic.responses.arn
    }
  }
  depends_on = [aws_cloudwatch_log_group.notifier, aws_iam_role_policy.notifier]
}

resource "aws_lambda_event_source_mapping" "responses" {
  event_source_arn = aws_sqs_queue.responses.arn
  function_name    = aws_lambda_function.notifier.arn
  batch_size       = 1
}