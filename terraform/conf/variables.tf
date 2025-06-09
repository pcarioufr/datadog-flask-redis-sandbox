variable "dd_api_key" {
  type = string
}

variable "dd_app_key" {
  type = string
}

variable "dd_site" {
  type = string
}

variable "dd_env" {
  type = string
}

variable "dd_tags" {
  type = string
}

variable "notif_email" {
  type = string
}

variable "location" {
  type        = string
  description = "ID of the private location to use for synthetics tests"
  default     = "us-east-1"
}

locals {
  # Process tags: split on comma, trim whitespace, and remove any quotes
  tags = distinct(concat(
    [for tag in split(",", var.dd_tags) : replace(trimspace(tag), "\"", "")],
    ["env:${var.dd_env}"]
  ))
}
