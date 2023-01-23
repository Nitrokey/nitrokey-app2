.PHONY: clean 

PACKAGE_NAME=nitropyapp
VENV=venv
PYTHON3=python3

BLACK_FLAGS=-t py39
ISORT_FLAGS=--py 39

# setup environment
init: update-venv

update-venv: $(VENV)
	$(VENV)/bin/python3 -m pip install -U pip
	$(VENV)/bin/python3 -m pip install flit
	$(VENV)/bin/python3 -m flit install --symlink

$(VENV):
	$(PYTHON3) -m venv $(VENV)
	$(VENV)/bin/python3 -m pip install -U pip

# clean environment
semi-clean:
	rm -rf **/__pycache__

clean: semi-clean
	rm -rf $(VENV)
	rm -rf .mypy_cache

build:
	$(VENV)/bin/python3 -m flit build

# code checks
check-format:
	python3 -m black $(BLACK_FLAGS) --check $(PACKAGE_NAME)/

check-import-sorting:
	python3 -m isort $(ISORT_FLAGS) --check-only $(PACKAGE_NAME)/

check-style:
	python3 -m flake8 $(PACKAGE_NAME)/