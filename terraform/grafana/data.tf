data "grafana_data_source" "prometheus" {
  name = var.prometheus_data_source_name
}

data "grafana_data_source" "loki" {
  name = var.loki_data_source_name
}
