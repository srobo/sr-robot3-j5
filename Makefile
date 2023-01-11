.PHONY: all clean docs lint type test test-cov

CMD:=poetry run
PYMODULE:=sr/robot3
TESTS:=tests
SPHINX_ARGS:=docs/ docs/_build -nWE
EXTRACODE:=examples/

all: type test lint

docs:
	$(CMD) sphinx-build $(SPHINX_ARGS)

docs-serve:
	$(CMD) sphinx-autobuild $(SPHINX_ARGS)


lint:
	$(CMD) flake8 $(PYMODULE) $(TESTS) 
	$(CMD) flake8 --config=extracode.flake8 $(EXTRACODE)
	$(CMD) isort $(PYMODULE) $(TESTS) $(EXTRACODE)

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
