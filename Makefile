.PHONY: clean 

PACKAGE_NAME=nitrokeyapp
VENV=venv
PYTHON=python3
UI_FILES_PATH=nitrokeyapp/ui
UI_FILES = $(wildcard $(UI_FILES_PATH)/*.ui)

ALL: update-venv build

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

build-ui: $(UI_FILES)
	pyrcc5 $(UI_FILES_PATH)/resources.qrc -o $(UI_FILES_PATH)/resources_rc.py
	$(foreach var,$(UI_FILES),pyuic5 --from-imports $(var) -o $(subst .ui,.py,$(var));)

build: build-ui
	$(VENV)/bin/$(PYTHON) -m flit build

# code checks
check-format:
	$(PYTHON) -m black --check $(PACKAGE_NAME)/

check-import-sorting:
	$(PYTHON) -m isort --check-only $(PACKAGE_NAME)/

check-style:
	$(PYTHON) -m flake8 $(PACKAGE_NAME)/

check-typing:
	$(PYTHON) -m mypy $(PACKAGE_NAME)/

check: check-format check-import-sorting check-style check-typing

fix:
	$(PYTHON) -m black $(PACKAGE_NAME)/
	$(PYTHON) -m isort $(PACKAGE_NAME)/
