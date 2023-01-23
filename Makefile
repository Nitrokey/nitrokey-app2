.PHONY: clean 

PACKAGE_NAME=nitropyapp
VENV=venv
PYTHON3=python3

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
