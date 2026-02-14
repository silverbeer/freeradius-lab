resource "grafana_rule_group" "freeradius_log_alerts" {
  name             = "FreeRADIUS Log Alerts"
  folder_uid       = grafana_folder.freeradius.uid
  interval_seconds = 60

  rule {
    name      = "Auth Failure Spike"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.loki_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "sum(count_over_time({source=\"linelog\"} | json | result=\"reject\" [5m]))"
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
              type   = "gt"
              params = [10]
            }
          }
        ]
      })
    }

    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "warning"
    }

    annotations = {
      summary     = "Auth failure spike detected"
      description = "More than 10 authentication rejections in the last 5 minutes (count: {{ $values.A }})."
    }
  }

  rule {
    name      = "Unknown NAS Client"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.loki_uid

      relative_time_range {
        from = 60
        to   = 0
      }

      model = jsonencode({
        expr    = "count_over_time({source=\"radius_log\"} |= \"unknown client\" [1m])"
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
              type   = "gt"
              params = [0]
            }
          }
        ]
      })
    }

    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "critical"
    }

    annotations = {
      summary     = "Unknown NAS client detected"
      description = "A RADIUS request was received from an unknown NAS client. This may indicate a misconfigured client or unauthorized access attempt."
    }
  }

  rule {
    name      = "Config Reload Failure"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.loki_uid

      relative_time_range {
        from = 60
        to   = 0
      }

      model = jsonencode({
        expr    = "count_over_time({source=\"journald\"} |= \"Failed to reload\" |= \"radiusd\" [1m])"
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
              type   = "gt"
              params = [0]
            }
          }
        ]
      })
    }

    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "critical"
    }

    annotations = {
      summary     = "FreeRADIUS config reload failed"
      description = "A configuration reload attempt for radiusd has failed. The server may be running with stale configuration."
    }
  }

  rule {
    name      = "Module Error"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.loki_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "count_over_time({source=\"radius_log\"} |~ \"Error|ERROR\" |~ \"rlm_\" [5m])"
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
              type   = "gt"
              params = [0]
            }
          }
        ]
      })
    }

    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "warning"
    }

    annotations = {
      summary     = "FreeRADIUS module error detected"
      description = "An error was logged by a FreeRADIUS module (rlm_*). Check radius.log for details."
    }
  }

  rule {
    name      = "Duplicate Request Spike"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.loki_uid

      relative_time_range {
        from = 60
        to   = 0
      }

      model = jsonencode({
        expr    = "sum(count_over_time({source=\"radius_log\"} |= \"Dropping duplicate request\" [1m]))"
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
              type   = "gt"
              params = [5]
            }
          }
        ]
      })
    }

    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "warning"
    }

    annotations = {
      summary     = "Duplicate request spike detected"
      description = "More than 5 duplicate RADIUS requests dropped in the last minute (count: {{ $values.A }}). NAS clients may be retransmitting too aggressively."
    }
  }

  rule {
    name      = "Vector Pipeline Error"
    condition = "B"

    data {
      ref_id         = "A"
      datasource_uid = var.loki_uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr    = "count_over_time({source=\"journald\", unit=\"vector\"} |= \"error\" [5m])"
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
              type   = "gt"
              params = [0]
            }
          }
        ]
      })
    }

    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false
    notification_settings {
      contact_point = "grafana-default-email"
    }

    labels = {
      severity = "warning"
    }

    annotations = {
      summary     = "Vector pipeline error detected"
      description = "The Vector observability agent has logged errors. Metrics or logs may not be shipping to Grafana Cloud."
    }
  }
}
