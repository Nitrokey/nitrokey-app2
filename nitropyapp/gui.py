
# use "pbs" for packaging...
# pip-run -> pyqt5
# pip-dev -> pyqt5-stubs

import sys
import os
from pathlib import Path
from queue import Queue

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject

import nitropyapp.libnk as nk_api

#pyrcc5 -o gui_resources.py ui/resources.qrc
import nitropyapp.gui_resources


#import pysnooper
#@pysnooper.snoop


class BackendThread(QThread):
    hello = pyqtSignal()

    job_q = Queue()

    def __del__(self):
        self.wait()

    def add_job(self, signal, func, *f_va, **f_kw):
        self.job_q.put((signal, func, f_va, f_kw))

    def stop_loop(self):
        self.add_job(None, None)

    def run(self):
        self.hello.emit()
        while True:
            # blocking job-wait-loop
            job = self.job_q.get()
            if job is None:
                continue
            signal, func, vargs, kwargs = job

            # func == None means stop/end thread asap!
            if func is None:
                break

            # eval `func`, emit signal with results
            res = func(*vargs, **kwargs)
            signal.emit(res or {})

########################################################################################
########################################################################################
########################################################################################
########################################################################################
# Define function to import external files when using PyInstaller.
# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     try:
#         # PyInstaller creates a temp folder and stores path in _MEIPASS
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#
#     return os.path.join(base_path, relative_path)


# Import .ui forms for the GUI using function resource_path()
#securitySearchForm = resource_path("securitySearchForm.ui")
#popboxForm = resource_path("popbox.ui")

#Ui_MainWindow, QtBaseClass = uic.loadUiType(securitySearchForm)
#Ui_PopBox, QtSubClass = uic.loadUiType(popboxForm)

#pyrcc4 -py3 resources.qrc -o resources_rc.py
########################################################################################
########################################################################################
########################################################################################
########################################################################################


class QtUtilsMixIn:
    # singleton backend-thread
    backend_thread = None

    def __init__(self):
        self.widgets = {}

        # ensure we are always mixed-in with an QObject-ish class
        assert isinstance(self, QObject)

    @classmethod
    def connect_signal_slots(cls, slot, signal, res_slots, func, *va, **kw):
        """
        Signal to Slot connection helper for functions to be executed inside
        the BackgroundThread.

        slot: the event to bind to (e.g., a clicked button)
        signal: the `signal` to be emitted once the `func` returns its results
        res_slots: list-of-slots to be connected to the `signal`
        func: function to be run inside the BackgroundThread, with *va & **kw passed
        """
        for res_slot in res_slots:
            signal.connect(res_slot)
        _func = lambda: cls.backend_thread.add_job(signal, func, *va, **kw)
        return slot.connect(_func)

    def user_warn(self, msg, title=None, parent=None):
        QtWidgets.QMessageBox.warning(parent or self, title or msg, msg)
    def user_info(self, msg, title=None, parent=None):
        QtWidgets.QMessageBox.information(parent or self, title or msg, msg)
    def user_err(self, msg, title=None, parent=None):
        QtWidgets.QMessageBox.critical(parent or self, title or msg, msg)


    def get_widget(self, qt_cls, name=""):
        """while finding widgets, why not cache them into a map"""
        widget = self.widgets.get(name)
        if not widget:
            # ensure `self` will always be mixed-in with a QObject derived class
            assert isinstance(self, QObject)
            widget = self.findChild(qt_cls, name)
            self.widgets[name] = widget
        return widget

    def apply_by_name(self, names, func):
        """expects only known widget-names (`name` in `self.widgets`)"""
        for name in names:
            func(self.widgets[name])

    def set_enabled(self, cls, names, enable):
        # @todo: replace with 'apply_by_name'
        for name in names:
            self.get_widget(cls, name).setEnabled(enable)

    def set_visible(self, cls, names, visible):
        # @todo: replace with 'apply_by_name'
        for name in names:
            self.get_widget(cls, name).setVisible(visible)

    def load_ui(self, filename, qt_obj):
        uic.loadUi(filename, qt_obj)
        return True

    # def set_layout_visible(self, cls, obj_name, visible=True):
    #     to_hide = [(cls, obj_name)]
    #     cur = to_hide.pop()
    #     while cur:
    #         cur_cls, cur_name = cur
    #         widget = self.findChild(cur_cls, cur_name)
    #         if cls in [QtWidgets.QHBoxLayout, QtWidgets.QVBoxLayout]:
    #             for idx in range(widget.count()):
    #                 obj = widget.itemAt(idx).widget()
    #                 if obj:
    #                     to_hide.append((obj.__class__, obj.objectName()))
    #         else:
    #             widget.setVisible(visible)
    #         cur = to_hide.pop(0)


