# ==================================================================================================
# Creates or updates a ECS service on a given cluster with a new task definition.
# Unless instructed otherwise, will wait for the new task to reach a RUNNING state,
# and will try to revert to the latest task in the event of failures.
# This assumes the AWS CLI is setup correctly (right user, profile, region, etc.)
# ==================================================================================================

# Optional settings:
# ==================================================================================================
# A path to the folder containing the ecs task
TASK_PATH="${TASK_PATH:-docker-config/ecs-tasks/}"
# The number of times to poll for the newly created task before declaring the deploy failed
MAX_RETRIES="${MAX_RETRIES:-60}"
# Will print additional output
DEBUG_DEPLOY="${DEBUG_DEPLOY:-false}"
# Will not try to revert to the latest task in case of failures
NO_REVERT="${NO_REVERT:-false}"
# The full name of the image to deploy
[[ -z "${IMAGE_NAME}" ]] && IMAGE_NAME=${CONTAINER_REPO}:${APP}-${TAG}
export IMAGE_NAME

# Required settings
# =================================================================================================
# APP: the name of the app this service belongs to
# CLUSTER: the cluster where the task will run
# TASK_DEFINITION: The name of the image that will be deployed. Must correspond to the task's family
# CONTAINER_REPO: the repo containing the task's docker image
# TAG: the image's tag
# SECRETS: the ARN of the AWS Secret Manager secrets the task will use
# ENVIRONMENT: name of the deployment environment: dev, local, staging etc.
# ACCOUNT_ID: the ID of the user's account

set -euo pipefail

for variable in APP ACCOUNT_ID CONTAINER_REPO TAG CLUSTER TASK_DEFINITION DOCKER_CREDENTIALS SECRETS ENVIRONMENT; do
  eval echo >/dev/null "$"${variable}
done

[[ ${ENVIRONMENT} = 'staging' ]] && export CLUSTER=${STAGING_CLUSTER}
[[ ${ENVIRONMENT} = 'demo' ]] && export CLUSTER=${DEMO_CLUSTER}

# Globals:
# ==================================================================================================
# The name of the service to update / create
SERVICE_NAME="${TASK_DEFINITION}-service"
# Will hold the task definition of the task currently running before the deploy. Will be used for reverting
PREVIOUS_TASK_DEFINITION=""
# The task definition of the newly registered task
NEW_TASK_DEFINITION=""

print_error() {
  # Prints all arguments to stderr
  for arg; do
    2>&1 echo ${arg}
  done
}

debug_enabled() {
  [[ "${DEBUG_DEPLOY}" = true ]] && return 0
}

get_task_definition_from_cli_response() {
  # Parses the AWS CLI Json Response given as parameter and returns the first task arn found
  task_arn=$1
  echo "${task_arn}" | sed -n 's/^.*task-definition\/\(.*\)".*$/\1/p' | head -n1
}


run_task_and_check_errors() {
  # Runs a task with the PREVIOUS_TASK_DEFINITION
  output=$(aws ecs run-task --cluster "${CLUSTER}" --task-definition "${PREVIOUS_TASK_DEFINITION}" --count 1)

  # The run-task command sometimes returns exit code 0 even when it failed, so we need to check for the "failures" key
  echo "${output}" | grep -q '"failures": \[\]' || (echo "${output}" && return 1)

  debug_enabled && print_error "${output}"
}

