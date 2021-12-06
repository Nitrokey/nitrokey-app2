from struct import pack, unpack, calcsize

from tqdm import tqdm
from zlib import crc32
from time import sleep
import traceback
import libusb1
import sys
import re

DFU_REQUEST_TYPE = libusb1.LIBUSB_TYPE_CLASS | \
    libusb1.LIBUSB_RECIPIENT_INTERFACE
DFU_DETACH = 0
DFU_DNLOAD = 1
DFU_UPLOAD = 2
DFU_GETSTATUS = 3
DFU_CLRSTATUS = 4
DFU_GETSTATE = 5
DFU_ABORT = 6

DFU_ST_SET_ADDRESS = 0x21
DFU_ST_ERASE_PAGE = 0x41

DFU_TIMEOUT = 5000 # from dfuse-dfu-util

DFU_STATUS_DICT = {
    0x00: 'No error condition is present.',
    0x01: 'File is not targeted for use by this device.',
    0x02: 'File is for this device but fails some vendor-specific '
        'verification test.',
    0x03: 'Device is unable to write memory.',
    0x04: 'Memory erase function failed.',
    0x05: 'Memory erase check failed.',
    0x06: 'Program memory function failed.',
    0x07: 'Programmed memory failed verification.',
    0x08: 'Cannot program memory due to received address that is our of '
        'range.',
    0x09: 'Received DFU_DNLOAD with wLength = 0, but device does not think it'
        'has all of the data yet.',
    0x0a: "Device's firmware is corrupt. It cannot return to run-time "
        "(non-DFU) operations.",
    0x0b: 'iString indicates a vendor-specific error.',
    0x0c: 'Device detected unexpected USB reset signaling.',
    0x0d: 'Device detected unexpected power on reset.',
    0x0e: 'Something went wrong, but the device does not know what is was.',
    0x0f: 'Device stalled a unexpected request.',
}

DFU_STATE_APP_IDLE = 0
DFU_STATE_APP_DETACH = 1
DFU_STATE_DFU_IDLE = 2
DFU_STATE_DFU_DNLOAD_SYNC = 3
DFU_STATE_DFU_DNBUSY = 4
DFU_STATE_DFU_DNLOAD_IDLE = 5
DFU_STATE_DFU_MANIFEST_SYNC = 6
DFU_STATE_DFU_MANIFEST = 7
DFU_STATE_DFU_MANIFEST_WAIT_RESET = 8
DFU_STATE_DFU_UPLOAD_IDLE = 9
DFU_STATE_DFU_ERROR = 10

DFU_CLASS = libusb1.LIBUSB_CLASS_APPLICATION
DFU_SUBCLASS = 0x01
DFU_CLASS_TUPPLE = (DFU_CLASS, DFU_SUBCLASS)
DFU_PROTOCOL_RUNTIME = 0x01
DFU_PROTOCOL_DFU_MODE = 0x02
DFU_DESCRIPTOR_LENGTH = 0x09
DFU_DESCRIPTOR_TYPE = 0x21
# For convenience
DFU_DESCRIPTOR_TYPE_STR = chr(DFU_DESCRIPTOR_TYPE)
DFU_ATTRIBUTE_WILL_DETACH = 1 << 3
DFU_ATTRIBUTE_MANIFESTATION_TOLERANT = 1 << 2
DFU_ATTRIBUTE_CAN_UPLOAD = 1 << 1
DFU_ATTRIBUTE_CAN_DOWNLOAD = 1
# 1.1a extension
DFU_ATTRIBUTE_ST_ACCELERATE = 1 << 7

# Parse non-repeating parts (use match). Can be rendered back with:
#  '@%(name)s/0x%(address)s/%(sectors)s' (without 'alias')
#  '@%(name)s/0x%(address)s-0x%(alias)s/%(sectors)s' (with 'alias')
DFU_ST_DEVICE_MAP_PATTERN = re.compile(r'^@(?P<name>[^/]*)/'
    '0x(?P<address>[^/-]+)(-0x(?P<alias>[^/]+))?/(?P<sectors>.*)')
# Parse a single sector (split on ',' and match on each chunk). Can be
# rendered back with:
#  '%(count)s*%(size)s%(unit)s%(mode)s' (and joined back with ',')
DFU_ST_DEVICE_MAP_SECTOR_PATTERN = re.compile(r'^(?P<count>[^*]+)\*'
    '(?P<size>[0-9]+)(?P<unit>.)(?P<mode>.)$')