##### @fixme: PINDialog should be modal!
class PINDialog(QtUtilsMixIn, QtWidgets.QDialog):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QDialog.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.app = qt_app

        self.checkbox, self.ok_btn, self.line_edit = None, None, None
        self.status, self.title = None, None
        self.ok_signal, self.tries_left = None, None

        self.opts = {}

    def init_gui(self):
        self.checkbox = self.get_widget(QtWidgets.QCheckBox, "checkBox")
        self.checkbox.stateChanged.connect(self.checkbox_toggled)

        self.ok_btn = self.get_widget(QtWidgets.QPushButton, "okButton")
        self.ok_btn.clicked.connect(self.ok_clicked)

        self.line_edit = self.get_widget(QtWidgets.QLineEdit, "lineEdit")
        self.status = self.get_widget(QtWidgets.QLabel, "status")
        self.title = self.get_widget(QtWidgets.QLabel, "label")

        self.reset()

    @pyqtSlot()
    def reset(self):
        self.status.setText("")
        self.title.setText("")
        self.ok_signal, self.tries_left = None, None
        self.line_edit.setText("")
        self.checkbox.setCheckState(0)
        self.opts = {}
        self.hide()

    @pyqtSlot(dict)
    def invoke(self, opts):
        self.opts = dct = opts

        self.tries_left = dct.get("retries", 0)
        who = dct.get("who")
        if self.tries_left == 0:
            self.user_warn(f"Please reset the {who} pin counter before continuing",
                           "No attempts left")
            self.reset()
            return

        self.status.setText(f"Attempts left: {self.tries_left}")
        self.title.setText(dct.get("title", self.title.text()))
        self.ok_signal = dct.get("sig")
        self.show()

    @pyqtSlot(int)
    def checkbox_toggled(self, state):
        if state == 0:
            self.line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 2:
            self.line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)

    @pyqtSlot()
    def ok_clicked(self):
        pin = self.line_edit.text()
        def_pin = self.opts.get("default", "(?)")
        # @fixme: get len-range from libnk.py
        if len(pin) < 6 or len(pin) > 20:
            self.line_edit.selectAll()
            self.user_warn("The pin requires to be 6-20 chars in length\n"
                f"default: {def_pin}", "Invalid PIN")
        else:
            self.ok_signal.emit(self.opts, pin)


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):

    sig_connected = pyqtSignal(dict)
    sig_disconnected = pyqtSignal()
    sig_lock = pyqtSignal(dict)

    sig_ask_pin = pyqtSignal(dict)
    sig_auth = pyqtSignal(dict, str)
    sig_confirm_auth = pyqtSignal(str)

    sig_status_upd = pyqtSignal(dict)

    sig_unlock_pws = pyqtSignal(dict)
    sig_unlock_hv = pyqtSignal(dict)
    sig_unlock_ev = pyqtSignal(dict)

    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QMainWindow.__init__(self)
        QtUtilsMixIn.__init__(self)

        self.app = qt_app

        self.backend_thread.hello.connect(self.backend_cb_hello)
        self.backend_thread.start()

        ################################################################################
        # load UI-files and prepare them accordingly
        ui_dir = Path(__file__).parent.resolve().absolute() / "ui"
        ui_files = {
            "main": (ui_dir / "mainwindow.ui").as_posix(),
            "pin": (ui_dir / "pindialog.ui").as_posix()
        }

        self.load_ui(ui_files["main"], self)

        self.pin_dialog = PINDialog(qt_app)
        self.pin_dialog.load_ui(ui_files["pin"], self.pin_dialog)
        self.pin_dialog.init_gui()

        _get = self.get_widget
        _qt = QtWidgets

        ################################################################################
        #### get widget objects
        ## app wide widgets
        self.status_bar = _get(_qt.QStatusBar, "statusBar")
        self.menu_bar = _get(_qt.QMenuBar, "menuBar")
        self.tabs = _get(_qt.QTabWidget, "tabWidget")
        self.tab_overview = _get(_qt.QWidget, "tab_5")
        self.tab_otp_conf = _get(_qt.QWidget, "tab")
        self.tab_otp_gen = _get(_qt.QWidget, "tab_2")
        self.tab_pws = _get(_qt.QWidget, "tab_3")
        self.tab_settings = _get(_qt.QWidget, "tab_4")

        ## overview buttons
        self.quit_button = _get(_qt.QPushButton, "btn_dial_quit")
        self.help_btn = _get(_qt.QPushButton, "btn_dial_help")
        self.lock_btn = _get(_qt.QPushButton, "btn_dial_lock")
        self.unlock_pws_btn = _get(_qt.QPushButton, "btn_dial_PWS")

        # OTP widgets
        self.radio_hotp = _get(_qt.QRadioButton, "radioButton")
        self.radio_totp = _get(_qt.QRadioButton, "radioButton_2")
        self.otp_combo_box = _get(_qt.QComboBox, "slotComboBox")
        self.otp_name = _get(_qt.QLineEdit, "nameEdit")
        self.otp_len_label = _get(_qt.QLabel, "label_5")
        self.otp_erase_btn = _get(_qt.QPushButton, "eraseButton")
        self.otp_save_btn = _get(_qt.QPushButton, "writeButton")
        self.otp_cancel_btn = _get(_qt.QPushButton, "cancelButton")
        self.otp_secret = _get(_qt.QLineEdit, "secretEdit")
        self.otp_secret_type_b32 = _get(_qt.QRadioButton, "base32RadioButton")
        self.otp_secret_type_hex = _get(_qt.QRadioButton, "hexRadioButton")
        self.otp_gen_len = _get(_qt.QSpinBox, "secret_key_generated_len")
        self.otp_gen_secret_btn = _get(_qt.QPushButton, "randomSecretButton")
        self.otp_gen_secret_clipboard_btn = _get(_qt.QPushButton, "btn_copyToClipboard")
        self.otp_gen_secret_hide = _get(_qt.QCheckBox, "checkBox")

        ################################################################################
        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WA_DeleteOnClose)

        #self.tabs.setCurrentIndex(0)
        self.tabs.setCurrentWidget(self.tab_overview)
        self.tabs.currentChanged.connect(self.slot_tab_changed)

        self.init_gui()
        self.show()

        self.device = None

        ################################################################################
        # app wide callbacks
        self.quit_button.clicked.connect(self.slot_quit_button_pressed)
        self.lock_btn.clicked.connect(self.slot_lock_button_pressed)
        self.unlock_pws_btn.clicked.connect(self.unlock_pws_button_pressed)

        ################################################################################
        #### connections for functional signals
        ## generic / global
        self.connect_signal_slots(self.help_btn.clicked, self.sig_connected,
            [self.job_nk_connected, self.slot_toggle_otp], self.job_connect_device)

        self.sig_status_upd.connect(self.update_status_bar)
        self.sig_disconnected.connect(self.init_gui)

        ## otp stuff
        self.radio_totp.toggled.connect(self.slot_toggle_otp)
        self.radio_hotp.toggled.connect(self.slot_toggle_otp)

        self.otp_combo_box.currentIndexChanged.connect(self.slot_select_otp)
        self.otp_erase_btn.clicked.connect(self.slot_erase_otp)
        self.otp_cancel_btn.clicked.connect(self.slot_cancel_otp)
        self.otp_save_btn.clicked.connect(self.slot_save_otp)

        self.otp_secret.textChanged.connect(self.slot_otp_save_enable)
        self.otp_name.textChanged.connect(self.slot_otp_save_enable)

        self.otp_gen_secret_btn.clicked.connect(self.slot_random_secret)
        self.otp_gen_secret_hide.stateChanged.connect(self.slot_secret_hide)

        ## auth related
        self.sig_ask_pin.connect(self.pin_dialog.invoke)
        self.sig_auth.connect(self.slot_auth)
        self.sig_confirm_auth.connect(self.slot_confirm_auth)

        self.sig_lock.connect(self.slot_lock)

    #### helper
    def get_active_otp(self):
        who = "totp" if self.radio_totp.isChecked() else "hotp"
        idx = self.otp_combo_box.currentIndex()
        return who, idx, self.device.TOTP if who == "totp" else self.device.HOTP,

    def ask_pin(self, who):
        assert who in ["user", "admin"]
        who_cap = who.capitalize()
        dct = dict(
                title=f"{who_cap} PIN:",
                retries=self.device.user_pin_retries if who == "user" else
                        self.device.admin_pin_retries,
                sig=self.sig_auth,
                default=self.device.default_user_pin if who == "user" else
                        self.device.default_admin_pin,
                who=who
        )

        self.sig_ask_pin.emit(dct)
        self.msg(f"need {who_cap} auth")
        return

    def msg(self, what):
        what = what if isinstance(what, dict) else {"msg": what}
        self.sig_status_upd.emit(what)

    #### OTP related callbacks
    @pyqtSlot()
    def slot_random_secret(self):
        self.otp_secret_type_hex.setChecked(True)
        cnt = int(self.otp_gen_len.text())
        self.otp_secret.setText(self.device.gen_random(cnt, hex=True).decode("utf-8"))

    @pyqtSlot()
    def slot_cancel_otp(self):
        _, _, otp_obj = self.get_active_otp()

        self.otp_secret.clear()
        self.slot_select_otp()

    @pyqtSlot()
    def slot_erase_otp(self):
        who, idx, otp_obj = self.get_active_otp()

        if not self.device.is_auth_admin:
            self.ask_pin("admin")
            return

        ret = otp_obj.erase(idx)
        if not ret.ok:
            self.msg(f"failed erase {who.upper()} #{idx + 1} err: {ret.name}")
        else:
            self.msg(f"erased {who.upper()} #{idx + 1}")
            self.slot_select_otp(idx)

    @pyqtSlot()
    def slot_otp_save_enable(self):
        self.otp_save_btn.setEnabled(True)
        self.otp_cancel_btn.setEnabled(True)

    @pyqtSlot()
    def slot_save_otp(self):
        who, idx, otp_obj = self.get_active_otp()

        if not self.device.is_auth_admin:
            self.ask_pin("admin")
            return

        name = self.otp_name.text()
        if len(name) == 0:
            self.user_err("need non-empty name")
            return

        secret = self.otp_secret.text()
        # @fixme: what are the secret allowed lengths/chars
        #if len(secret)

        ret = otp_obj.write(idx, name, secret)
        if not ret.ok:
            self.msg(f"failed writing to {who.upper()} slot #{idx+1} err: {ret.name}")
        else:
            self.msg(f"wrote {who.upper()} slot #{idx+1}")
            self.otp_secret.clear()
            self.slot_select_otp(idx)

    @pyqtSlot()
    def slot_select_otp(self, force_idx=None):
        who, idx, otp_obj = self.get_active_otp()

        if force_idx is not None and idx != force_idx:
            idx = force_idx
            self.otp_combo_box.setCurrentIndex(idx)

        if idx < 0 or idx is None:
            return

        name = otp_obj.get_name(idx)
        self.otp_name.setText(name)
        self.otp_combo_box.setItemText(idx, f"{who.upper()} #{idx+1} ({name})")

        if name:
            self.sig_status_upd.emit({"msg": otp_obj.get_code(idx)})

        self.otp_cancel_btn.setEnabled(False)
        self.otp_save_btn.setEnabled(False)

    @pyqtSlot()
    def slot_toggle_otp(self):
        who, idx, otp_obj = self.get_active_otp()
        if who == "totp":
            # labels
            self.otp_len_label.setText("TOTP length:")
            self.set_visible(QtWidgets.QLabel, ["label_6"], False)
            self.set_visible(QtWidgets.QLabel, ["intervalLabel"], True)

            # spacers + spin-box
            self.set_visible(QtWidgets.QSpinBox, ["intervalSpinBox"], True)

            # moving seed
            self.set_visible(QtWidgets.QPushButton,
                ["setToRandomButton", "setToZeroButton"], False)
            self.set_visible(QtWidgets.QLineEdit, ["counterEdit"], False)
        else:
            # labels
            self.otp_len_label.setText("HOTP length:")
            self.set_visible(QtWidgets.QLabel, ["intervalLabel"], False)
            self.set_visible(QtWidgets.QLabel, ["label_6"], True)

            # spacers + spin-box
            self.set_visible(QtWidgets.QSpinBox, ["intervalSpinBox"], False)

            # moving seed
            self.set_visible(QtWidgets.QPushButton,
                             ["setToRandomButton", "setToZeroButton"], True)
            self.set_visible(QtWidgets.QLineEdit, ["counterEdit"], True)

        # drop down contents
        self.otp_combo_box.clear()
        for idx in range(otp_obj.count):
            name = otp_obj.get_name(idx) or ""
            self.otp_combo_box.addItem(f"{who.upper()} #{idx+1} ({name})")
            if idx == 0:
                self.otp_name.setText(name)

    @pyqtSlot(int)
    def slot_secret_hide(self, state):
        if state == 2:
            self.otp_secret.setEchoMode(QtWidgets.QLineEdit.Password)
        elif state == 0:
            self.otp_secret.setEchoMode(QtWidgets.QLineEdit.Normal)

    @pyqtSlot(str)
    def slot_confirm_auth(self, who):
        self.unlock_pws_btn.setEnabled(False)
        self.lock_btn.setEnabled(True)

        self.msg(f"{who.capitalize()} authenticated!")

    @pyqtSlot(dict)
    def slot_lock(self, status):
        self.unlock_pws_btn.setEnabled(True)
        self.lock_btn.setEnabled(False)
        self.sig_disconnected.emit()

    #### app-wide slots
    @pyqtSlot(dict, str)
    def slot_auth(self, opts, pin=None):
        who = opts.get("who")
        assert who in ["user", "admin"]
        who_cap = who.capitalize()

        auth_func = self.device.user_auth if who == "user" else self.device.admin_auth
        if pin is not None and auth_func(pin).ok:
            self.sig_confirm_auth.emit(who)
            self.pin_dialog.reset()
            self.user_info(f"{who_cap} auth successful", parent=self.pin_dialog)
        else:
            self.user_err(f"The provided {who}-PIN is not correct, please retry!",
                          f"{who_cap} not authenticated",
                          parent=self.pin_dialog)
            self.ask_pin(who)

    @pyqtSlot()
    def init_gui(self):
        self.init_overview()
        self.init_otp_conf()
        self.init_otp_general()
        self.init_pws()

    @pyqtSlot()
    def job_connect_device(self):
        devs = nk_api.BaseLibNitrokey.list_devices()
        dev = None

        if self.device is not None:
            return {"device": self.device, "connected": self.device.connected,
                    "status": self.device.status}

        if len(devs) > 0:
            _dev = devs[tuple(devs.keys())[0]]

            if _dev["model"] == 1:
                dev = nk_api.NitrokeyPro()
            elif _dev["model"] == 2:
                dev = nk_api.NitrokeyStorage()
            else:
                self.msg("Unknown device model detected")
                return {"connected": False}

            try:
                dev.connect()
                self.device = dev
            except nk_api.DeviceNotFound as e:
                self.device = None
                self.msg("Connection failed, already in use?")
                return {"connected": False}

        if not self.device.connected:
            self.device = None
            return {"connected": False}

        status = dev.status
        self.msg({"status": status, "connected": status["connected"]})

        return {"connected": status["connected"], "status": status, "device": dev}

    @pyqtSlot(dict)
    def update_status_bar(self, res_dct):
        cur_msg = self.status_bar.currentMessage
        append_msg = lambda s: self.status_bar.showMessage(
            s + ((" || " + cur_msg().strip()) if cur_msg().strip() else ""))

        # directly show passed 'msg'
        if "msg" in res_dct:
            append_msg(res_dct["msg"])
            return

        # not connected, show default message
        if not res_dct.get("connected"):
            self.status_bar.showMessage("Not connected")
            return

        # connected, show status information (if available)
        info = res_dct.get("status")
        if info:
            append_msg(f"Device: {info['model'].friendly_name}")
            append_msg(f"Serial: {info['card_serial_u32']}")
            append_msg(f"FW Version: {info['fw_version'][0]}.{info['fw_version'][1]}")
            append_msg(f"PIN Retries - (Admin/User): "
                       f"{info['admin_pin_retries']}/{info['user_pin_retries']}")

    @pyqtSlot(dict)
    def job_nk_connected(self, res_dct):
        if not res_dct["connected"]:
            self.msg("Not connected")
            return

        info = res_dct["status"]

        # enable and show needed widgets
        func = lambda w: (w.setEnabled(True), w.setVisible(True))
        self.apply_by_name(["btn_dial_PWS", "btn_dial_lock",    # overview
                            "frame", "frame_8", "frame_2",      # otp
                            #"frame_4",                         # otp config
                            #"frame_7"                          # pws
                           ], func)

        if info["model"] == nk_api.DeviceModel.NK_STORAGE:
            self.apply_by_name(["btn_dial_EV", "btn_dial_HV"], func) # overview

    #### backend callbacks
    @pyqtSlot()
    def backend_cb_hello(self):
        print(f"hello signaled from worker, started successfully")

    @pyqtSlot(int)
    def slot_tab_changed(self, idx):
        pass

    #### main-window callbacks
    @pyqtSlot()
    def slot_quit_button_pressed(self):
        self.backend_thread.stop_loop()
        self.backend_thread.wait()
        self.app.quit()

    @pyqtSlot()
    def slot_lock_button_pressed(self):
        if not self.device.connected:
            self.msg({"connected": False})
            self.sig_disconnected.emit()
            return

        self.device.lock()
        self.msg("Locked device!")
        self.sig_lock.emit(self.device.status)

    @pyqtSlot()
    def unlock_pws_button_pressed(self):
        if not self.device.connected:
            self.msg({"connected": False})
            self.sig_disconnected.emit()
            return

        self.ask_pin("user")


    #### init main windows
    @pyqtSlot()
    def init_overview(self):
        names = ["btn_dial_EV", "btn_dial_HV", "btn_dial_PWS", "btn_dial_lock"]
        self.set_enabled(QtWidgets.QPushButton, names, False)

    @pyqtSlot()
    def init_otp_conf(self):
        self.set_enabled(QtWidgets.QFrame, ["frame", "frame_8", "frame_2"], False)
        self.set_enabled(QtWidgets.QPushButton, ["writeButton", "cancelButton"], False)
        btns = ["setToRandomButton", "setToZeroButton"]
        self.set_visible(QtWidgets.QPushButton, btns, False)
        lbls = ["l_supportedLength", "labelNotify", "label_6"]
        self.set_visible(QtWidgets.QLabel, lbls , False)
        self.set_visible(QtWidgets.QProgressBar, ["progressBar"], False)
        self.set_visible(QtWidgets.QLineEdit, ["counterEdit"], False)

        self.radio_totp.setChecked(True)
        self.radio_hotp.setChecked(False)

    @pyqtSlot()
    def init_otp_general(self):
        self.set_enabled(QtWidgets.QFrame, ["frame_4"], False)
        names = ["generalCancelButton", "writeGeneralConfigButton"]
        self.set_enabled(QtWidgets.QPushButton, names, False)

    @pyqtSlot()
    def init_pws(self):
        btn_cls = QtWidgets.QPushButton
        self.set_enabled(QtWidgets.QFrame, ["frame_7"], False)
        self.set_visible(btn_cls, ["PWS_Lock"], False)
        self.set_visible(QtWidgets.QProgressBar, ["PWS_progressBar"], False)
        names = ["PWS_ButtonEnable", "PWS_ButtonSaveSlot", "PWS_ButtonClose"]
        self.set_enabled(btn_cls, names, False)
        self.set_enabled(QtWidgets.QLabel, ["l_utf8_info"], False)


def main():
    # backend thread init
    QtUtilsMixIn.backend_thread = BackendThread()

    app = QtWidgets.QApplication(sys.argv)
    window = GUI(app)
    app.exec()

if __name__ == "__main__":
    main()
