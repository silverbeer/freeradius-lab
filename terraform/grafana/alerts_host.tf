resource "grafana_rule_group" "freeradius_host_alerts" {
  org_id           = 1
  name             = "FreeRADIUS Host Alerts"
  folder_uid       = grafana_folder.freeradius.uid
  interval_seconds = 60

  rule {
    name      = "High CPU"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.prometheus_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "host_cpu_usage_idle"
        refId   = "A"
        instant = true
      })
    }

    data {
      ref_id         = "B"
      datasource_uid = "-100"

      relative_time_range {
        from = 0
        to   = 0
      }

      model = jsonencode({
        type       = "threshold"
        expression = "A"
        refId      = "B"
        conditions = [
          {
            evaluator = {
              type   = "lt"
              params = [10]
            }
          }
        ]
      })
    }

    for            = "5m"
    no_data_state  = "NoData"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "warning"
    }

    annotations = {
      summary     = "High CPU usage on FreeRADIUS host"
      description = "CPU idle percentage is below 10% (current: {{ $values.A }}%). The server may be overloaded."
    }
  }

  rule {
    name      = "Disk Space Low"
    condition = "C"

    data {
      ref_id         = "A"
      datasource_uid = var.prometheus_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "host_filesystem_free_bytes{mountpoint=\"/\"}"
        refId   = "A"
        instant = true
      })
    }

    data {
      ref_id         = "B"
      datasource_uid = var.prometheus_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "host_filesystem_total_bytes{mountpoint=\"/\"}"
        refId   = "B"
        instant = true
      })
    }

    data {
      ref_id         = "C"
      datasource_uid = "-100"

      relative_time_range {
        from = 0
        to   = 0
      }

      model = jsonencode({
        type       = "math"
        expression = "$A / $B < 0.1"
        refId      = "C"
      })
    }

    for            = "5m"
    no_data_state  = "NoData"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "critical"
    }

    annotations = {
      summary     = "Disk space critically low on root filesystem"
      description = "Less than 10% disk space remaining on /. Logs and data may fail to write."
    }
  }
}
