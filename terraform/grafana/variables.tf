variable "grafana_url" {
  description = "Grafana Cloud stack URL (e.g. https://<stack>.grafana.net)"
  type        = string
}

variable "grafana_sa_token" {
  description = "Grafana Cloud Service Account token with Editor role"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name used for folder and resource naming"
  type        = string
  default     = "freeradius-lab"
}

variable "prometheus_uid" {
  description = "UID of the Prometheus/Mimir data source in Grafana Cloud"
  type        = string
}

variable "loki_uid" {
  description = "UID of the Loki data source in Grafana Cloud"
  type        = string
}

variable "environment" {
  description = "Environment label (e.g. lab, staging, production)"
  type        = string
  default     = "lab"
}

variable "contact_email" {
  description = "Email address for alert notifications"
  type        = string
  default     = ""
}
