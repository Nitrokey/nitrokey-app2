#!/usr/bin/env python3
"""
Copyright (c) 2015-2018 Nitrokey UG

This file is part of libnitrokey.

libnitrokey is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

libnitrokey is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with libnitrokey. If not, see <http://www.gnu.org/licenses/>.

SPDX-License-Identifier: LGPL-3.0
"""

from pathlib import Path
from random import randint
from datetime import datetime as dt
from functools import wraps

import cffi
from enum import IntEnum

from typing import Tuple, List

from pynitrokey.exceptions import BasePyNKException


class LibraryNotFound(BasePyNKException): pass
class DeviceNotFound(BasePyNKException): pass
class InvalidHOTPSecret(BasePyNKException): pass
class InvalidTOTPSecret(BasePyNKException): pass



ffi = cffi.FFI()


def _get_c_library():
    # @todo: how to properly search for c-libs (on all platforms)
    #        maybe: lin + mac = pkgconfig? win = PATH?
    root = Path("/")
    header_paths = [
        root / "usr" / "include" / "libnitrokey" / "NK_C_API.h"
    ]
    lib_paths = [
        root / "lib" / "libnitrokey.so",
        root / "usr" / "lib" / "libnitrokey.so",
        root / "usr" / "local" / "lib" / "libnitrokey.so"
    ]

    c_code = []
    for h_path in header_paths:
        with open(h_path.as_posix(), 'r') as fd:
            c_code += fd.readlines()

    cnt = 0
    a = iter(c_code)
    for line in a:
        # parse `enum` and `struct` (maybe typedef?)
        if line.strip().startswith("struct") or \
                line.strip().startswith("enum"):
            while '};' not in line:
                line += (next(a)).strip()
            ffi.cdef(line, override=True)
            cnt += 1
        # parse marked-as portions from the header (function calls)
        if line.strip().startswith('NK_C_API'):
            line = line.replace('NK_C_API', '').strip()
            while ';' not in line:
                line += (next(a)).strip()
            ffi.cdef(line, override=True)
            cnt += 1

    # currently 90 (inc. enums, structs, func-sigs)
    assert cnt > 85

    lib_paths = [p.absolute().as_posix() for p in lib_paths if p.exists()]
    if len(lib_paths) > 0:
        return ffi.dlopen(lib_paths.pop())


def to_hex(ss):
    return ''.join([format(ord(s), '02x') for s in ss])

# def lazyio(f):
#     @wraps
#     def wrapper(*v, **kw):
#         ret_val = f(*v, **kw)
#
#         return py_enc(ret_val) \
#             if isinstance(ret_val, ffi.CData) and \
#                "char" in ffi.typeof(ret_val).cname else ret_val
#
#     return wrapper
#



class DeviceErrorCode(IntEnum):
    STATUS_OK = 0
    NOT_PROGRAMMED = 3
    WRONG_PASSWORD = 4
    STATUS_NOT_AUTHORIZED = 5
    STATUS_AES_DEC_FAILED = 0xA

class LibraryErrorCode(IntEnum):
    # Library
    InvalidSlotException = 201
    TooLongStringException = 200
    TargetBufferSmallerThanSource = 203
    InvalidHexString = 202

class DeviceCommunicationErrorCode(IntEnum):
    DeviceNotConnected = 2
    DeviceSendingFailure = 3
    DeviceReceivingFailure = 4
    InvalidCRCReceived = 5


# @todo: derive/get from c-header ?
class DeviceModel(IntEnum):
    NONE = 0
    NK_PRO = 1
    NK_STORAGE = 2
    NK_LIBREM = 3

    @property
    def friendly_name(self):
        return {
            DeviceModel.NONE:       "Disconnected",
            DeviceModel.NK_PRO:     NitrokeyPro.friendly_name,
            DeviceModel.NK_STORAGE: NitrokeyStorage.friendly_name,
            DeviceModel.NK_LIBREM:  "Nitrokey Librem(?)"
        }[self.value]

# string-conversion functions from/to C(++) @fixme: rename properly
c_enc = lambda x: x.encode("ascii") if isinstance(x, str) else x
py_enc = lambda x: ffi.string(x).decode() if not isinstance(x, str) else x

def gen_tmp_pass():
    _hay = "1234567890abcdefghijklmnopqrstuwvxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return c_enc("".join(_hay[randint(0, len(_hay) - 1)] \
                         for _ in range(MAX_PASS_LEN)))

MAX_PASS_LEN = 20

ADMIN_PIN = "12345678"
USER_PIN = "123456"

ADMIN_SESSION_PIN = gen_tmp_pass()
USER_SESSION_PIN = ADMIN_SESSION_PIN #gen_tmp_pass()


