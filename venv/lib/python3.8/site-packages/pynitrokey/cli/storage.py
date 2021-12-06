# -*- coding: utf-8 -*-
#
# Copyright 2020 Nitrokey Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.


import click

from pynitrokey.helpers import local_print, local_critical

from pynitrokey.libnk import NitrokeyStorage, BaseLibNitrokey, DeviceNotFound


@click.group()
def storage():
    """(experimental) 'Nitrokey Storage' keys, see subcommands."""
    pass


@click.command()
def list():
    """list connected devices"""

    local_print(":: 'Nitrokey Storage' keys:")
    for dct in NitrokeyStorage.list_devices():
        local_print(dct)


@click.command()
@click.option("-p", "--password", default="12345678",
              help="update password to be used instead of default")
def enable_update(password):
    """enable firmware update for NK Storage device"""

    local_print("Enabling firmware update mode")
    nks = NitrokeyStorage()
    nks.connect()
    try:
        if nks.enable_firmware_update(password) == 0:
            local_print("setting firmware update mode - success!")
    except DeviceNotFound:
        local_print("No Nitrokey Storage device found")


storage.add_command(list)
storage.add_command(enable_update)

