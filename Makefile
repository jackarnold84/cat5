PY_DIRS := api db cat5 processor tests

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
