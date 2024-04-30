# Nitrokey App 2

This application allows to manage Nitrokey 3 devices. To manage Nitrokey Pro and Nitrokey Storage devices, use the older [Nitrokey App](https://github.com/Nitrokey/nitrokey-app).

## Installation

These are the preferred installation methods for the following operating systems:

### Windows

Download and run the prebuilt `.msi` available inside [releases](https://github.com/Nitrokey/nitrokey-app2/releases).

### Linux

Flathub lists the [Nitrokey App2](https://flathub.org/apps/com.nitrokey.nitrokey-app2) to be used for an easy install within your prefered Linux distribution.


### macOS

Currently there is no official support for macOS, you might want to try installing through [pypi](https://pypi.org/project/nitrokeyapp/) using `pip` and/or `pipx`. 


## Features

The following features are currently implemented.

- Firmware update
- Passwords
    - TOTP
    - HOTP

## Download

Executable binaries for Linux and Windows as well as a MSI installer for Windows can be downloaded from the [releases](https://github.com/Nitrokey/nitrokey-app2/releases).

### Compiling for Linux and macOS

This project uses [Poetry](https://python-poetry.org/) as its dependency management and packaging system.
See the [documentation](https://python-poetry.org/docs/) of *Poetry* for available commands.

The application can be compiled by executing:

```
git clone https://github.com/Nitrokey/nitrokey-app2.git
cd nitrokey-app2
make init
make build
poetry shell
nitrokeyapp
```

## Dependencies

* [pynitrokey ](https://github.com/Nitrokey/pynitrokey)
* Python >3.9

## Author

Nitrokey GmbH, Jan Suhr and [contributors](https://github.com/Nitrokey/nitrokey-app2/graphs/contributors).
