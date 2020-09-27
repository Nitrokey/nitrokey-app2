


# use "pbs" for packaging...
# pip-run -> pyqt5
# pip-dev -> pyqt5-stubs


import sys
import os
from pathlib import Path
from queue import Queue

from pprint import pprint as pp


from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject

import nitropyapp.libnk as nk_api

#pyrcc5 -o gui_resources.py ui/resources.qrc
import nitropyapp.gui_resources


#import pysnooper
#@pysnooper.snoop

UI_FILES_PATH = "ui"

class ResultUIDNotFound(Exception): pass


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
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
        ui_path = Path(UI_FILES_PATH)
        ui_res = resource_path((ui_path / filename).as_posix())
        uic.loadUi(ui_res, qt_obj)
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
        self.hide()

    @pyqtSlot(dict)
    def invoke(self, dct):
        self.tries_left = dct.get("retries", 0)
        if self.tries_left == 0:
            self.user_warn("Please reset the user pin counter before continuing",
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
        # @fixme: mmmh, hardcoded or not?
        if len(pin) < 6 or len(pin) > 20:
            self.line_edit.selectAll()
            self.user_warn("The pin requires to be 6-20 chars in length\n"
                "default: 123456", "Invalid PIN")
        else:
            self.ok_signal.emit(pin)


class GUI(QtUtilsMixIn, QtWidgets.QMainWindow):

    sig_connected = pyqtSignal(dict)
    sig_disconnected = pyqtSignal()
    sig_lock = pyqtSignal(dict)

    sig_admin_auth = pyqtSignal(str)

    sig_ask_user_pin = pyqtSignal(dict)
    sig_user_auth = pyqtSignal(str)
    sig_confirm_user = pyqtSignal()

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

        ################################################################################
        # app wide widgets
        self.status_bar = self.get_widget(QtWidgets.QStatusBar, "statusBar")
        self.menu_bar = self.get_widget(QtWidgets.QMenuBar, "menuBar")
        self.tabs = self.get_widget(QtWidgets.QTabWidget, "tabWidget")
        self.tab_overview = self.get_widget(QtWidgets.QWidget, "tab_5")
        self.tab_otp_conf = self.get_widget(QtWidgets.QWidget, "tab")
        self.tab_otp_gen = self.get_widget(QtWidgets.QWidget, "tab_2")
        self.tab_pws = self.get_widget(QtWidgets.QWidget, "tab_3")
        self.tab_settings = self.get_widget(QtWidgets.QWidget, "tab_4")

        ################################################################################
        # OTP widgets
        self.radio_hotp = self.get_widget(QtWidgets.QRadioButton, "radioButton")
        self.radio_totp = self.get_widget(QtWidgets.QRadioButton, "radioButton_2")
        self.otp_combo_box = self.get_widget(QtWidgets.QComboBox, "slotComboBox")
        self.otp_name = self.get_widget(QtWidgets.QLineEdit, "nameEdit")
        self.otp_len_label = self.get_widget(QtWidgets.QLabel, "label_5")


        ################################################################################
        # set some props, initial enabled/visible, finally show()
        self.setAttribute(Qt.WA_DeleteOnClose)

        #self.tabs.setCurrentIndex(0)
        self.tabs.setCurrentWidget(self.tab_overview)
        self.tabs.currentChanged.connect(self.tab_changed)

        self.init_gui()
        self.show()

        self.device = None

        ################################################################################
        # app wide callbacks
        self.quit_button = self.get_widget(QtWidgets.QPushButton, "btn_dial_quit")
        self.quit_button.clicked.connect(self.quit_button_pressed)

        self.help_btn = self.get_widget(QtWidgets.QPushButton, "btn_dial_help")

        self.lock_btn = self.get_widget(QtWidgets.QPushButton, "btn_dial_lock")
        self.lock_btn.clicked.connect(self.lock_button_pressed)

        self.unlock_pws = self.get_widget(QtWidgets.QPushButton, "btn_dial_PWS")
        self.unlock_pws.clicked.connect(self.unlock_pws_button_pressed)


        ################################################################################
        # connections for functional signals
        self.connect_signal_slots(self.help_btn.clicked, self.sig_connected,
            [self.job_nk_connected, self.slot_toggle_otp], self.job_connect_device)

        self.sig_status_upd.connect(self.update_status_bar)
        self.sig_disconnected.connect(self.init_gui)

        self.radio_totp.toggled.connect(self.slot_toggle_otp)
        self.radio_hotp.toggled.connect(self.slot_toggle_otp)

        ################################################################################
        self.sig_ask_user_pin.connect(self.pin_dialog.invoke)
        self.sig_user_auth.connect(self.slot_try_user_auth)
        self.sig_confirm_user.connect(self.slot_confirm_user_auth)
        self.sig_lock.connect(self.slot_lock)

    @pyqtSlot()
    def slot_confirm_user_auth(self):
        self.unlock_pws.setEnabled(False)
        self.lock_btn.setEnabled(True)

    @pyqtSlot(dict)
    def slot_lock(self, status):
        self.unlock_pws.setEnabled(True)
        self.lock_btn.setEnabled(False)

    @pyqtSlot(str)
    def slot_try_user_auth(self, pin=None):
        # @fixme: error translation must be done within libnk(!)
        #         0 == "ok" .... bad bad
        if self.device.user_auth(pin) == 0:
            self.sig_confirm_user.emit()
            self.pin_dialog.reset()
            self.user_info("User authentification successful", parent=self.pin_dialog)
        else:
            self.user_err("The provided user-PIN is not correct, please retry!",
                          "Not authenticated", parent=self.pin_dialog)

            self.sig_ask_user_pin.emit(dict(title="User PIN:",
                retries=self.device.user_pin_retries,
                sig=self.sig_user_auth))

    @pyqtSlot()
    def slot_toggle_otp(self):
        who = None
        if self.radio_totp.isChecked():
            who = "totp"

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
            who = "hotp"

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
        what = self.device.TOTP if who == "totp" else self.device.HOTP
        for idx in range(what.count):
            name = what.get_name(idx) or "n/a"
            self.otp_combo_box.addItem(f"{who.upper()} #{idx+1} ({name})")
            if idx == 0:
                self.otp_name.setText(name)



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
                self.sig_status_upd.emit({"msg": "Unknown device model detected"})
                return {"connected": False}

            try:
                dev.connect()
                self.device = dev
            except nk_api.DeviceNotFound as e:
                self.device = None
                self.sig_status_upd.emit(
                    {"msg": "Connection failed, already in use?"})
                return {"connected": False}

        if not self.device.connected:
            self.device = None
            return {"connected": False}

        status = dev.status
        self.sig_status_upd.emit({"status": status, "connected": status["connected"]})

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
            self.sig_status_upd.emit({"msg": "Not connected"})
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
    def tab_changed(self, idx):
        pass

    #### main-window callbacks
    @pyqtSlot()
    def quit_button_pressed(self):
        self.backend_thread.stop_loop()
        self.backend_thread.wait()
        self.app.quit()

    @pyqtSlot()
    def lock_button_pressed(self):
        if not self.device.connected:
            self.sig_status_upd.emit({"connected": False})
            self.sig_disconnected.emit()
            return

        self.device.lock()
        self.sig_status_upd.emit({"msg": "Locked device!"})
        self.sig_lock.emit(self.device.status)

    @pyqtSlot()
    def unlock_pws_button_pressed(self):
        if not self.device.connected:
            self.sig_status_upd.emit({"connected": False})
            self.sig_disconnected.emit()
            return

        self.sig_ask_user_pin.emit(dict(title="User PIN:",
            retries=self.device.user_pin_retries,
            sig=self.sig_user_auth))


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
