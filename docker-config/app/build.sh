if [[ -z ${CONTAINER_REPO} ]] || [[ -z ${TAG} ]]; then
    echo "CONTAINER_REPO and TAG environment variables must be set"
    exit 1
fi

set -euo pipefail
echo "Build started"

docker pull "${CONTAINER_REPO}":edualert-api-latest || true
docker build --file docker-config/app/Dockerfile \
            --cache-from "${CONTAINER_REPO}":edualert-api-latest \
            --tag "${CONTAINER_REPO}":edualert-api-latest \
            --tag "${CONTAINER_REPO}":edualert-api-"${TAG}" .

docker push "${CONTAINER_REPO}":edualert-api-latest
docker push "${CONTAINER_REPO}":edualert-api-"${TAG}"