class BaseLibNitrokey:
    single_api = None

    friendly_name = "Nitrokey Device"

    def __init__(self):
        self._connected = False

        self.HOTP = self.hotp = HOTPSlots(self.api)
        self.TOTP = self.totp = TOTPSlots(self.api)
        self.PSafe = self.psafe = PasswordSlots(self.api)

    ###################################################
    @classmethod
    def get_api(cls):
        if not BaseLibNitrokey.single_api:
            BaseLibNitrokey.single_api = _get_c_library()
            if not BaseLibNitrokey.single_api:
                raise LibraryNotFound()
        return BaseLibNitrokey.single_api

    @classmethod
    def library_version(cls):
        api = cls.get_api()
        return (api.NK_get_major_library_version(),
                api.NK_get_minor_library_version())

    @classmethod
    def list_devices(cls):
        api = cls.get_api()
        dev_info = api.NK_list_devices()

        out, cur = {}, dev_info
        if not cur:
            return {}

        while True:
            model = DeviceModel(cur.model)
            name = model.friendly_name + "-" + py_enc(cur.serial_number)
            name = name.replace("0", "")
            out[name] = {
                "model": cur.model,
                "path": py_enc(cur.path),
                "name": name,
                "serial": py_enc(cur.serial_number)
            }
            if not cur.next:
                break
            cur = cur.next

        api.NK_free_device_info(dev_info)
        return out

        ##### raw_devs = api.NK_list_devices_by_cpuID()

    ###################################################

    @property
    def api(self):
        return self.get_api()

    def connect(self, path=None, cpu_id=None):
        """base-class uses 'auto' to connect to any key, or by path/id"""
        if path:
            self.api.NK_connect_with_path(c_enc(path))
        elif cpu_id:
            self.api.NK_connect_with_ID(c_enc(cpu_id))
        else:
            self._connect()

        if not self.connected:
            raise DeviceNotFound(self.friendly_name)

    def _connect(self):
        return self.api.NK_login_auto()

    def admin_auth(self, admin_pass):
        return self.api.NK_first_authenticate(c_enc(admin_pass),
                                              c_enc(ADMIN_SESSION_PIN))

    def user_auth(self, user_pass):
        return self.api.NK_user_authenticate(c_enc(user_pass),
                                             c_enc(USER_SESSION_PIN))

    def lock(self):
        return self.api.NK_lock_device()

    def logout(self):
        return self.api.NK_logout()

    def set_debug_level(self, lvl):
        # 0 - 5(max)
        self.api.NK_set_debug_level(lvl)

    @property
    def connected(self):
        # @fixme: on performance issues a timed-cache (~1sec?) might help

        # using `device_model` to determine, if some device is connected
        self._connected = self.device_model > DeviceModel.NONE and \
                          len(self.raw_status.strip()) > 0
        return self._connected

    @property
    def fw_version(self):
        return (self.api.NK_get_major_firmware_version(),
                self.api.NK_get_minor_firmware_version())
    @property
    def serial(self, as_int=False):
        return py_enc(self.api.NK_device_serial_number()) if not as_int \
            else self.api.NK_device_serial_number_as_u32()
    @property
    def last_command_status(self):
        return self.api.NK_get_last_command_status()
    @property
    def raw_status(self):
        return py_enc(self.api.NK_get_status_as_string())
    @property
    def device_model(self):
        return self.api.NK_get_device_model()
    @property
    def admin_pin_retries(self):
        return self.api.NK_get_admin_retry_count()
    @property
    def user_pin_retries(self):
        return self.api.NK_get_user_retry_count()

    @property
    def status(self):
        dct = dict([line.split(":") for line in self.raw_status.split("\n") \
                    if line.strip()])
        out = {key: val.replace("-", "").replace("\t", "").replace(".", "").strip() \
                    for key, val in dct.items()}
        out["fw_version"] = self.fw_version
        out["last_cmd_status"] = self.last_command_status
        out["admin_pin_retries"] = self.admin_pin_retries
        out["user_pin_retries"] = self.user_pin_retries
        out["card_serial"] = out["card_serial"][:11]
        out["model"] = DeviceModel(self.device_model)
        out["connected"] = self.connected
        return out

    def build_aes_key(self, admin_pass):
        return self.api.NK_build_aes_key(c_enc(admin_pass))

    def factory_reset(self, admin_pass):
        return self.api.NK_factory_reset(c_enc(admin_pass))

    def change_admin_pin(self, old_pin, new_pin):
        return self.api.NK_change_admin_PIN(c_enc(old_pin), c_enc(new_pin))

    def change_user_pin(self, old_pin, new_pin):
        return self.api.NK_change_user_PIN(c_enc(old_pin), c_enc(new_pin))

    def unlock_user_pin(self, admin_pass, new_user_pin):
        return self.api.NK_unlock_user_password(c_enc(admin_pass), c_enc(new_user_pin))


