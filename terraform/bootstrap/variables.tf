variable "region" {
  description = "AWS region for the state backend resources"
  type        = string
  default     = "us-east-2"
}

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
  default     = "silverbeer"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "freeradius-lab"
}
