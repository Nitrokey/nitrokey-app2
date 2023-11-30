import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WindowsUSBNotifi:
    from ctypes import Structure, c_ulong, c_ushort

    WORD = c_ushort
    DWORD = c_ulong

    def __init__(
        self, detect_nk3: Callable[[], None], remove_nk3: Callable[[], None]
    ) -> None:
        import win32api
        import win32con
        import win32gui

        self.detect_nk3 = detect_nk3
        self.remove_nk3 = remove_nk3
        message_map = {win32con.WM_DEVICECHANGE: self.onDeviceChange}

        winclass = win32gui.WNDCLASS()
        hinst = winclass.hInstance = win32api.GetModuleHandle(None)
        winclass.lpszClassName = "DeviceChange"
        winclass.lpfnWndProc = message_map
        reg_window = win32gui.RegisterClass(winclass)

        self.hwnd = win32gui.CreateWindow(
            reg_window,
            "Device Change",
            win32con.WS_ICONIC,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            hinst,
            None,
        )
        win32gui.UpdateWindow(self.hwnd)

    def onDeviceChange(self, hwnd: Any, msg: Any, wparam: int, lparam: Any) -> int:
        import win32con

        if wparam == win32con.DBT_DEVICEARRIVAL:
            logger.info("Windows: USB added")
            self.detect_nk3()
        if wparam == win32con.DBT_DEVICEREMOVECOMPLETE:
            logger.info("Windows: USB removed")
            self.remove_nk3()
        return 0

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
