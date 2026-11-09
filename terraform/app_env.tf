
locals {
  app_env = {
    AWS_REGION   = var.region
    MEDIA_BUCKET = aws_s3_bucket.media.id
    CDN_DOMAIN   = aws_cloudfront_distribution.media.domain_name
    TABLE_NAME   = aws_dynamodb_table.listings.name

    COGNITO_DOMAIN    = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.region}.amazoncognito.com"
    COGNITO_CLIENT_ID = aws_cognito_user_pool_client.web.id
    COGNITO_POOL_ID   = aws_cognito_user_pool.main.id
    APP_URL           = "https://${aws_cloudfront_distribution.app.domain_name}"
  }
}
