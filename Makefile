.PHONY: clean 

-include variables.mk

RUFF ?= poetry run ruff

PACKAGE_NAME=nitrokeyapp

PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

ALL: init build

# setup environment
init: update-venv

update-venv:
ifeq (, $(shell which poetry))
$(error "No poetry in $(PATH)")
endif
	poetry sync --without=deploy

# clean environment
semi-clean:
	rm -rf **/__pycache__
	rm -rf build/
	rm -rf dist/

clean: semi-clean
	poetry env remove --all
	rm -rf .mypy_cache

# build
build:
	poetry build

build-pyinstaller-onefile:
	poetry run pyinstaller ci-scripts/linux/pyinstaller/nitrokey-app-onefile.spec

build-pyinstaller-onedir:
	poetry run pyinstaller ci-scripts/linux/pyinstaller/nitrokey-app-onedir.spec

# code checks
check-format:
	$(RUFF) format --check $(PACKAGE_NAME)/

check-import-sorting:
	$(RUFF) check --select I --diff $(PACKAGE_NAME)/

check-style:
	$(RUFF) check $(PACKAGE_NAME)/

check-typing:
	poetry run mypy $(PACKAGE_NAME)/

check: check-format check-import-sorting check-style check-typing

fix:
	$(RUFF) format $(PACKAGE_NAME)/
	$(RUFF) check --fix $(PACKAGE_NAME)/
