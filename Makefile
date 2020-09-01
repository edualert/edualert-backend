ENV_FILE := local.env

local-env:
	@cat $(ENV_FILE) 2>/dev/null | xargs

build:
	(export `$(MAKE) local-env` && sh docker-config/app/build.sh)

deploy-task:
	(export `$(MAKE) local-env` && sh scripts/deploy-task.sh ${EXTRA_ARGS})

deploy-app:
	(export `$(MAKE) local-env` ENVIRONMENT=dev TASK_DEFINITION=app && $(MAKE) deploy)

deploy-redis:
	(export `$(MAKE) local-env` ENVIRONMENT=dev TASK_DEFINITION=redis IMAGE_NAME=redis:6.0-rc1-alpine3.11 && $(MAKE) deploy)

deploy-collectstatic:
	(export `$(MAKE) local-env` ENVIRONMENT=dev TASK_DEFINITION=collectstatic && $(MAKE) deploy-task)

deploy-migrate:
	(export `$(MAKE) local-env` ENVIRONMENT=dev TASK_DEFINITION=migrate && $(MAKE) deploy-task)

deploy-postgres:
	(export `$(MAKE) local-env` ENVIRONMENT=dev TASK_DEFINITION=postgres IMAGE_NAME=postgres:12.1-alpine && $(MAKE) deploy)

deploy-app-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging TASK_DEFINITION=app && $(MAKE) deploy)

deploy-redis-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging  TASK_DEFINITION=redis IMAGE_NAME=redis:6.0-rc1-alpine3.11 && $(MAKE) deploy)

deploy-collectstatic-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging  TASK_DEFINITION=collectstatic && $(MAKE) deploy-task)

deploy-migrate-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging  TASK_DEFINITION=migrate && $(MAKE) deploy-task)

deploy-postgres-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging  TASK_DEFINITION=postgres IMAGE_NAME=postgres:12.1-alpine && $(MAKE) deploy)

deploy-app-demo:
	(export `$(MAKE) local-env` ENVIRONMENT=demo TASK_DEFINITION=app && $(MAKE) deploy)

deploy-redis-demo:
	(export `$(MAKE) local-env` ENVIRONMENT=demo  TASK_DEFINITION=redis IMAGE_NAME=redis:6.0-rc1-alpine3.11 && $(MAKE) deploy)

deploy-collectstatic-demo:
	(export `$(MAKE) local-env` ENVIRONMENT=demo  TASK_DEFINITION=collectstatic && $(MAKE) deploy-task)

deploy-migrate-demo:
	(export `$(MAKE) local-env` ENVIRONMENT=demo  TASK_DEFINITION=migrate && $(MAKE) deploy-task)

deploy-postgres-demo:
	(export `$(MAKE) local-env` ENVIRONMENT=demo  TASK_DEFINITION=postgres IMAGE_NAME=postgres:12.1-alpine && $(MAKE) deploy)

deploy:
	(export `$(MAKE) local-env` && sh scripts/deploy-service.sh ${EXTRA_ARGS})

# Set the SERVICES env var for this e.g. SERVICES=app-service make debug-service
debug-service:
	(export `$(MAKE) local-env` && aws ecs describe-services --cluster ${CLUSTER} --services $(SERVICES))