# NK_C_API int NK_write_config(uint8_t numlock, uint8_t capslock, uint8_t scrolllock,
#     bool enable_user_password, bool delete_user_password,
#     const char *admin_temporary_password);
# NK_C_API int NK_write_config_struct(struct NK_config config,
#     const char *admin_temporary_password);
# NK_C_API uint8_t* NK_read_config();
# NK_C_API void NK_free_config(uint8_t* config);
# NK_C_API int NK_read_config_struct(struct NK_config* out);


#  NK_get_last_command_status();
#  NK_get_status(struct NK_status* out);
#  NK_C_API char * NK_get_status_as_string() - (debug)
#  NK_login_auto - (connects to first device available...)
#

class NitrokeyStorage(BaseLibNitrokey):
    friendly_name = "Nitrokey Storage"

    def _connect(self):
        """only connects to NitrokeyStorage devices"""
        return self.api.NK_login(b'S')


class NitrokeyPro(BaseLibNitrokey):
    friendly_name = "Nitrokey Pro"

    def _connect(self):
        """only connects to NitrokeyPro devices"""
        return self.api.NK_login(b'P')


class BaseSlots:
    def __init__(self, api):
        self.api = api

    def get_code(self, *v, **kw):
        return py_enc(self._get_code(*v, **kw))

    def get_name(self, *v, **kw):
        return py_enc(self._get_name(*v, **kw))

    def write_slot(self, *v, **kw):
        return self._write_slot(*v, **kw)

    def erase_slot(self, *v, **kw):
        return self._erase_slot(*v, **kw)

    def _get_code(self, *v, **kw):
        raise NotImplementedError((v, kw))
    _erase_slot = _write_slot = _get_name = _get_code

    # def __getitem__(self, slot_idx):
    #     return self.get_code().get_code
    # def __setitem__(self, slot_idx, secret):
    #     self.write_slot()
    # def __delitem__(self, slot_id):
    #     self.erase_slot()


class HOTPSlots(BaseSlots):
    count = 3
    def _get_name(self, slot_idx):
        return py_enc(self.api.NK_get_hotp_slot_name(slot_idx))

    def _get_code(self, slot_idx):
        return self.api.NK_get_hotp_slot_name(slot_idx)

    def _write_slot(self, slot_idx, name, secret, hotp_cnt, use_8_digits=False,
                    use_enter=False, token_id=None):
        """secret is expected without(!) \0 termination"""

        if len(secret) != 40:
            raise InvalidHOTPSecret(("len", len(secret)))
        secret = secret.encode("ascii") + '\x00'.encode("ascii")

        tmp_pass = c_enc(ADMIN_SESSION_PIN)

        # @TODO: interpret ret-val as LibraryErrorCode
        return self.api.NK_write_hotp_slot(slot_idx, c_enc(name), secret,
            hotp_cnt, use_8_digits, use_enter, not token_id, c_enc(""), tmp_pass)

    def _erase_slot(self, slot_idx):
        return self.api.NK_erase_hotp_slot(slot_idx, ADMIN_SESSION_PIN)


class TOTPSlots(BaseSlots):
    count = 15
    def _get_name(self, slot_idx):
        return self.api.NK_get_totp_slot_name(slot_idx)

    def _get_code(self, slot_idx):
        return self.api.NK_get_totp_code(slot_idx)

    def _write_slot(self, slot_idx, name, secret, time_window=30, use_8_digits=False,
                    use_enter=False, token_id=None):
        tmp_pass = c_enc(ADMIN_SESSION_PIN)
        return self.api.NK_write_totp_slot(slot_idx, c_enc(name), c_enc(secret),
                                           time_window, use_8_digits, use_enter,
                                           not token_id, c_enc(""), tmp_pass)

        # NdK_write_totp_slot(uint8_t slot_number, const char *slot_name, const char *secret, uint16_t time_window,
        # 		bool use_8_digits, bool use_enter, bool use_tokenID, const char *token_ID,
        # 		const char *temporary_password);

    def _erase_slot(self, slot_idx):
        tmp_pass = c_enc(ADMIN_SESSION_PIN)
        self.api.NK_erase_totp_slot(slot_idx, tmp_pass)

        # (uint8_t slot_number, const char *temporary_password)
        # NK_get_hotp_code_PIN(uint8_t slot_number, const char *user_temporary_password);


class PasswordSlots(BaseSlots):
    pass
