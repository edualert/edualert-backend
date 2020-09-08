if [[ -z ${CONTAINER_REPO} ]] || [[ -z ${TAG} ]]; then
    echo "CONTAINER_REPO and TAG environment variables must be set"
    exit 1
fi

aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin ${CONTAINER_REPO}

set -euo pipefail
echo "Build started"

docker pull "${CONTAINER_REPO}":${APP}-latest || true
docker build --file docker-config/app/Dockerfile \
            --cache-from "${CONTAINER_REPO}":${APP}-latest \
            --tag "${CONTAINER_REPO}":${APP}-latest \
            --tag "${CONTAINER_REPO}":${APP}-"${TAG}" .

docker push "${CONTAINER_REPO}":${APP}-latest
docker push "${CONTAINER_REPO}":${APP}-"${TAG}"
