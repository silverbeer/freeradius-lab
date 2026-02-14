output "folder_uid" {
  description = "UID of the FreeRADIUS Lab folder in Grafana"
  value       = grafana_folder.freeradius.uid
}

output "dashboard_urls" {
  description = "URLs for the Grafana dashboards"
  value = {
    freeradius_overview = "${var.grafana_url}/d/${grafana_dashboard.freeradius_overview.uid}"
    host_metrics        = "${var.grafana_url}/d/${grafana_dashboard.host_metrics.uid}"
    logs_explorer       = "${var.grafana_url}/d/${grafana_dashboard.logs_explorer.uid}"
  }
}

output "alert_rule_groups" {
  description = "Names of the alert rule groups"
  value = [
    grafana_rule_group.freeradius_metric_alerts.name,
    grafana_rule_group.freeradius_log_alerts.name,
    grafana_rule_group.freeradius_host_alerts.name,
  ]
}
