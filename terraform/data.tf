
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
