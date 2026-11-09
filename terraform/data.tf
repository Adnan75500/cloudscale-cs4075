
# ==========================================
# DYNAMODB LISTINGS TABLE
# ==========================================

resource "aws_dynamodb_table" "listings" {
  name         = "cloudscale-listings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "listing_id"

  attribute {
    name = "listing_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }
}
resource "random_password" "flask_key" {
  length  = 48
  special = false
}

resource "aws_ssm_parameter" "flask_key" {
  name  = "/cloudscale/flask-secret-key"
  type  = "SecureString"
  value = random_password.flask_key.result
}
data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}    