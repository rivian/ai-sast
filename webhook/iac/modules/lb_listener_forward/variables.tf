variable "lb_arn" {
    type = any
}

variable "port" {
    type = number
}

variable "protocol" {
    type = string
}

variable "certificate_arn" {
    type = any
}

variable "target_group_arn" {
    type = any
}