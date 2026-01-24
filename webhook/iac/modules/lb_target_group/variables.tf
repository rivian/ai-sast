variable "name" {
    type = string
}

variable "port" {
    type = number
}

variable "protocol" {
    type = string
}

variable "vpc_id" {
    type = string
}

variable "type" {
    type = string
}

variable "health_check" {
    type = any
    description = "Health Check configuration for Load Balancer Target Group"
}