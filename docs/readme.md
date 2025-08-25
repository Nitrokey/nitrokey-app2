# Developer Documentation

Nitrokey App 2 uses [Poetry](https://python-poetry.org/) for dependency and package management.

The Makefile provides targets for common operations:
- `make init` to install or update the development environment
- `make check` to run all checks and lints
- `make fix` to automatically fix some problems reported by `make check`

If you create a PR, please make sure that `make check` runs successfully.
