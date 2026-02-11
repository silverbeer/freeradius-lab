# IAM role for EC2 instance — SSM access + S3 RPM bucket read
resource "aws_iam_role" "freeradius" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-ec2-role"
  }
}

# SSM managed policy — enables Session Manager access
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.freeradius.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Custom policy — read-only access to RPM artifact bucket
resource "aws_iam_role_policy" "s3_rpm_read" {
  name = "${var.project_name}-s3-rpm-read"
  role = aws_iam_role.freeradius.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.rpm_artifacts.arn,
          "${aws_s3_bucket.rpm_artifacts.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "freeradius" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.freeradius.name
}
