PY_DIRS := api cat5 processor tests
PROCESSOR_TEST_EVENT := processor/events/test.json
API_TEST_EVENT := api/events/test.json

default: check

check: lint type-check test-unit
	@tput bold; tput setaf 2; echo "All checks passed"; tput sgr0

lint:
	autopep8 --recursive --diff $(PY_DIRS)
	flake8 --select=F401 $(PY_DIRS)

type-check:
	mypy . --ignore-missing-imports

test-unit:
	python -m unittest discover -s tests -v

test-integration:
	python -m tests.integration_test

test-cloud-integration:
	python -m tests.integration_test --cloud

set-espn-auth:
	.venv/bin/python scripts/set_espn_auth.py

clean:
	rm -rf .aws-sam/
	rm -rf .mypy_cache/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +

stage:
	mkdir -p .sam-source/processor/cat5 .sam-source/processor/processor .sam-source/api/api
	rsync -a --delete --exclude __pycache__ cat5/ .sam-source/processor/cat5/
	rsync -a --delete --exclude __pycache__ processor/ .sam-source/processor/processor/
	rsync -a --delete --exclude __pycache__ api/ .sam-source/api/api/
	cp requirements-processor.txt .sam-source/processor/requirements-processor.txt
	cp deploy/processor/Makefile .sam-source/processor/Makefile
	cp deploy/api/Makefile .sam-source/api/Makefile

sam: stage
	sam validate --lint
	sam build --use-container

invoke-processor: stage
	sam build Cat5Processor --use-container
	sam local invoke Cat5Processor --event $(PROCESSOR_TEST_EVENT) --env-vars processor/events/env.json

invoke-api: stage
	sam build Cat5Api
	sam local invoke Cat5Api --event $(API_TEST_EVENT) --env-vars api/events/env.json

serve-local: sam
	sam local start-lambda

deploy: check sam
	sam deploy
