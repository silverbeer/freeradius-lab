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

variable "prometheus_data_source_name" {
  description = "Name of the Prometheus/Mimir data source in Grafana Cloud (e.g. grafanacloud-<stack>-prom)"
  type        = string
  default     = "grafanacloud-freeradiuslab-prom"
}

variable "loki_data_source_name" {
  description = "Name of the Loki data source in Grafana Cloud (e.g. grafanacloud-<stack>-logs)"
  type        = string
  default     = "grafanacloud-freeradiuslab-logs"
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
