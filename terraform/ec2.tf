resource "aws_instance" "freeradius" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.freeradius.id]
  iam_instance_profile   = aws_iam_instance_profile.freeradius.name

  user_data = base64encode(templatefile("${path.module}/user_data.sh.tpl", {
    instance_architecture = var.instance_architecture
    rpm_bucket_name       = aws_s3_bucket.rpm_artifacts.id
  }))

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${var.project_name}-server"
  }
}
