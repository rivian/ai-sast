variable "security_group_id" {
    type = any
}

variable "from_port" {
    type = number
    default = 79
}

variable "ip_protocol" {
    type = string
}

variable "to_port" {
    type = number
    default = 444
}

variable "cidr_ipv4" {
    type = string
}