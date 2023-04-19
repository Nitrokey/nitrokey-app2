# Nitrokey App 2

This application allows to manage Nitrokey 3 devices. Currently, it only allows updating the firmware of Nitrokey 3 devices. More features will be added. To manage Nitrokey Pro and Nitrokey Storage devices, use the older [Nitrokey App](https://github.com/Nitrokey/nitrokey-app).

## To run on Linux and (macOS):
We offer two options here:
### The source code
```
git clone https://github.com/Nitrokey/nitrokey-app2.git
cd nitrokey-app2
make
source venv/bin/activate
python3 nitrokeyapp/__main__.py
```
### The Binary
You can find it in the releases:
https://github.com/Nitrokey/nitrokey-app2/releases

## To run on Windows:
We offer two binary options here:

### The Msi-installer
You can find it in the releases (.msi):
https://github.com/Nitrokey/nitrokey-app2/releases

### The Executable
You can find it in the releases (windows-binary.zip):
https://github.com/Nitrokey/nitrokey-app2/releases

## Notes:
* the current version uses pynitrokey 
* therefore python >3.9 must first be installed

