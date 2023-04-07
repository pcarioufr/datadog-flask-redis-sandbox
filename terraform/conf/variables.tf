
variable "dd_api_key" {
  type    = string
  sensitive   = true
}

variable "dd_app_key" {
  type    = string
  sensitive   = true
}

variable "dd_site" {
  type    = string
}

variable "dd_env" {
  type    = string
}

variable "dd_tags" {
  type    = string
}