DFU_ST_SECTOR_SIZE_UNIT_DICT = {
    'K': 1024,
    'M': 1024 * 1024,
}
DFU_ST_SECTOR_MODE_R = 1 # read
DFU_ST_SECTOR_MODE_E = 1 << 1 # erase
DFU_ST_SECTOR_MODE_W = 1 << 2 # write
# Exemples from DSO Nano v2 ("DS0201 Firmware Upgrade Ver 2.0",
# LIB v2.22, APP v2.40):
# '@Internal Flash  /0x08000000/12*001Ka,116*001Kg'
#   Name = 'Internal Flash  '
#   Base address = 0x8000000
#   Address alias = None
#   Block count = 128 (12 read + 116 read/erase/write)
#   Block size = 1kB
#   (total size: 128kB)
# '@SPI Flash : M25P64/0x00000000/64*064Kg,64*064Kg'
#   Name = 'SPI Flash : M25P64'
#   Base address = 0
#   Address alias = None
#   Block count = 128 (64 read/erase/write + 64 read/erase/write)
#   Block size = 64kB
#   (total size: 8MB)

class DoubleException(Exception):
    """
    Exception triggered, and attempt to recover triggered another exception.
    """
    def __init__(self, original, recovery):
        super(DoubleException, self).__init__()
        self.__original = original.replace('\n', '\n  ')
        self.__recovery = recovery.replace('\n', '\n  ')

    def __str__(self):
        return 'Double-exception: recovering from\n  %s\n triggered\n  %s' % (
            self.__original, self.__recovery)

class DFUError(Exception):
    pass

class DFUUnsupportedError(DFUError):
    """
    Device doesn't support this operation/feature.
    """
    pass

class DFUFormatError(DFUError):
    """
    This is not a DFU file.
    """
    pass

class DFUIncompatibleDevice(DFUError):
    """
    This DFU file is not for that device.
    """
    pass

class DFUDownloadError(DFUError):
    """
    Something bad happened during firmware download.
    Device might be half-briked (... or worse !).
    """
    pass

class DFUBadSate(DFUError):
    """
    Device is not in DFU idle state.
    """
    pass

class DFUDeviceReset(DFUError):
    """
    Device has been reset (as part of DFU normal procedure). Existing DFU
    instances for this device become unusable, application can destroy them,
    and may enumerate USB devices to find the device again.
    """
    pass

class DFUStatusError(DFUError):
    """
    Status check reported an error.
    """
    def __init__(self, status, timeout, state, status_message=None,
            extra=None):
        self.__status = status
        self.__timeout = timeout
        self.__state = state
        self.__status_message = status_message
        self.__extra = extra
        super(DFUStatusError, self).__init__()

    def getStatus(self):
        return self.__status

    def getTimeout(self):
        return self.__timeout

    def getState(self):
        return self.__state

    def getStatusMessage(self):
        message = self.__status_message
        if message is None:
            message = DFU_STATUS_DICT.get(self.__status, '(non-standard, '
                'non-described error)')
        return message

    def getExtra(self):
        return self.__extra

    def __str__(self):
        return 'Status error %s (%s), device entering state %s' % (
            self.__status, self.getStatusMessage(), self.__state)

def getDFUDescriptor(usb_device):
    """
    Retrieve and parse a DFU descriptor from given device.
    usb_device
        usb1.USBDevice instance.
        Device will not be opened by this function.
    Returns a 6-tuple:
        - attribute bitmask (see DFU_ATTRIBUTE_*)
        - detach timeout (in ms)
        - transfer size (in bytes)
        - version number
        - protocol (see DFU_PROTOCOL_*)
        - USB interface number
        - a list of usb descriptors for each DFU alternate setting on device
          Useful for STM extension.
    """
    found = False
    descriptor_list = []
    append = descriptor_list.append
    print (usb_device)
    for setting in usb_device.iterSettings():
        if setting.getClassTupple() == DFU_CLASS_TUPPLE:
            found = True
            append(setting.getDescriptor())
    if not found:
        raise DFUUnsupportedError("This device doesn't support DFU")
    for extra in setting.getExtra():
        if True or extra[1] == DFU_DESCRIPTOR_TYPE_STR:
            break
    else:
        raise ValueError('Inconsistent USB descriptor: last DFU '
            'interface has no DFU descriptor')
    return  unpack('<BHHH', extra[2:]) + (setting.getProtocol(),
        setting.getNumber(), descriptor_list)

