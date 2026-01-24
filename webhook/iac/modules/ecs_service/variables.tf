variable "name" {
    type = string
}

variable "cluster" {
    type = any
}

variable "task_definition" {
    type = any
}

variable "desired_count" {
    type = number
}

variable "deployment_minimum_healthy_percent" {
    type = number
}

variable "deployment_maximum_percent" {
    type = number
}

variable "health_check_grace_period_seconds" {
    type = number
}

variable "launch_type" {
    type = string
}

variable "network_configuration" {
    type = any
}

variable "load_balancer" {
    type = any
}