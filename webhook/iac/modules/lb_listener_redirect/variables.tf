variable "lb_arn" {
    type = any
}

variable "port" {
    type = number
}

variable "protocol" {
    type = string
}

variable "redirect" {
    type = any
    description = "Configuration for redirecting at the listener"
}