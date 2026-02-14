resource "grafana_dashboard" "freeradius_overview" {
  folder = grafana_folder.freeradius.id

  config_json = templatefile("${path.module}/../../dashboards/freeradius-overview.json", {
    prometheus_uid = data.grafana_data_source.prometheus.uid
    loki_uid       = data.grafana_data_source.loki.uid
  })
}

resource "grafana_dashboard" "host_metrics" {
  folder = grafana_folder.freeradius.id

  config_json = templatefile("${path.module}/../../dashboards/host-metrics.json", {
    prometheus_uid = data.grafana_data_source.prometheus.uid
    loki_uid       = data.grafana_data_source.loki.uid
  })
}

resource "grafana_dashboard" "logs_explorer" {
  folder = grafana_folder.freeradius.id

  config_json = templatefile("${path.module}/../../dashboards/logs-explorer.json", {
    prometheus_uid = data.grafana_data_source.prometheus.uid
    loki_uid       = data.grafana_data_source.loki.uid
  })
}
