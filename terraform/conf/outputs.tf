output "tags" {
  value = local.tags
}

output "private_location_access_key" {
  description = "The access key for the private location"
  value       = jsondecode(datadog_synthetics_private_location.local.config).accessKey
  sensitive   = true
}

output "private_location_secret_access_key" {
  description = "The secret access key for the private location"
  value       = jsondecode(datadog_synthetics_private_location.local.config).secretAccessKey
  sensitive   = true
}

output "private_location_private_key" {
  description = "The private key for the private location"
  value       = jsondecode(datadog_synthetics_private_location.local.config).privateKey
  sensitive   = true
}

output "private_location_public_key_pem" {
  description = "The public key PEM for the private location"
  value       = jsondecode(datadog_synthetics_private_location.local.config).publicKey.pem
  sensitive   = true
}

output "private_location_public_key_fingerprint" {
  description = "The public key fingerprint for the private location"
  value       = jsondecode(datadog_synthetics_private_location.local.config).publicKey.fingerprint
  sensitive   = true
}

output "private_location_site" {
  description = "The Datadog site for the private location"
  value       = jsondecode(datadog_synthetics_private_location.local.config).site
  sensitive   = true
}

output "rum_application_id" {
  description = "The ID of the RUM application"
  value       = datadog_rum_application.llm_2000.id
  sensitive   = true
}

output "rum_client_token" {
  description = "The client token for RUM"
  value       = datadog_rum_application.llm_2000.client_token
  sensitive   = true
}
