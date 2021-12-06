#!/usr/bin/env python3

import faulthandler
import sys

import fire
import intelhex as ih
import usb1

import nkdfu.dfu as dfu

faulthandler.enable(all_threads=True)


def main(firmware_path: str, bus: str = None):
    """
    Run DFU flashing for the Nitrokey Pro

    Remember to activate bootloader on the Nitrokey Pro before proceeding, or the operation will not start.

    Based on https://github.com/vpelletier/python-dfu

    :param firmware_path: Path to the firmware file, .bin format
    :param bus: USB path, e.g. 2:3
    """
    assert firmware_path.endswith('bin')
    vendor = "20a0:42b4"
    product = None
    if vendor is not None:
        if ':' in vendor:
            vendor, product = vendor.split(':')
            product = int(product, 16)
        vendor = int(vendor, 16)
    dev = None
    if bus is not None:
        if ':' in bus:
            bus, dev = bus.split(':', 1)
            dev = int(dev, 16)
        bus = int(bus, 16)
    with usb1.USBContext() as context:
        for device in context.getDeviceList():
            # print((list(map(hex, (device.getVendorID(), device.getProductID())))))
            if (vendor is not None and (vendor != device.getVendorID() or \
                                        (product is not None and product != device.getProductID()))) \
                    or (bus is not None and (bus != device.getBusNumber() or \
                                             (dev is not None and dev != device.getDeviceAddress()))):
                continue
            break
        else:
            print('No device found.')
            sys.exit(1)
        dfu_device = dfu.DFU(device.open())
        # print dfu_device.upload()
        print(f'Using firmware file {firmware_path}')
        hex_firmware = ih.IntelHex()
        hex_firmware.fromfile(open(firmware_path, 'rb'), "bin")
        data = hex_firmware.tobinarray()
        # data = hex_firmware
        print((dfu_device.download(data)))


def cli():
    fire.Fire(main)
