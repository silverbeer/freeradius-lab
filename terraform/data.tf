data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# AL2023 AMI via SSM parameter (always returns the latest)
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-${var.instance_architecture}"
}
