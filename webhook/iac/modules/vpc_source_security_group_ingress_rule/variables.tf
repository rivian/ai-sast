variable "security_group_id" {
    type = any
}

variable "from_port" {
    type = number
    default = 80
}

variable "ip_protocol" {
    type = string
}

variable "to_port" {
    type = number
    default = 80
}

variable "referenced_security_group_id" {
    type = any
}