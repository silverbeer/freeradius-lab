# S3 bucket for RPM artifact delivery (GHA uploads, EC2 pulls)
resource "aws_s3_bucket" "rpm_artifacts" {
  bucket        = "${var.project_name}-rpms-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Name = "${var.project_name}-rpms"
  }
}

resource "aws_s3_bucket_versioning" "rpm_artifacts" {
  bucket = aws_s3_bucket.rpm_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "rpm_artifacts" {
  bucket = aws_s3_bucket.rpm_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "rpm_artifacts" {
  bucket = aws_s3_bucket.rpm_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "rpm_artifacts" {
  bucket = aws_s3_bucket.rpm_artifacts.id

  rule {
    id     = "expire-old-rpms"
    status = "Enabled"

    filter {} # Apply to all objects

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}