register_new_task_definition() {
  echo "==========================================="
  echo "Registering new task definition revision..."

  # This makes sure there are no leftovers files in the event of exit, errors, or cancelling
  trap "rm -f task.json >/dev/null 2>&1; exit" INT TERM EXIT

  # Replace environment variables in the task definition file
  touch task.json
  awk '{while(match($0,"[$]{[^}]*}")) {var=substr($0,RSTART+2,RLENGTH -3);gsub("[$]{"var"}",ENVIRON[var])}}1' < "${TASK_PATH}""${TASK_DEFINITION}".json > task.json
  cat task.json

  # Register the task definition
  register_task_response=$(aws ecs register-task-definition --cli-input-json file://task.json)
  debug_enabled && echo "${register_task_response}"

  NEW_TASK_DEFINITION=$(get_task_definition_from_cli_response "${register_task_response}")

  echo "${NEW_TASK_DEFINITION} registered successfully!"
  # Remove the trap and cleanup
  trap - INT TERM EXIT
  rm -f task.json >/dev/null 2>&1
}

stop_current_task() {
  # Stops the task with the same task family currently running in the cluster
  # Populates PREVIOUS_TASK_DEFINITION with its definition
  echo && echo "Killing any currently running tasks..."
  current_tasks=$(aws ecs list-tasks --cluster "${CLUSTER}" --family "${APP}-${TASK_DEFINITION}")

  debug_enabled && echo "Current tasks:" && echo "${current_tasks}"

  set +o pipefail
  current_task_id=$(echo "${current_tasks}" \
      | grep -s -E "task/" \
      | tr "/" " " \
      | tr "[" " " \
      | tr -d '"' \
      | awk '{print $3}')
  set -o pipefail

  debug_enabled && echo "Extracted ARNs: " && echo "${current_task_id}"

  if [[ -n "${current_task_id}" ]]
  then
      stop_task_response="$(aws ecs stop-task --cluster "${CLUSTER}" --task "${current_task_id}")"
      debug_enabled && echo "Stopping task: " && echo "${stop_task_response}"
      PREVIOUS_TASK_DEFINITION=$(get_task_definition_from_cli_response "${stop_task_response}")
      echo "${PREVIOUS_TASK_DEFINITION} killed successfully." && echo
  else
      echo "No tasks to kill" && echo
  fi
}

revert_to_last_task() {
  # Deploys a task with the PREVIOUS_TASK_DEFINITION
  [[ ${NO_REVERT} = true ]] && return 0

  echo && echo "Reverting to the previously running task"

  if [[ -n "${PREVIOUS_TASK_DEFINITION}" ]]; then
    print_error "Error creating service!!!  Reverting to the last working task: ${PREVIOUS_TASK_DEFINITION}"

    if run_task_and_check_errors; then
      print_error "Task ${PREVIOUS_TASK_DEFINITION} reverted succesfully, but service was still not updated deployed."
    else
      print_error "Error reverting task!!!"
    fi
    exit 1
  else
    echo "No task to revert to. Exiting"
  fi

}


wait_for_task_to_reach_state() {
  # Polls aws until the the task reach the state $1, meaning the pattern $2
  # is found in the describe-task response, or until MAX_TRIES is reached. If
  # the task didn't properly start revert to the previous one.
  echo && echo "Waiting for task to become $1"

  counter=0
  task_running=false
  list_tasks_response="$(aws ecs list-tasks --cluster "${CLUSTER}" --service-name "${SERVICE_NAME}")"
  debug_enabled && echo "Current tasks:" && echo "${list_tasks_response}"

  while [[ ${task_running} = false ]];
  do
    [[ ${counter} -eq $MAX_RETRIES ]] \
      && print_error "Task failed to become $1 in the required time. Check ecs logs." \
      && revert_to_last_task && \
      exit 1

    echo "${counter}/${MAX_RETRIES} Retrying..."

    # Get the task arn from the list-tasks response
    task_arn="$(echo "${list_tasks_response}" | grep -Eo "(arn.*)\"")" || true

    if [[ -n "${task_arn}" ]]; then
      # The only way to get the task status is by calling describe-tasks
      task_info="$(aws ecs describe-tasks --cluster "${CLUSTER}" --tasks "$(echo "${task_arn}" | rev | cut -c2- | rev)")"
      debug_enabled && echo "Task status:" && echo "${task_info}"

      # We-re looking for a RUNNING task matching the previously deployed task's revision
      if echo "${task_info}" | grep -q "$2" \
        && echo "${task_info}" | grep -q "${NEW_TASK_DEFINITION}"
      then
        task_running=true
      fi

      # If the task somehow becomes STOPPED, throw an error and exit
      if echo "${task_info}" | grep -q "\"lastStatus\": \"STOPPED\""; then
        print_error "Task became STOPPED. Possible reason:" "${task_info}" "Exiting" && exit 1
      fi
    fi

    # Try again
    [[ ${task_running} = false ]] \
      && list_tasks_response="$(aws ecs list-tasks --cluster "${CLUSTER}" --service-name "${SERVICE_NAME}")" \
      && debug_enabled && echo "Current tasks:" \
      && echo "${list_tasks_response}"

    counter=$((counter+1))
  done

  echo "Success, task is now $1!!"
}

main() {
  set -euo pipefail

  register_new_task_definition

  echo "==========================================="
  # Deploy
  # Check to see if there already is an active service running on this cluster
  services="$(aws ecs describe-services --cluster "${CLUSTER}" --services "${SERVICE_NAME}")"
  debug_enabled && echo "Current services:" && echo "${services}" && echo

  if [[ -n "${services}" ]] && (set +o pipefail && echo "${services}" | grep -q "\"status\": \"ACTIVE\""); then
    echo "Previous service found. Updating and deploying..."

    # Stop the current task. Normally the ECS service would take care of this,
    # but we need to do it because a "dangling" task may have already been deployed outside the service
    stop_current_task

    echo "Updating service..."
    aws ecs update-service --cluster "${CLUSTER}" \
                          --service "${SERVICE_NAME}" \
                          --task-definition "${NEW_TASK_DEFINITION}" \
                          --force-new-deployment
    if [[ $? -eq 0 ]]; then
      echo && echo "Service updated successfully!"
    else
      revert_to_last_task || echo && echo "Service updating failed. Exiting" && exit 1
    fi

  else
    echo "No active service found. Creating a new one..."
    # Stop the current task, which doesn't belong to any service
    stop_current_task

    echo "Creating service..."
    aws ecs create-service --task-definition "${NEW_TASK_DEFINITION}" \
                        --service-name "${SERVICE_NAME}" \
                        --cluster "${CLUSTER}" \
                        --launch-type "EC2" \
                        --deployment-configuration "minimumHealthyPercent=0,maximumPercent=100" \
                        --scheduling-strategy "DAEMON" \
                        --deployment-controller "type=ECS"
    if [[ $? -eq 0 ]]; then
      echo && echo "Service created successfully!"
    else
      revert_to_last_task || echo && echo "Service creation failed. Exiting" && exit 1
    fi
  fi

  wait_for_task_to_reach_state "PENDING" "\"lastStatus\": \"PENDING\""
  # There's no point in reverting here since the task may become running at a later time.
  NO_REVERT=true wait_for_task_to_reach_state "RUNNING" "\"lastStatus\": \"RUNNING\""
}

main
