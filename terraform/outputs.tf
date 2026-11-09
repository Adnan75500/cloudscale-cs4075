    output "media_bucket_name" {
  description = "Name of the private S3 media bucket"
  value       = aws_s3_bucket.media.id
}

output "media_cloudfront_domain" {
  description = "CloudFront domain for media delivery"
  value       = aws_cloudfront_distribution.media.domain_name
}