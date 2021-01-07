# Alternative Nitrokey Application - nitropy-app

Work in Progress !!

To run:
```
cd /tmp
git clone https://github.com/daringer/nitropy-app.git
cd nitropy-app
make
venv/bin/nitropy-app
```

Once started, click on `Help` (don't ask why) to connect a device.
Currently HOTP/TOTP save, erase, get (just choose it from the dropdown) is (likely) working.
Due to a currently exisiting bug in libnitrokey make sure no FIDO2 key is plugged in!


