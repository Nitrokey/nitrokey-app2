# -*- coding: utf-8 -*-
#
# Copyright 2019 SoloKeys Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import sys
import time

import click
from fido2.ctap import CtapError

from pynitrokey.helpers import local_print, local_critical

from pynitrokey.fido2 import find
from pynitrokey.fido2 import hot_patch_windows_libusb



@click.group()
def program():
    """Program a key."""
    pass
#
# @click.command()
# @click.option("-s", "--serial", help="Serial number of Nitrokey to use")
# @click.argument("firmware")  # , help="firmware (bundle) to program")
# def check_only(serial, firmware):
#     """Validate currently flashed firmware, and run on success. Bootloader only."""
#     from pynitrokey.fido2 import find
#     p = find(serial)
#     try:
#         p.use_hid()
#         p.program_file(firmware)
#     except CtapError as e:
#         if e.code == CtapError.ERR.INVALID_COMMAND:
#             local_critical("Not in bootloader mode.", e)


@click.command()
@click.option("-s", "--serial", help="Serial number of Nitrokey to use")
@click.argument("firmware")  # , help="firmware (bundle) to program")
def bootloader(serial, firmware):
    """Program via Nitrokey bootloader interface.

    \b
    FIRMWARE argument should be either a .hex or .json file.

    If the bootloader is verifying, the .json is needed containing
    a signature for the verifying key in the bootloader.

    If the bootloader is nonverifying, either .hex or .json can be used.

    DANGER: if you try to flash a firmware with signature that doesn't
    match the bootloader's verifying key, you will be stuck in bootloader
    mode until you find a signed firmware that does match.

    Enter bootloader mode using `nitropy fido2 util program aux enter-bootloader` first.
    """

    p = find(serial)
    try:
        p.use_hid()
        p.program_file(firmware)
    except CtapError as e:
        if e.code == CtapError.ERR.INVALID_COMMAND:
            local_print("Not in bootloader mode.  Attempting to switch...")
            local_print("Please confirm with button on key!")
        else:
            local_critical(e)

        p.enter_bootloader_or_die()

        local_print("Nitrokey rebooted.  Reconnecting...")
        time.sleep(2.0)

        find(serial)
        if p is None:
            local_critical("Cannot find Nitrokey device.")

        p.use_hid()
        p.program_file(firmware)


@click.group()
def aux():
    """Auxiliary commands related to firmware/bootloader/dfu mode."""
    pass


def _enter_bootloader(serial):
    from pynitrokey.fido2 import find
    p = find(serial)

    local_print("please use the button on the device to confirm")
    p.enter_bootloader_or_die()

    local_print("Nitrokey rebooted.  Reconnecting...")
    time.sleep(0.5)
    if find(serial) is None:
        local_critical(RuntimeError("Failed to reconnect!"))


@click.command()
@click.option("-s", "--serial", help="Serial number of Nitrokey to use")
def enter_bootloader(serial):
    """Switch from Nitrokey firmware to Nitrokey bootloader.

    Note that after powercycle, you will be in the firmware again,
    assuming it is valid.
    """

    return _enter_bootloader(serial)


@click.command()
@click.option("-s", "--serial", help="Serial number of Nitrokey to use")
def leave_bootloader(serial):
    """Switch from Nitrokey bootloader to Nitrokey firmware."""
    from pynitrokey.fido2 import find
    find(serial).reboot()


@click.command()
@click.option("-s", "--serial", help="Serial number of Nitrokey to use")
def reboot(serial):
    """Reboot.

    \b
    This implementation actually only works for bootloader reboot
    """

    # this implementation actually only works for bootloader
    # firmware doesn't have a reboot command
    from pynitrokey.fido2 import find
    find(serial).reboot()


@click.command()
@click.option("-s", "--serial", help="Serial number of Nitrokey to use")
@click.option("-p", "--pubkey", help="Show public key for the firmware", is_flag=True)
def bootloader_version(serial, pubkey):
    """Version of bootloader."""
    from pynitrokey.fido2 import find
    p = find(serial)

    if not p.is_solo_bootloader():
        local_print("Not in Bootloader Mode!")
        return
    else:
        local_print("Detected Bootloader Mode")

    local_print("Version: " + ".".join(map(str, p.bootloader_version())))
    from binascii import b2a_hex
    from hashlib import sha256
    if pubkey:
        bpub = p.boot_pubkey()
        bpub = b2a_hex(bpub)
        local_print(f'Bootloader public key: \t\t{bpub}')
        s = sha256()
        s.update(bpub)
        bpubh = b2a_hex(s.digest())
        local_print(f'Bootloader public key sha256: \t{bpubh}')


program.add_command(aux)

aux.add_command(bootloader_version)
aux.add_command(leave_bootloader)
aux.add_command(enter_bootloader)
aux.add_command(reboot)

program.add_command(bootloader)


# @fixme: looks useless, so remove it?
#program.add_command(check_only)


