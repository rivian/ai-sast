variable "name" {
    type = string
}

variable "security_groups" {
    type = list
}

variable "subnets" {
    type = list(string)
}

variable "idle_timeout" {
    type = number
}