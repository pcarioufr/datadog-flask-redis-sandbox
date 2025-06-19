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

resource "datadog_synthetics_test" "browser_test_new_user_chat" {
  name    = "Chat for a New User"
  type    = "browser"
  status  = "live"
  message = "Browser test for new user chat flow failed. Notify: ${var.notif_email}"

  device_ids = ["firefox.tablet", "chrome.laptop_large"]
  locations  = ["${datadog_synthetics_private_location.local.id}"]

  request_definition {
    method = "GET"
    url    = "http://nginx/"
  }

  options_list {
    tick_every                     = 300
    min_failure_duration          = 0
    min_location_failed           = 1
    no_screenshot                 = false
    ignore_server_certificate_error = false
    disable_cors                  = false
    disable_csp                   = false
    
    retry {
      count    = 0
      interval = 300
    }
    
    monitor_options {
      renotify_interval = 120
    }
    
    rum_settings {
      is_enabled = false
    }
  }

  config_variable {
    name    = "USER_ID"
    type    = "text"
    secure  = false
    example = "3678-vXfL"
    pattern = "{{ numeric(4) }}-{{ alphabetic(4) }}"
  }

  # Step 1: Assert default prompt textarea is not empty
  browser_step {
    name                = "default prompt"
    type                = "assertElementContent"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      check = "notIsEmpty"
      value = ""
      element = jsonencode({
        multiLocator = {
          ro = "//*[@id=\"prompt-editor\"]"
        }
        targetOuterHTML = "<textarea id=\"prompt-editor\" rows=\"10\" placeholder=\"Enter your system prompt here, or leave it empty for no prompt\"></textarea>"
      })
    }
  }

  # Step 2: Click on mistral:latest model selection
  browser_step {
    name                = "Click on div \"mistral:latest\""
    type                = "click"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      element = jsonencode({
        multiLocator = {
          ro = "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')) = \"mistral:latest\"]]"
        }
        targetOuterHTML = "<div class=\"radio-option\" data-model=\"mistral:latest\">mistral:latest</div>"
      })
    }
  }

  # Step 3: Click save button
  browser_step {
    name                = "Click on svg"
    type                = "click"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      element = jsonencode({
        multiLocator = {
          ro = "//*[@id=\"save-prompt\"]/*"
        }
        targetOuterHTML = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" fill=\"currentColor\"><path d=\"M9.9997 15.1709L19.1921 5.97852L20.6063 7.39273L9.9997 17.9993L3.63574 11.6354L5.04996 10.2212L9.9997 ...\"/></svg>"
      })
    }
  }

  # Step 4: Wait for page processing
  browser_step {
    name                = "Wait"
    type                = "wait"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      value = 10
    }
  }

  # Step 5: Assert welcome message appears
  browser_step {
    name                = "welcome message"
    type                = "assertElementContent"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      check = "notIsEmpty"
      value = ""
      element = jsonencode({
        userLocator = {
          values = [
            {
              type = "css"
              value = ".message.assistant-message"
            }
          ]
          failTestOnCannotLocate = true
        }
        targetOuterHTML = "<div class=\"message assistant-message\" style=\"white-space: pre-wrap;\">🌟 Bonjour! Welcome to Idiom-matic, your personal guide through the colorful world of idioms in both French and English! I'm here ..."
      })
    }
  }

  # Step 6: Type message in chat input
  browser_step {
    name                = "Type text on textarea #chat-input"
    type                = "typeText"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      value = "Hello!"
      element = jsonencode({
        multiLocator = {
          ro = "//*[@id=\"chat-input\"]"
        }
        targetOuterHTML = "<textarea id=\"chat-input\" placeholder=\"Type your message here...\" rows=\"1\"></textarea>"
      })
    }
  }

  # Step 7: Click send button
  browser_step {
    name                = "Click on path"
    type                = "click"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      element = jsonencode({
        multiLocator = {
          ro = "//*[@id=\"send-button\"]/*/*"
        }
        targetOuterHTML = "<path d=\"M3 12.9999H9V10.9999H3V1.84558C3 1.56944 3.22386 1.34558 3.5 1.34558C3.58425 1.34558 3.66714 1.36687 3.74096 1.40747L22.2034 11.5618C22.4454 11.6949 22.5337 11.9989 22.4006 12.2409C22.3549 ...\"/>"
      })
    }
  }

  # Step 8: Wait for user message to appear
  browser_step {
    name                = "Wait for user message"
    type                = "wait"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      value = 1
    }
  }

  # Step 9: Assert user message appears correctly
  browser_step {
    name                = "user input"
    type                = "assertElementContent"
    allow_failure       = false
    is_critical         = true
    no_screenshot       = false
    
    params {
      check = "equals"
      value = "Hello!"
      element = jsonencode({
        userLocator = {
          values = [
            {
              type = "css"
              value = ".message.user-message"
            }
          ]
          failTestOnCannotLocate = true
        }
        targetOuterHTML = "<div class=\"message user-message\" style=\"white-space: pre-wrap;\">Hello!</div>"
      })
    }
  }

  tags = local.tags
}

resource "datadog_synthetics_private_location" "local" {
  name        = "LLM-2000 Private Location"
  description = "Private location for testing LLM-2000 API locally"
  tags        = local.tags
} 