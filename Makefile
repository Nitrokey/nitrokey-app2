.PHONY: clean translations-update translations-release check-translations

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
	rm -f $(PACKAGE_NAME)/translations/*.qm

# translations
translations-update:
	poetry run python ci-scripts/translations.py update

translations-release:
	poetry run python ci-scripts/translations.py release

# build
build: translations-release
	poetry build

build-pyinstaller-onefile: translations-release
	poetry run pyinstaller ci-scripts/linux/pyinstaller/nitrokey-app-onefile.spec

build-pyinstaller-onedir: translations-release
	poetry run pyinstaller ci-scripts/linux/pyinstaller/nitrokey-app-onedir.spec

# code checks
check-format:
	$(RUFF) format --check $(PACKAGE_NAME)/

check-style:
	$(RUFF) check $(PACKAGE_NAME)/

check-typing:
	poetry run mypy $(PACKAGE_NAME)/

check-translations:
	poetry run python ci-scripts/translations.py check

check: check-format check-style check-typing check-translations

fix:
	$(RUFF) format $(PACKAGE_NAME)/
	$(RUFF) check --fix $(PACKAGE_NAME)/
