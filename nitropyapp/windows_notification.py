##### windows usb monitoring 
# https://stackoverflow.com/questions/62601721/usb-hotplugging-callbacks-with-python-on-windows

class WindowsUSBNotification():
    from ctypes import Structure, c_ulong, c_ushort
    #
    # Device change events (WM_DEVICECHANGE wParam)
    #
    DBT_DEVICEARRIVAL = 0x8000
    DBT_DEVICEQUERYREMOVE = 0x8001
    DBT_DEVICEQUERYREMOVEFAILED = 0x8002
    DBT_DEVICEMOVEPENDING = 0x8003
    DBT_DEVICEREMOVECOMPLETE = 0x8004
    DBT_DEVICETYPESSPECIFIC = 0x8005
    DBT_CONFIGCHANGED = 0x0018

    #
    # type of device in DEV_BROADCAST_HDR
    #
    DBT_DEVTYP_OEM = 0x00000000
    DBT_DEVTYP_DEVNODE = 0x00000001
    DBT_DEVTYP_VOLUME = 0x00000002
    DBT_DEVTYPE_PORT = 0x00000003
    DBT_DEVTYPE_NET = 0x00000004

    #
    # media types in DBT_DEVTYP_VOLUME
    #
    DBTF_MEDIA = 0x0001
    DBTF_NET = 0x0002

    WORD = c_ushort
    DWORD = c_ulong
    
    def __init__(self, detect_nk3):
        # https://stackoverflow.com/questions/62601721/usb-hotplugging-callbacks-with-python-on-windows
        # windows
        import win32api
        import win32con
        import win32gui

        self.detect_nk3 =detect_nk3
        message_map = {
            win32con.WM_DEVICECHANGE: self.onDeviceChange
        }

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
            0, 0,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0,
            hinst, None
        )
       
    def onDeviceChange(self, hwnd, msg, wparam, lparam):
        #
        # WM_DEVICECHANGE:
        #  wParam - type of change: arrival, removal etc.
        #  lParam - what's changed?
        #    if it's a volume then...
        #  lParam - what's changed more exactly
        #
        dev_broadcast_hdr = self.DEV_BROADCAST_HDR.from_address(lparam)

        if wparam == self.DBT_DEVICEARRIVAL:
            print("Something's arrived")
            self.detect_nk3()
            #self.tray.show() 
            #self.tray.setToolTip("Nitrokey 3")
            #self.tray.showMessage("Nitrokey 3 connected!!!","Nitrokey 3 connected!!!!")
            if dev_broadcast_hdr.dbch_devicetype ==  self.DBT_DEVTYP_VOLUME:
                print("It's a volume!")

                dev_broadcast_volume =  self.DEV_BROADCAST_VOLUME.from_address(lparam)
                if dev_broadcast_volume.dbcv_flags &  self.DBTF_MEDIA:
                    print("with some media")
                    drive_letter = self.drive_from_mask(dev_broadcast_volume.dbcv_unitmask)
                    print("in drive", chr(ord("A") + drive_letter))

                return 1
    ################# more stuff for usb monitoring windows 
    def drive_from_mask(mask):
        n_drive = 0
        while 1:
            if (mask & (2 ** n_drive)):
                return n_drive
            else:
                n_drive += 1
        
    
    class DEV_BROADCAST_HDR(Structure):
        from ctypes import c_ulong, c_ushort
        WORD = c_ushort
        DWORD = c_ulong
        _fields_ = [
            ("dbch_size", DWORD),
            ("dbch_devicetype", DWORD),
            ("dbch_reserved", DWORD)
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
            ("dbcv_flags", WORD)
        ]