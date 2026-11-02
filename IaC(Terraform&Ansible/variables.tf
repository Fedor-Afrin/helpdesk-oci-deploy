variable "tenancy_ocid" { type = string }
variable "user_ocid" { type = string }
variable "fingerprint" { type = string }
variable "private_key_path" { type = string }
variable "region" { type = string }

variable "compartment_ocid" {
  type        = string
  description = "OCID компартмента"
}

variable "ssh_public_key" { type = string }

variable "vcn_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "api_subnet_cidr" {
  type    = string
  default = "10.0.0.0/28"
}

variable "nodes_subnet_cidr" {
  type    = string
  default = "10.0.10.0/24"
}

variable "oke_cluster_name" {
  type    = string
  default = "devops-final-cluster"
}

variable "k8s_version" {
  type    = string
  default = "v1.31.1"
}
