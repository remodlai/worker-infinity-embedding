group "default" {
  targets = ["worker"]
}

target "worker" {
  dockerfile = "Dockerfile.unified"
  tags = ["ghcr.io/remodlai/worker-infinity-embedding:qwen3-0.6B-unified"]
  platforms = ["linux/amd64"]
  args = {
    BUILDKIT_INLINE_CACHE = "1"
  }
}