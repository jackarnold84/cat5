PY_DIRS := api cat5 processor tests
PROCESSOR_TEST_EVENT := processor/events/test.json
API_TEST_EVENT := api/events/test.json

default: check

run:
	python -m tests.e2e_test

lint:
	autopep8 --recursive --diff $(PY_DIRS)
	flake8 --select=F401 $(PY_DIRS)

type-check:
	mypy . --ignore-missing-imports

test:
	python -m unittest discover -s tests -v

check: lint type-check test
	@tput bold; tput setaf 2; echo "All checks passed"; tput sgr0

clean:
	rm -rf .aws-sam/
	rm -rf .mypy_cache/
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +

sam:
	sam build

build-Cat5Api:
	cp -r api $(ARTIFACTS_DIR)/api

invoke-processor: sam
	sam local invoke Cat5Processor --event $(PROCESSOR_TEST_EVENT) --env-vars processor/events/env.json

invoke-api: sam
	sam local invoke Cat5Api --event $(API_TEST_EVENT) --env-vars api/events/env.json

serve-local: sam
	sam local start-lambda

deploy: check sam
	sam deploy --guided
