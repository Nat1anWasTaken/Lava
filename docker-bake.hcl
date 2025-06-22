group "default" {
  targets = ["main"]
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
  platforms = ["linux/amd64", "linux/arm64/v8", "linux/arm/v7"]
  dockerfile = "./Dockerfile"
  tags = getTag("latest")
}