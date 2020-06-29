variable "name" {
  description = "Name of the function payload thing"
}

variable "project_path" {
  description = "Source code path"
}

variable "output_path" {
  description = "Where to write the payload zip"
}

# Optional settings

variable "runtime" {
  default     = "python3.8"
  description = "Python runtime. defaults to python3.8"
}

variable "requirements_file" {
  default     = ""
  description = "The path to the requirements file. Can be empty."
}

variable "lib_path" {
  default     = ""
  description = "Path to common python files directory"
}
