resource "grafana_rule_group" "freeradius_metric_alerts" {
  org_id           = 1
  name             = "FreeRADIUS Metric Alerts"
  folder_uid       = grafana_folder.freeradius.uid
  interval_seconds = 60

  rule {
    name      = "Auth Success Rate Low"
    condition = "C"

    data {
      ref_id         = "A"
      datasource_uid = var.prometheus_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "sum(rate(freeradius_radius_auth_total{result=\"reject\"}[5m]))"
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
        expr    = "sum(rate(freeradius_radius_auth_total[5m]))"
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
        expression = "1 - ($A / $B) < 0.8"
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
      severity = "warning"
    }

    annotations = {
      summary     = "Auth success rate has dropped below 80%"
      description = "The RADIUS authentication success rate is {{ $values.C }}, which is below the 80% threshold."
    }
  }

  rule {
    name      = "FreeRADIUS Down"
    condition = "A"

    data {
      ref_id         = "A"
      datasource_uid = var.prometheus_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "absent(freeradius_status_access_requests_total)"
        refId   = "A"
        instant = true
      })
    }

    for            = "2m"
    no_data_state  = "Alerting"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "critical"
    }

    annotations = {
      summary     = "FreeRADIUS server is down"
      description = "No status-server metrics have been received. The FreeRADIUS process may be stopped or unreachable."
    }
  }

  rule {
    name      = "Request Rate Zero"
    condition = "A"

    data {
      ref_id         = "A"
      datasource_uid = var.prometheus_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "sum(rate(freeradius_radius_auth_total[5m])) == 0"
        refId   = "A"
        instant = true
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
      summary     = "RADIUS request rate is zero"
      description = "No authentication requests have been received in the last 5 minutes. The server may be unreachable or no clients are sending traffic."
    }
  }
}
