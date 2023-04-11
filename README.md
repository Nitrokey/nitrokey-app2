# Nitrokey 3 Application - nitrokey-app2

This application is not a replacement for the Nitrokey app. It is an application designed to manage Nitrokey 3 devices. Currently, the app only allows you to update the Nitrokey 3 devices.

## To run on Linux:

```
git clone https://github.com/Nitrokey/nitrokey-app2.git
cd nitrokey-app2
make init
source venv/bin/activate
python3 nitrokeyapp/__main__.py
```

## Notes:
* the current version uses pynitrokey 
* therefore python >3.9 must first be installed

## To run on Windows:

```
python3 -m venv venv
venv/Scripts/python -m pip install -U pip
git installed and path?
venv/Scripts/python -m pip install -U -r dev-requirements.txt
venv/Scripts/python -m flit install --symlink
venv/Scripts/python -m pip install pywin32
venv/Scripts/python venv/Scripts/pywin32_postinstall.py -install
venv/Scripts/activate
python nitrokeyapp/__main__.py
```
## Update ui files
make build-ui
