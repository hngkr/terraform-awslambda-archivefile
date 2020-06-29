output "path" {
  value = data.external.payload_sha.result["path"]
}

output "filename" {
  value = data.external.payload_sha.result["filename"]
}

output "sha256" {
  value = data.external.payload_sha.result["sha256"]
}

output "md5" {
  value = data.external.payload_sha.result["md5"]
}
