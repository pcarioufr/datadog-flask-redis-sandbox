resource "datadog_monitor" "low_hits" {
  name               = "Low number of hits"
  type               = "metric alert"
  message            = "Less than 10 hits in the last 5 minutes."
  query = "sum(last_5m):sum:trace.flask.request.hits{env:test,service:flask,resource_name:post_/count/_user_id}.as_count() < 10"
  monitor_thresholds {
    critical = 10
  }
  # on_missing_data = "show_and_notify_no_data"
  require_full_window = false

  tags = local.tags
  priority = 5
}

resource "datadog_monitor" "high_latency" {
  name               = "High latency ⬅️"
  type               = "metric alert"
  message            = "High latency in the last 5 minutes. ⬅️"
  query = "max(last_5m):max:trace.flask.request{env:test,service:flask} > 1.8"
  monitor_thresholds {
    warning  = 1.5
    critical = 1.8
  }

  require_full_window = false
  tags = local.tags
  priority = 5
}

resource "datadog_monitor" "endpoint_composite" {
  name               = "High latency && high number of hits"
  type               = "composite"
  message            = "Endpoint in bad shape. Notify: @${var.notif_email}"
  query = "!${datadog_monitor.low_hits.id} && ${datadog_monitor.high_latency.id}"
  tags = local.tags

  priority = 1
}
