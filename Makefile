.PHONY: all clean lint type test test-cov

CMD:=poetry run
PYMODULE:=sr/robot3
TESTS:=tests
EXTRACODE:=

all: type test lint

lint:
	$(CMD) flake8 $(PYMODULE) $(TESTS) $(EXTRACODE)

type:
	$(CMD) mypy --namespace-packages -p sr.robot3
	$(CMD) mypy --namespace-packages $(TESTS) $(EXTRACODE)

test:
	$(CMD) pytest --cov=$(PYMODULE) $(TESTS)

test-cov:
	$(CMD) pytest --cov=$(PYMODULE) $(TESTS) --cov-report html

test-ci:
	$(CMD) pytest --cov=$(PYMODULE) $(TESTS) --cov-report xml

isort:
	$(CMD) isort $(PYMODULE) $(TESTS) $(EXTRACODE)

clean:
	git clean -Xdf # Delete all files in .gitignore
