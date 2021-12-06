import platform
import sys

import click
import nkdfu
import logging
import intelhex as ih

from pynitrokey.helpers import local_print
from pynitrokey.libnk import NitrokeyPro, DeviceNotFound

print = local_print
vendor = "20a0:42b4"

@click.group()
def pro():
    """Interact with Nitrokey Pro keys, see subcommands."""
    pass


@click.command()
def list():
    """list connected devices"""

    local_print(":: 'Nitrokey Pro' keys:")
    for dct in NitrokeyPro.list_devices():
        local_print(dct)


@click.command()
@click.option("-p", "--password", default="12345678",
              help="update password to be used instead of default")
def enable_update(password):
    """enable firmware update for NK Pro device"""

    local_print("Enabling firmware update mode")
    nks = NitrokeyPro()
    try:
        libnk_version_current = nks.library_version()
    except Exception as e:
        local_print('Unhandled libnitrokey library version. Please upgrade it.')
        local_print(f'Error: {str(e)}')
        return 1
    libnk_version_required = (3, 5)
    if libnk_version_current < libnk_version_required:
        local_print(f'You need libnitrokey {libnk_version_required} to run this command. Currently installed: {libnk_version_current}.')
        local_print('You can provide custom path for the libnitrokey with LIBNK_PATH environmental variable, e.g. by calling it like:')
        local_print('$ env LIBNK_PATH=/my/path/libnitrokey.so nitropy <command>')
        return 1

    try:
        nks.connect()
        if nks.enable_firmware_update(password) == 0:
            local_print("Setting firmware update mode - success!")
        local_print("Done")
    except DeviceNotFound:
        local_print(f"No {nks.friendly_name} device found")
        local_print("If connected, perhaps already in update mode?")


@click.command()
@click.argument("firmware_path")
def update(firmware_path: str):
    """
    Run firmware update with the provided binary.

    FIRMWARE_PATH: A path to the firmware file. File name should end with .bin.
    """
    import nkdfu.dfu as dfu
    import usb1

    print = local_print
    # TODO(szszsz): extract logic to nkdfu, leaving only end-user error handling
    assert firmware_path.endswith('bin')
    vendor = "20a0:42b4"
    product = None
    if vendor is not None:
        if ':' in vendor:
            vendor, product = vendor.split(':')
            product = int(product, 16)
        vendor = int(vendor, 16)
    dev = None
    bus = None
    with usb1.USBContext() as context:
        for device in context.getDeviceList():
            if (vendor is not None and (vendor != device.getVendorID() or \
                                        (product is not None and product != device.getProductID()))) \
                    or (bus is not None and (bus != device.getBusNumber() or \
                                             (dev is not None and dev != device.getDeviceAddress()))):
                continue
            break
        else:
            print('No Nitrokey Pro found in the update mode.')
            print('If you have Nitrokey Pro connected please run (requires libnitrokey):')
            print('$ nitropy pro enable-update')
            sys.exit(1)
        dfu_device = None
        try:
            dfu_device = dfu.DFU(device.open())
        except usb1.USBErrorAccess as e:
            print(f'Cannot connect to the device: {device} -> {e}')
            if 'LIBUSB_ERROR_ACCESS' in str(e) and platform.system().lower() == 'linux':
                print('Try to install UDEV rules, e.g. by executing the following:')  # TODO add command for that
                print('$ curl https://raw.githubusercontent.com/Nitrokey/libnitrokey/master/data/41-nitrokey.rules | sudo tee /usr/lib/udev/rules.d/41-nitrokey.rules')
                print('$ sudo udevadm control --reload-rules; sudo udevadm trigger')
            sys.exit(1)
        except Exception as e:
            print(f'Cannot connect to the device: {device} -> {e}')
            sys.exit(1)

        print(f'Using firmware file {firmware_path}')
        hex_firmware = ih.IntelHex()
        hex_firmware.fromfile(open(firmware_path, 'rb'), "bin")
        data = hex_firmware.tobinarray()
        try:
            print((dfu_device.download(data)))
            print('Please reinsert device to the USB port to complete the process')
        except nkdfu.dfu.DFUBadSate as e:
            print(f'Cannot connect to the device: {device} -> {e}')
            print(f'Reinsert device to the USB port and try again (DFU connects, but reports invalid state)')
            sys.exit(1)
        except Exception as e:
            print(f'Cannot connect to the device: {device} -> {e}')
            sys.exit(1)


pro.add_command(update)
pro.add_command(list)
pro.add_command(enable_update)

