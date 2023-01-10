.PHONY: clean 

PACKAGE_NAME=nitropy-app
VENV=venv
PYTHON3=python3

init: update-venv

semi-clean:
	rm -rf **/__pycache__

build:
	$(VENV)/bin/python3 -m flit build

clean: semi-clean
	rm -rf $(VENV)
	rm -rf dist

update-venv: $(VENV)
	$(VENV)/bin/python3 -m pip install -U pip
	$(VENV)/bin/python3 -m pip install -U -r dev-requirements.txt
	$(VENV)/bin/python3 -m flit install --symlink

$(VENV):
	$(PYTHON3) -m venv $(VENV)
	$(VENV)/bin/python3 -m pip install -U pip