# /**
#  * Enable password safe access
#  * @param user_pin char[30] current user PIN
#  * @return command processing error code
#  */
# NK_C_API int NK_enable_password_safe(const char *user_pin);
#
# /**
#  * Get password safe slots' status
#      * The return value must be freed using NK_free_password_safe_slot_status.
#  * @return uint8_t[16] slot statuses - each byte represents one slot with 0 (not programmed) and 1 (programmed)
#  */
# NK_C_API uint8_t * NK_get_password_safe_slot_status();
#
#     /**
#      * Free a value returned by NK_get_password_safe_slot_status.  May be
#      * called with a NULL argument.
#      */
#     NK_C_API void NK_free_password_safe_slot_status(uint8_t* status);
#
# /**
#  * Get password safe slot name
#  * @param slot_number password safe slot number, slot_number<16
#  * @return slot name
#  */
# NK_C_API char *NK_get_password_safe_slot_name(uint8_t slot_number);
#
# /**
#  * Get password safe slot login
#  * @param slot_number password safe slot number, slot_number<16
#  * @return login from the PWS slot
#  */
# NK_C_API char *NK_get_password_safe_slot_login(uint8_t slot_number);
#
# /**
#  * Get the password safe slot password
#  * @param slot_number password safe slot number, slot_number<16
#  * @return password from the PWS slot
#  */
# NK_C_API char *NK_get_password_safe_slot_password(uint8_t slot_number);
#
# /**
#  * Write password safe data to the slot
#  * @param slot_number password safe slot number, slot_number<16
#  * @param slot_name char[11] name of the slot
#  * @param slot_login char[32] login string
#  * @param slot_password char[20] password string
#  * @return command processing error code
#  */
# NK_C_API int NK_write_password_safe_slot(uint8_t slot_number, const char *slot_name,
# 	const char *slot_login, const char *slot_password);
#
# /**
#  * Erase the password safe slot from the device
#  * @param slot_number password safe slot number, slot_number<16
#  * @return command processing error code
#  */
# NK_C_API int NK_erase_password_safe_slot(uint8_t slot_number);


# * @return Returns 1, if set unencrypted volume ro/rw pin type is User, 0 otherwise.
#	NK_C_API int NK_set_unencrypted_volume_rorw_pin_type_user();

########### STORAGE
# NK_C_API NK_unlock_encrypted_volume(const char* user_pin);
# NK_C_API NK_lock_encrypted_volume();
# NK_C_API NK_unlock_hidden_volume(const char* hidden_volume_password);
# NK_C_API NK_lock_hidden_volume();
# NK_C_API NK_create_hidden_volume(uint8_t slot_nr, uint8_t start_percent, uint8_t end_percent, const char *hidden_volume_password);
# NK_C_API NK_set_unencrypted_read_only(const char *user_pin);
# NK_C_API NK_set_unencrypted_read_write(const char *user_pin);
# NK_C_API NK_set_unencrypted_read_only_admin(const char* admin_pin);
# NK_C_API NK_set_unencrypted_read_write_admin(const char* admin_pin);
# NK_C_API NK_set_encrypted_read_only(const char* admin_pin);
# NK_C_API NK_export_firmware(const char* admin_pin);
# NK_C_API NK_clear_new_sd_card_warning(const char* admin_pin);
# NK_C_API NK_fill_SD_card_with_random_data(const char* admin_pin);

# NK_C_API int NK_wink();

# ? NK_change_update_password(const char* current_update_password, const char* new_update_password);

# NK_get_progress_bar_value();#


#
# # For function parameters documentation please check NK_C_API.h
# assert libnitrokey.NK_write_config(255, 255, 255, False, True, ADMIN_TEMP.encode('ascii')) == DeviceErrorCode.STATUS_OK.value
# libnitrokey.NK_first_authenticate(ADMIN.encode('ascii'), ADMIN_TEMP.encode('ascii'))
# libnitrokey.NK_write_hotp_slot(1, 'python_test'.encode('ascii'), RFC_SECRET.encode('ascii'), 0, use_8_digits, False, False, "".encode('ascii'),
#                             ADMIN_TEMP.encode('ascii'))
# # RFC test according to: https://tools.ietf.org/html/rfc4226#page-32
# test_data = [
#     1284755224, 1094287082, 137359152, 1726969429, 1640338314, 868254676, 1918287922, 82162583, 673399871,
#     645520489,
# ]
# print('Getting HOTP code from Nitrokey Stick (RFC test, 8 digits): ')
# for i in range(10):
#     hotp_slot_1_code = get_hotp_code(libnitrokey, 1)
#     correct_str =  "correct!" if hotp_slot_1_code.decode('ascii') == str(test_data[i])[-8:] else  "not correct"
#     print('%d: %s, should be %s -> %s' % (i, hotp_slot_1_code.decode('ascii'), str(test_data[i])[-8:], correct_str))
# libnitrokey.NK_logout()  # disconnect device

if __name__ == "__main__":
    nkp = NitrokeyPro()
    print(nkp.connect())
    print(nkp.admin_auth("12345678"))
