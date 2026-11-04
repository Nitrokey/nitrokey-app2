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

check-style:
	$(RUFF) check $(PACKAGE_NAME)/

check-typing:
	poetry run mypy $(PACKAGE_NAME)/

check: check-format check-style check-typing

fix:
	$(RUFF) format $(PACKAGE_NAME)/
	$(RUFF) check --fix $(PACKAGE_NAME)/

# desktop integration
XDG_DATA_HOME ?= $(HOME)/.local/share
DESKTOP_ENTRY = $(XDG_DATA_HOME)/applications/com.nitrokey.nitrokey-app2.desktop

install-desktop-entry:
	@mkdir -p $(dir $(DESKTOP_ENTRY))
	@bin=$$(poetry run sh -c 'command -v nitrokey-app2' | tail -n 1); test -n "$$bin" || { echo "nitrokey-app2 not found, run 'make init' first" >&2; exit 1; }; sed -e "s|^TryExec=.*|TryExec=$$bin|" -e "s|^Exec=.*|Exec=$$bin|" -e "s|^Icon=.*|Icon=$(CURDIR)/meta/nk-app2.svg|" meta/com.nitrokey.nitrokey-app2.desktop > $(DESKTOP_ENTRY)
	@echo "installed $(DESKTOP_ENTRY)"

uninstall-desktop-entry:
	rm -f $(DESKTOP_ENTRY)
