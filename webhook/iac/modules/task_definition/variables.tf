variable "family" {
    type = string
}

variable "requires_compatibilities" {
    type = list
}

variable "network_mode" {
    type = string
}

variable "cpu" {
    type = number
}

variable "memory" {
    type = number
}

variable "execution_role_arn" {
    type = any
}

variable "task_role_arn" {
    type = any
}

variable "container_definitions" {
    type = any
}