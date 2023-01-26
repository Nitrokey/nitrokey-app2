.PHONY: clean 

PACKAGE_NAME=nitropyapp
VENV=venv
PYTHON=python3

BLACK_FLAGS=-t py39
ISORT_FLAGS=--py 39

# setup environment
init: update-venv

update-venv: $(VENV)
	$(VENV)/bin/$(PYTHON) -m pip install -U pip
	$(VENV)/bin/$(PYTHON) -m pip install flit
	$(VENV)/bin/$(PYTHON) -m flit install --symlink

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/$(PYTHON) -m pip install -U pip

# clean environment
semi-clean:
	rm -rf **/__pycache__

clean: semi-clean
	rm -rf $(VENV)
	rm -rf .mypy_cache

build:
	$(VENV)/bin/$(PYTHON) -m flit build

# code checks
check-format:
	$(PYTHON) -m black $(BLACK_FLAGS) --check $(PACKAGE_NAME)/

check-import-sorting:
	$(PYTHON) -m isort $(ISORT_FLAGS) --check-only $(PACKAGE_NAME)/

check-style:
	$(PYTHON) -m flake8 $(PACKAGE_NAME)/

check-typing:
	$(PYTHON) -m mypy $(PACKAGE_NAME)/