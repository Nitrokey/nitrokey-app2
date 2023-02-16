# Alternative Nitrokey Application - nitrokey-app2

Work in Progress !!

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
## Update ui files (for Devs)

python -m PyQt5.uic.pyuic -x "changed_file".ui -o "changed_file_ui".py