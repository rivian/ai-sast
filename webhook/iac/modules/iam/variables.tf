variable "effect" {
    type = string
    default = "Allow"

    validation {
        condition = contains(["Allow", "Deny"], var.effect)
        error_message = "Valid values for iam_policy_doc_effect are (Allow, Deny)"
    }
}

variable "actions" {
    type = list(string)
}

variable "principals" {
    type = any
}

variable "name" {
    type = string
}

variable "policy_arns" {
    type = set(string)
}