# Deploys a single task on ECS (without service)

# Check environment
if [[ -z ${CONTAINER_REPO} ]] || [[ -z ${TAG} ]] || [[ -z ${CLUSTER} ]] || [[ -z ${TASK_DEFINITION} ]] || [[ -z ${SECRETS} ]] || [[ -z ${APP} ]]; then
     echo "CONTAINER_REPO, TAG, CLUSTER, TASK_DEFINITION, SECRETS and APP must be set"
     exit 1
fi

if [[ ${ENVIRONMENT} = "staging" ]]; then
  CLUSTER=${STAGING_CLUSTER}
fi
[[ ${ENVIRONMENT} = 'staging' ]] && export CLUSTER=${STAGING_CLUSTER}
[[ ${ENVIRONMENT} = 'demo' ]] && export CLUSTER=${DEMO_CLUSTER}

[[ -z "${IMAGE_NAME}" ]] && export IMAGE_NAME=${CONTAINER_REPO}:${APP}-${TAG}

set -e

echo "==========================================="
echo "Registering new task definition revision..."

# Replace environment variables in the task definition file
touch task.json
awk '{while(match($0,"[$]{[^}]*}")) {var=substr($0,RSTART+2,RLENGTH -3);gsub("[$]{"var"}",ENVIRON[var])}}1' < docker-config/ecs-tasks/${TASK_DEFINITION}.json > task.json
aws ecs register-task-definition --cli-input-json file://task.json
rm task.json

echo "==========================================="
echo "Running task..."

OUTPUT=$(aws ecs run-task --cluster ${CLUSTER} --task-definition ${APP}-${TASK_DEFINITION} --count ${COUNT:-1})
echo "${OUTPUT}"

# The ecs cli returns with exit code 0 even on failure, so we need to explicitly check
SUCCESS=$(echo ${OUTPUT} | grep "\"failures\": \[\]")

if [[ ! -z "${SUCCESS}" ]]
then
    echo "Task successfully deployed!"
else
    exit 1
fi

set +e
