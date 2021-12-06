
import time
import socket
import usb

#from pynitrokey.fido2 import hmac_secret
from pynitrokey.fido2.client import NKFido2Client
from pynitrokey.exceptions import NoSoloFoundError


def hot_patch_windows_libusb():
    # hot patch for windows libusb backend
    olddel = usb._objfinalizer._AutoFinalizedObjectBase.__del__

    def newdel(self):
        try:
            olddel(self)
        except OSError:
            pass

    usb._objfinalizer._AutoFinalizedObjectBase.__del__ = newdel



def _UDP_InternalPlatformSwitch(funcname, *args, **kwargs):
    if funcname == "__init__":
        return HidOverUDP(*args, **kwargs)
    return getattr(HidOverUDP, funcname)(*args, **kwargs)



def find(solo_serial=None, retries=5, raw_device=None, udp=False):
    if udp:
        force_udp_backend()

    p = NKFido2Client()

    # This... is not the right way to do it yet
    p.use_u2f()

    for i in range(retries):
        try:
            p.find_device(dev=raw_device, solo_serial=solo_serial)
            return p
        except RuntimeError:
            time.sleep(0.2)

    # return None
    raise NoSoloFoundError("no Nitrokey FIDO2 found")


def find_all():
    from fido2.hid import CtapHidDevice

    hid_devices = list(CtapHidDevice.list_devices())
    solo_devices = [d for d in hid_devices
        if (d.descriptor.vid, d.descriptor.pid) in [
            ## @FIXME: move magic numbers
            (1155, 41674),
            (0x20A0, 0x42B3),
            (0x20A0, 0x42B1),
        ]
    ]
    return [find(raw_device=device) for device in solo_devices]


