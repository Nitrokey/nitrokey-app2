# Nitrokey App 2

This application allows to manage Nitrokey 3 devices. Currently, it only allows updating the firmware of Nitrokey 3 devices. More features will be added. To manage Nitrokey Pro and Nitrokey Storage devices, use the older [Nitrokey App](https://github.com/Nitrokey/nitrokey-app).

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
## Update UI files
make build-ui