def _getNextSTMBlockNumber(blocknum=None):
    if blocknum is None:
        return 2
    if blocknum < 2:
        raise ValueError('Block number %i reserved by STM '
            'extensions' % (blocknum, ))
    else:
        # wrap 0xffff to 2, otherwise increment by 1
        return (blocknum - 1) % 0xfffe + 2

def _getNextStandardBlockNumber(blocknum=None):
    if blocknum is None:
        return 0
    else:
        return (blocknum + 1) & 0xffff

class DFUProtocol(object):
    __interface = None

    def __init__(self, handle):
        """
        handle (USBDeviceHandle)
        """
        self.__handle = handle
        self.__attributes, self.__detach_timeout, self.__transfer_size, \
            dfu_version, self.__protocol, iface, descriptor_list = \
            getDFUDescriptor(handle.getDevice())
        self.__interface = iface
        self.__dfu_version = dfu_version
        # From STM documentation UM0392, page 10
        self.__has_stm_extensions = has_stm_extensions = \
            0x11a <= dfu_version < 0x120
        self.getNextBlockNumber = has_stm_extensions and \
            _getNextSTMBlockNumber or _getNextStandardBlockNumber
        self.__descriptor_list = [handle.getASCIIStringDescriptor(x) \
            for x in descriptor_list]
        handle.claimInterface(iface)

    def __del__(self):
        pass

    def _controlWrite(self, request, value, data='', timeout=DFU_TIMEOUT):
        self.__handle.controlWrite(DFU_REQUEST_TYPE, request, value,
                self.__interface, data, timeout=timeout)

    def _controlRead(self, request, value, length, timeout=DFU_TIMEOUT):
        return self.__handle.controlRead(DFU_REQUEST_TYPE, request, value,
                self.__interface, length, timeout=timeout)

    def hasSTMExtensions(self):
        return self.__has_stm_extensions

    def willDetach(self):
        return bool(self.__attributes & DFU_ATTRIBUTE_WILL_DETACH)

    def isManifestationTolerant(self):
        return bool(self.__attributes & DFU_ATTRIBUTE_MANIFESTATION_TOLERANT)

    def canUpload(self):
        return bool(self.__attributes & DFU_ATTRIBUTE_CAN_UPLOAD)

    def canDownload(self):
        return bool(self.__attributes & DFU_ATTRIBUTE_CAN_DOWNLOAD)

    def STM_canAccelerate(self):
        if not self.__has_stm_extensions:
            raise DFUUnsupportedError('This device lacks STM extensions')
        return bool(self.__attributes & DFU_ATTRIBUTE_ST_ACCELERATE)

    def STM_getDeviceMappingList(self):
        """
        Return device's mappings.
        Notes:
        - sector modes are a bitmask of
          DFU_ST_SECTOR_MODE_R (read)
          DFU_ST_SECTOR_MODE_E (erase)
          DFU_ST_SECTOR_MODE_W (write)
          ...and possibly other values (namely 0x60, probably to get an ascii
          representation which doesn't conflict with format special tokens)
        - consecutive identical (same block size, same mode) sectors are merged
        - If any unexpected format is encountered, ValueError is raised
          (please report)
        Example:
          Device with 2 alternate settings, with descriptors
            '@Internal Flash  /0x08000000/12*001Ka,116*001Kg'
            '@SPI Flash : M25P64/0x00000000/64*064Kg,64*064Kg'
          Result:
            [{'address': 0x8000000,
              'alias': None,
              'name': 'Internal Flash  ',
              'sectors': [{'count': 12, 'mode': 0x61, 'size': 1024},
                          {'count': 116, 'mode': 0x67, 'size': 1024}]},
             {'address': 0,
              'alias': None,
              'name': 'SPI Flash : M25P64',
              'sectors': [{'count': 128, 'mode': 0x67, 'size': 65536}]}]
        """
        if not self.__has_stm_extensions:
            raise DFUUnsupportedError('This device lacks STM extensions')
        result = []
        append = result.append
        for descriptor in self.__descriptor_list:
            entry = DFU_ST_DEVICE_MAP_PATTERN.match(descriptor)
            if entry is None:
                raise ValueError('Unexpected descriptor: %s' % (descriptor, ))
            entry = entry.groupdict()
            sector_list = entry['sectors'].split(',')
            if len(sector_list) == 0:
                raise ValueError('Empty sector list: %s' % (descriptor, ))
            parsed_sector_list = []
            sector_append = parsed_sector_list.append
            last_sector = None
            for sector in sector_list:
                sector = DFU_ST_DEVICE_MAP_SECTOR_PATTERN.match(sector)
                if sector is None:
                    raise ValueError('Unexpected sector: %s' % (sector, ))
                sector = sector.groupdict()
                unit = sector['unit']
                unit_factor = DFU_ST_SECTOR_SIZE_UNIT_DICT.get(unit)
                if unit_factor is None:
                    raise ValueError('Unexpected sector unit: %s' % (unit, ))
                size = int(sector['size']) * unit_factor
                mode = ord(sector['mode'])
                count = int(sector['count'])
                if last_sector is not None and last_sector['size'] == size \
                        and last_sector['mode'] == mode:
                    # Same settings as previous sector description, merge
                    last_sector['count'] += count
                else:
                    sector = {
                        'size': size,
                        'mode': mode,
                        'count': count,
                    }
                    last_sector = sector
                    sector_append(sector)
            if entry['alias'] is None:
                alias = None
            else:
                alias = int(entry['alias'], 16)
            append({
                'name': entry['name'],
                'address': int(entry['address'], 16),
                'alias': alias,
                'sectors': parsed_sector_list,
            })
        return result

    def _STM_specialOperation(self, data):
        if not self.__has_stm_extensions:
            raise DFUUnsupportedError('This device lacks STM extensions')
        self._controlWrite(DFU_DNLOAD, 0, data)
        self.checkStatus()
        self.abort()

    def STM_setAddress(self, address):
        self._STM_specialOperation(pack('<BI', DFU_ST_SET_ADDRESS, address))

    def STM_erasePage(self, address):
        self._STM_specialOperation(pack('<BI', DFU_ST_ERASE_PAGE, address))

    #def STM_getSupportedOperations(self):
    #    """
    #    Pure guessing. Meaning unknown.
    #    Returns '\x00\x21\x41' on a DSO Nano v2.
    #    Meaning of '\x00' unknown.
    #    """
    #    if not self.__has_stm_extensions:
    #        raise DFUUnsupportedError('This device lacks STM extensions')
    #    result = self._controlRead(DFU_UPLOAD, 0, self.__transfer_size)
    #    self.checkStatus()
    #    self.abort()
    #    return result

    #def STM_enterWeirdState(self):
    #    """
    #    After running this, device enters non-standard state 0xe and
    #    libusb reports a pipe error.
    #    Obviously, you should refrain from using this if you care for your
    #    device.
    #    """
    #    if not self.__has_stm_extensions:
    #        raise DFUUnsupportedError('This device lacks STM extensions')
    #    result = self._controlRead(DFU_UPLOAD, 1, self.__transfer_size)
    #    self.checkStatus()
    #    self.abort()
    #    return result

    def getDetachTimeout(self):
        return self.__detach_timeout

    def getTransferSize(self):
        return self.__transfer_size

    def getDFUVersion(self):
        return self.__dfu_version

    def getProtocol(self):
        """
        DFU_PROTOCOL_RUNTIME if device is runing in firmware mode.
        DFU_PROTOCOL_DFU_MODE is device is running in DFU mode.
        """
        return self.__protocol

    def getInterface(self):
        return self.__interface

    def detach(self, timeout=None):
        if timeout is None:
            timeout = self.__detach_timeout
        elif timeout > self.__detach_timeout:
            raise ValueError('Timeout too large for this device.')
        self._controlWrite(DFU_DETACH, timeout)

    def getNextBlockNumber(self, blocknum=None):
        """
        Convenience function to compute the next block number.
        This is needed because of STM extensions giving a special meaning to
        block numbers 0 and 1.
        """
        # Overloaded on instance during __init__ call.
        raise NotImplementedError

    def download(self, firmware, blocknum=None):
        blocknum = self.getNextBlockNumber(blocknum)
        if self.__has_stm_extensions and blocknum < 2:
            raise ValueError('download must not be called with blocknum < 2 '
                'on devices supporting STM extensions')
        self._controlWrite(DFU_DNLOAD, blocknum, firmware)
        self.checkStatus()
        while True:
            state = self.getState()
            # print (state)
            assert state in (
                    DFU_STATE_DFU_DNLOAD_SYNC,
                    DFU_STATE_DFU_DNLOAD_IDLE,
                    DFU_STATE_DFU_DNBUSY,
                    DFU_STATE_DFU_MANIFEST_SYNC,
                ), state
            status, timeout, state, _ = self.getStatus()
            if status:
                # XXX: Is there something smarter to do upon error ?
                raise DFUDownloadError(status)
            if state == DFU_STATE_DFU_ERROR:
                # XXX: Is there something smarter to do upon error ?
                self.clearStatus()
                raise DFUDownloadError('Error status')
            if state in (
                        DFU_STATE_DFU_DNLOAD_IDLE, # more to download
                        DFU_STATE_DFU_MANIFEST, # download over (data == '')
                        DFU_STATE_DFU_IDLE, # download over and manifest over
                    ):
                break
            sleep(timeout / 1000)
        return blocknum

    def upload(self, length, blocknum=None):
        blocknum = self.getNextBlockNumber(blocknum)
        if self.__has_stm_extensions and blocknum < 2:
            raise ValueError('upload must not be called with blocknum < 2 '
                'on devices supporting STM extensions')
        try:
            result = self._controlRead(DFU_UPLOAD, blocknum, length)
            self.checkStatus()
        except Exception:
            exc_info = sys.exc_info()
            try:
                self.abort()
            except Exception:
                raise DoubleException(
                    ''.join(traceback.format_exception(*exc_info)),
                    traceback.format_exc())
            raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
        return result, blocknum

    def getStatus(self):
        status, timeout, timeout_upper, state, status_descriptor = unpack(
            '<BBHBB', self._controlRead(DFU_GETSTATUS, 0, 6))
        timeout |= timeout_upper << 8
        return status, timeout, state, status_descriptor

    def checkStatus(self):
        status, timeout, state, status_descriptor = self.getStatus()
        if status:
            try:
                status_message = self.__handle.getASCIIStringDescriptor(
                    status_descriptor)
            except Exception:
                extra = traceback.format_exc()
                status_message = None
            else:
                extra = None
            raise DFUStatusError(status, timeout, state, status_message,
                extra)

    def clearStatus(self):
        self._controlWrite(DFU_CLRSTATUS, 0, 0)

    def getState(self):
        return ord(self._controlRead(DFU_GETSTATE, 0, 1))

    def abort(self):
        self._controlWrite(DFU_ABORT, 0, 0)
        self.checkStatus()

