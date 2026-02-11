resource "aws_security_group" "freeradius" {
  name        = "${var.project_name}-radius-sg"
  description = "Allow RADIUS UDP traffic and all egress"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-radius-sg"
  }
}

# RADIUS Authentication (UDP 1812)
resource "aws_vpc_security_group_ingress_rule" "radius_auth" {
  security_group_id = aws_security_group.freeradius.id
  description       = "RADIUS Authentication"
  ip_protocol       = "udp"
  from_port         = 1812
  to_port           = 1812
  cidr_ipv4         = var.radius_allowed_cidrs[0]
}

# RADIUS Accounting (UDP 1813)
resource "aws_vpc_security_group_ingress_rule" "radius_acct" {
  security_group_id = aws_security_group.freeradius.id
  description       = "RADIUS Accounting"
  ip_protocol       = "udp"
  from_port         = 1813
  to_port           = 1813
  cidr_ipv4         = var.radius_allowed_cidrs[0]
}

# All egress (for SSM agent, yum updates, S3 access)
resource "aws_vpc_security_group_egress_rule" "all_egress" {
  security_group_id = aws_security_group.freeradius.id
  description       = "Allow all outbound traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
