locals {
  app_env = {
    AWS_REGION   = var.region
    MEDIA_BUCKET = aws_s3_bucket.media.id
    CDN_DOMAIN   = aws_cloudfront_distribution.media.domain_name
  }
}