DFU_SUFFIX_BASE_FORMAT = '<3sBI' # In file order !
DFU_SUFFIX_BASE_LENGTH = calcsize(DFU_SUFFIX_BASE_FORMAT)
if calcsize('I') != 4:
    raise NotImplementedError('Unsupported architecture')
# field name, format (In reverse file order !)[, length]
# (length is computed automatically, se below)
DFU_SUFFIX_FIELD_LIST = [
    ['dfu_version', 'H'],
    ['vendor', 'H'],
    ['product', 'H'],
    ['device', 'H'],
]
DFU_STM_PREFIX_FIELD_LIST = [
    ['dfuse_magic', '4s'],
    ['dfuse_version', 'B'],
    ['image_size', '>I'],
    ['target_count', 'B'],
]
DFU_STM_TARGET_PREFIX_FIELD_LIST = [
    ['magic', '6s'],
    ['alt_setting', 'B'],
    ['target_named', '>I'],
    ['target_name', '255s'],
    ['target_size', '>I'],
    ['element_count', '>I'],
]
DFU_STM_ELEMENT_PREFIX_FIELD_LIST = [
    ['address', '>I'],
    ['size', '>I'],
]
def _completeFieldLists():
    dfu_suffix_set = set()
    for field_list in (DFU_SUFFIX_FIELD_LIST, DFU_STM_PREFIX_FIELD_LIST,
            DFU_STM_TARGET_PREFIX_FIELD_LIST,
            DFU_STM_ELEMENT_PREFIX_FIELD_LIST):
        for field in field_list:
            field_name = field[0]
            if field_name in dfu_suffix_set:
                raise ValueError('Dulpicate field name: ' + field_name)
            dfu_suffix_set.add(field_name)
            field.append(calcsize(field[1]))
