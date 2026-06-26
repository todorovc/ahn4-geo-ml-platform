variable "project_name" {
  type    = string
  default = "ahn4-geo-ml-platform"
}

variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}

variable "data_bucket_name" {
  type    = string
  default = "geo-ml-ahn"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.42.0.0/24", "10.42.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.42.10.0/24", "10.42.11.0/24"]
}
