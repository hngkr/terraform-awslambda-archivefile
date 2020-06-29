# Sha the requirements file. This determines whether or not we need to
# rebuild the virtualenv (which will trigger whether or not we need to rebuild)
# the payload

locals {
  requirements_file = var.requirements_file != "" ? var.requirements_file : "null"
  lib_path = var.lib_path != "" ? var.lib_path : "null"
}

data "external" "needs_rebuild" {
  program = ["python3", "${path.module}/scripts/needs_rebuild.py"]

  query = {
    name              = var.name
    output_path       = var.output_path
    project_path      = var.project_path
    requirements_file = local.requirements_file
    runtime           = var.runtime
    lib_path          = local.lib_path
  }

  # returns 3 results: sha, isodate, output_filepath
}

resource "null_resource" "build" {
  triggers = {
    needs_rebuild = data.external.needs_rebuild.result["sha"]
    output_filepath = data.external.needs_rebuild.result["output_filepath"]
  }

  provisioner "local-exec" {
    interpreter = ["python3"]
    command = "${path.module}/scripts/build.py"

    environment = {
      OUTPUT_FILEPATH   = data.external.needs_rebuild.result["output_filepath"]
      PROJECT_PATH      = var.project_path
      REQUIREMENTS_FILE = local.requirements_file
      LIB_PATH          = local.lib_path
      RUNTIME           = var.runtime
    }
  }
}

data "external" "payload_sha" {
  program = ["python3", "${path.module}/scripts/calculate_hash.py"]

  query = {
    file_path   = data.external.needs_rebuild.result["output_filepath"]
    id          = null_resource.build.id
  }
}
