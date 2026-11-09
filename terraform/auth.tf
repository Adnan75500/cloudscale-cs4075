
resource "aws_cognito_user_pool" "main" {
  name                     = "cloudscale-users"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = false
  }
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "cloudscale-${data.aws_caller_identity.me.account_id}"
  user_pool_id = aws_cognito_user_pool.main.id
}

resource "aws_cognito_user_pool_client" "web" {
  name            = "cloudscale-web"
  user_pool_id    = aws_cognito_user_pool.main.id
  generate_secret = false

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email"]

  callback_urls = [
    "https://${aws_cloudfront_distribution.app.domain_name}/callback"
  ]

  logout_urls = [
    "https://${aws_cloudfront_distribution.app.domain_name}/"
  ]

  supported_identity_providers = ["COGNITO"]

  explicit_auth_flows = ["ALLOW_REFRESH_TOKEN_AUTH"]
}
