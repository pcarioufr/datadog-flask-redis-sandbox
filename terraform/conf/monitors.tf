locals {
  # monitor_tags = [split(" ", var.dd_tags), "env:${var.dd_env}", "owner:terraform"]
  monitor_tags = ["env:${var.dd_env}", "owner:terraform"]
}


resource "datadog_monitor" "foo1" {
  name               = "Name for monitor foo1"
  type               = "metric alert"
  message            = "Monitor triggered. Notify: @hipchat-channel"
  query = "avg(last_1h):avg:system.cpu.idle{*} by {host} > 98"
  monitor_thresholds {
    warning  = 95
    critical = 98
  }
  tags = local.monitor_tags
}

resource "datadog_monitor" "foo2" {
  name               = "Name for monitor foo2"
  type               = "metric alert"
  message            = "Monitor triggered. Notify: @hipchat-channel"
  query = "avg(last_1h):avg:system.cpu.idle{*} by {host} > 98"
  monitor_thresholds {
    warning  = 95
    critical = 98
  }
  tags = local.monitor_tags
}

resource "datadog_monitor" "foocomposite" {
  name               = "Name for composite monitor foo1 && foo2"
  type               = "composite"
  message            = "Composite Monitor triggered. Notify: @hipchat-channel"
  query = "${datadog_monitor.foo1.id} && ${datadog_monitor.foo2.id}"
  tags = local.monitor_tags
}
