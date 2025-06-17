resource "datadog_synthetics_test" "api_test" {
  name    = "Test LLM-2000 API"
  type    = "api"
  subtype = "http"
  status  = "live"
  message = "The LLM-2000 API test failed. Notify: ${var.notif_email}"

  request_definition {
    method = "POST"
    url    = "http://nginx:80/api/chat"
    body   = jsonencode({
      message = "What is your favorite color?",
      prompt  = "You must respond to all questions with text in CAPITAL LETTERS only.",
      model   = "mistral:latest"
    })
    timeout = 30
  }

  request_headers = {
    "Content-Type" = "application/json"
  }

  assertion {
    type     = "statusCode"
    operator = "is"
    target   = "200"
  }

  assertion {
    type     = "responseTime"
    operator = "lessThan"
    target   = 15000
  }

  locations = ["${datadog_synthetics_private_location.local.id}"]
  
  options_list {
    tick_every = 300  # Run every 5 minutes
    retry {
      count    = 2
      interval = 300
    }
    monitor_options {
      renotify_interval = 120
    }
  }

  # Use the local variable for tags
  tags = local.tags
}

resource "datadog_synthetics_private_location" "local" {
  name        = "LLM-2000 Private Location"
  description = "Private location for testing LLM-2000 API locally"
  tags        = local.tags
} 