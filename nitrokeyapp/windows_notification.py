import logging

# windows usb monitoring
# https://stackoverflow.com/questions/62601721/usb-hotplugging-callbacks-with-python-on-windows

logger = logging.getLogger(__name__)


class WindowsUSBNotification:
    from ctypes import Structure, c_ulong, c_ushort

    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEREMOVECOMPLETE = 0x8004
    WORD = c_ushort
    DWORD = c_ulong

    def __init__(self, detect_nk3, remove_nk3):
        # https://stackoverflow.com/questions/62601721/usb-hotplugging-callbacks-with-python-on-windows
        # windows
        import win32api
        import win32con
        import win32gui

        self.detect_nk3 = detect_nk3
        self.remove_nk3 = remove_nk3
        message_map = {win32con.WM_DEVICECHANGE: self.onDeviceChange}

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "DeviceChangeDemo"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(
            classAtom,
            "Device Change Demo",
            style,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            hinst,
            None,
        )

    def onDeviceChange(self, hwnd, msg, wparam, lparam):

        if wparam == self.DBT_DEVICEARRIVAL:
            logger.info("Something's arrived")
            self.detect_nk3()
        if wparam == self.DBT_DEVICEREMOVECOMPLETE:
            logger.info("Something's removed")
            self.remove_nk3()
            # self.tray.show()
            # self.tray.setToolTip("Nitrokey 3")
            # self.tray.showMessage("Nitrokey 3 connected!!!","Nitrokey 3 connected!!!!")

    class DEV_BROADCAST_HDR(Structure):
        from ctypes import c_ulong, c_ushort

        WORD = c_ushort
        DWORD = c_ulong
        _fields_ = [
            ("dbch_size", DWORD),
            ("dbch_devicetype", DWORD),
            ("dbch_reserved", DWORD),
        ]

    class DEV_BROADCAST_VOLUME(Structure):
        from ctypes import c_ulong, c_ushort

        WORD = c_ushort
        DWORD = c_ulong
        _fields_ = [
            ("dbcv_size", DWORD),
            ("dbcv_devicetype", DWORD),
            ("dbcv_reserved", DWORD),
            ("dbcv_unitmask", DWORD),
            ("dbcv_flags", WORD),
        ]
