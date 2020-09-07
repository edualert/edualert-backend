ENV_FILE := local.env

local-env:
	@cat $(ENV_FILE) 2>/dev/null | xargs

build:
	(export `$(MAKE) local-env` && sh docker-config/app/build.sh)

deploy-task:
	(export `$(MAKE) local-env` && sh scripts/deploy-task.sh ${EXTRA_ARGS})

deploy-app:
	(export `$(MAKE) local-env` ENVIRONMENT=production TASK_DEFINITION=app && $(MAKE) deploy)

deploy-redis:
	(export `$(MAKE) local-env` ENVIRONMENT=production TASK_DEFINITION=redis IMAGE_NAME=redis:6.0-rc1-alpine3.11 && $(MAKE) deploy)

deploy-collectstatic:
	(export `$(MAKE) local-env` ENVIRONMENT=production TASK_DEFINITION=collectstatic && $(MAKE) deploy-task)

deploy-app-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging TASK_DEFINITION=app && $(MAKE) deploy)

deploy-redis-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging  TASK_DEFINITION=redis IMAGE_NAME=redis:6.0-rc1-alpine3.11 && $(MAKE) deploy)

deploy-collectstatic-staging:
	(export `$(MAKE) local-env` ENVIRONMENT=staging  TASK_DEFINITION=collectstatic && $(MAKE) deploy-task)

deploy:
	(export `$(MAKE) local-env` && sh scripts/deploy-service.sh ${EXTRA_ARGS})

# Set the SERVICES env var for this e.g. SERVICES=app-service make debug-service
debug-service:
	(export `$(MAKE) local-env` && aws ecs describe-services --cluster ${CLUSTER} --services $(SERVICES))
