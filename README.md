# Nitrokey App 2

This application allows to manage Nitrokey 3 devices. To manage Nitrokey Pro and Nitrokey Storage devices, use the older [Nitrokey App](https://github.com/Nitrokey/nitrokey-app).

## Features

The following features are currently implemented.

- Firmware update
- Passwords
    - TOTP
    - HOTP

## Download

Executable binaries for Linux and Windows as well as a MSI installer for Windows can be downloaded from the [releases](https://github.com/Nitrokey/nitrokey-app2/releases).

### Compiling for Linux and macOS

The application can be compiled by executing:

```
git clone https://github.com/Nitrokey/nitrokey-app2.git
cd nitrokey-app2
make update-venv
source venv/bin/activate
make build
nitrokeyapp
```

## Dependencies

* [pynitrokey ](https://github.com/Nitrokey/pynitrokey)
* Python >3.9