_completeFieldLists()
del _completeFieldLists
DFU_STM_PREFIX_LENGTH = sum(x[2] for x in DFU_STM_PREFIX_FIELD_LIST)
DFU_STM_TARGET_PREFIX_LENGTH = sum(
    x[2] for x in DFU_STM_TARGET_PREFIX_FIELD_LIST)
DFU_STM_ELEMENT_PREFIX_LENGTH = sum(
    x[2] for x in DFU_STM_ELEMENT_PREFIX_FIELD_LIST)
def _parseFieldList(data, field_list):
    result = {}
    for name, fmt, length in field_list:
        result[name] = unpack(fmt, data[:length])[0]
        data = data[length:]
        if not data:
            break
    return result
def _generateFieldList(data_dict, field_list):
    return pack(''.join(x[1] for x in field_list),
        *[data_dict[x[0]] for x in field_list])

class DFU(object):
    def __init__(self, handle):
        self.__handle = handle
        self.__dfu_interface = DFUProtocol(handle)

    def startDFU(self):
        self.__dfu_interface.detach()
        self._reset('Switching to DFU mode.')

    def _reset(self, reason):
        self.__handle.resetDevice()
        raise DFUDeviceReset(reason)

    def download(self, data):
        iface = self.__dfu_interface
        if not iface.canDownload():
            raise DFUUnsupportedError('Cannot download')
        state = iface.getState()
        if state == DFU_STATE_DFU_ERROR:
            # TODO: handle properly (we shouldn't start with an error state)
            iface.clearStatus()
            state = iface.getState()
        if state != DFU_STATE_DFU_IDLE:
            raise DFUBadSate(state)

        self._download(data)
        try:
            self._download(b'')
        except Exception as e:
            print (e)

        try:
            if not iface.isManifestationTolerant():
                self._reset('Download complete.')
        except Exception as e:
            print (e)

        return "Finished"

    def _download(self, data):
        iface = self.__dfu_interface
        download = iface.download
        transfer_size = iface.getTransferSize()
        blocknum = None
        iterations = len(data) // transfer_size + 1
        tqdm_disable = iterations < 10
        if not tqdm_disable:
            print("Download started")
        for i in tqdm(range(iterations), disable=tqdm_disable):
            if not data:
                continue
            blocknum = download(data[:transfer_size], blocknum)
            data = data[transfer_size:]
        if not tqdm_disable:
            print("Download Finished")

    def upload(self, vendor_specific=True, product_specific=True,
            version=0xffff, stm_format=False):
        iface = self.__dfu_interface
        if not iface.canUpload():
            raise DFUUnsupportedError('Cannot upload')
        state = iface.getState()
        if state == DFU_STATE_DFU_ERROR:
            # TODO: handle properly (we shouldn't start with an error state)
            iface.clearStatus()
            state = iface.getState()
        if state != DFU_STATE_DFU_IDLE:
            raise DFUBadSate(state)
        result = ''
        iface_upload = iface.upload
        transfer_size = iface.getTransferSize()
        checkStatus = iface.checkStatus
        abort = iface.abort
        if stm_format and iface.hasSTMExtensions():
            # Untested/unfinished code ahead, raise.
            raise NotImplementedError
            # TODO: create a valid DfuSe file.
            setAddress = iface.STM_setAddress
            for chunk in iface.STM_getDeviceMappingList():
                setAddress(chunk['address'])
                blocknum = None
                for sector in chunk['sectors']:
                    if not sector['mode'] & DFU_ST_SECTOR_MODE_R:
                        continue
                    remain = sector['count'] * sector['size']
                    while len(result) < remain:
                        data, blocknum = iface_upload(min(transfer_size,
                            remain), blocknum)
                        checkStatus()
                        result += data
                    assert remain == len(result), (remain, len(result))
                    abort()
        else:
            blocknum = None
            while True:
                data, blocknum = iface_upload(transfer_size, blocknum)
                result += data
                if len(data) < transfer_size:
                    break
            abort()
        # Add defuse tail
        device = self.__handle.getDevice()
        tail = _generateFieldList({
            'dfu_version': 0x110,
            'vendor': vendor_specific and device.getVendorID() or 0xffff,
            'product': product_specific and device.getProductID() or 0xffff,
            'device': version,
        }, DFU_SUFFIX_FIELD_LIST)
        data += ''.join(reversed(tail)) + 'UFD' + \
            chr(len(tail) + DFU_SUFFIX_BASE_LENGTH)
        data += pack('<I', crc32(data))
        return data

