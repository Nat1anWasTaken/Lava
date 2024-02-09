group "default" {
  targets = ["main", "amd64", "arm64", "armv7"]
}

function "getTag" {
  params = [
    tagName
  ]
  result = flatten([
    "ghcr.io/nat1anwastaken/lava:${tagName}"
  ])
}

target "main" {
  platforms = ["linux/amd64", "linux/arm64", "linux/arm/v7"]
  dockerfile = "./Dockerfile"
  tags = getTag("latest")
}

target "amd64" {
  inherits = ["main"]
  platforms = ["linux/amd64"]
  tags = getTag("amd64")
}

target "arm64" {
  inherits = ["main"]
  platforms = ["linux/arm64"]
  tags = getTag("arm64")
}

target "armv7" {
  inherits = ["main"]
  platforms = ["linux/armv7"]
  tags = getTag("armv7")
}
