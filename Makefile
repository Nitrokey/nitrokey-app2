.PHONY: clean 

PACKAGE_NAME=nitrokeyapp
PYTHON=python3
VENV=$(shell poetry env info --path)
VENV_BIN=$(VENV)/bin
VENV_PYTHON=$(VENV_BIN)/$(PYTHON)
UI_FILES_PATH=nitrokeyapp/ui
UI_FILES = $(wildcard $(UI_FILES_PATH)/*.ui)

ALL: init build

# setup environment
init: update-venv

update-venv:
ifeq (, $(shell which poetry))
$(error "No poetry in $(PATH)")
endif
	poetry env use $(PYTHON)
	poetry install --sync --without=deploy

# clean environment
semi-clean:
	rm -rf **/__pycache__
	rm -rf build/
	rm -rf dist/

clean: semi-clean
	rm -rf $(VENV)
	rm -rf .mypy_cache

# build
build-ui: $(UI_FILES)
	$(VENV_BIN)/pyrcc5 $(UI_FILES_PATH)/resources.qrc -o $(UI_FILES_PATH)/resources_rc.py
	$(foreach var,$(UI_FILES),$(VENV_BIN)/pyuic5 --from-imports $(var) -o $(subst .ui,.py,$(var));)

build: build-ui
	$(VENV_PYTHON)/bin/$(PYTHON) -m flit build --no-use-vcs

# code checks
check-format:
	$(VENV_PYTHON) -m black --check $(PACKAGE_NAME)/

check-import-sorting:
	$(VENV_PYTHON) -m isort --check-only $(PACKAGE_NAME)/

check-style:
	$(VENV_PYTHON) -m flake8 $(PACKAGE_NAME)/

check-typing: build-ui
	$(VENV_PYTHON) -m mypy $(PACKAGE_NAME)/

check: check-format check-import-sorting check-style check-typing

fix:
	$(VENV_PYTHON) -m black $(PACKAGE_NAME)/
	$(VENV_PYTHON) -m isort $(PACKAGE_NAME)/
