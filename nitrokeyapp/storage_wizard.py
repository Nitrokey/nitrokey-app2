# Nitrokey 2
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot

from nitrokeyapp.qt_utils_mix_in import QtUtilsMixIn


class Storage(QtUtilsMixIn, QtWidgets.QWizard):
    def __init__(self, qt_app: QtWidgets.QApplication):
        QtWidgets.QWizard.__init__(self)
        QtUtilsMixIn.__init__(self)
        self.ok_insert = None
        self.app = qt_app

    def init_storage(self):
        self.wizardpage_hidden_volume_pw = self.get_widget(
            QtWidgets.QWizardPage, "wizardPage"
        )
        self.hidden_pw_1 = self.get_widget(QtWidgets.QLineEdit, "HVPasswordEdit")
        self.hidden_pw_2 = self.get_widget(QtWidgets.QLineEdit, "HVPasswordEdit_2")
        self.wizardpage_hidden_volume_pw.registerField("hidden_pw_1*", self.hidden_pw_1)
        self.wizardpage_hidden_volume_pw.registerField("hidden_pw_2*", self.hidden_pw_2)
        self.show_hidden_pw = self.get_widget(
            QtWidgets.QCheckBox, "ShowPasswordCheckBox"
        )

        self.storage_slider = self.get_widget(
            QtWidgets.QSlider, "horizontalSlider_storage"
        )
        self.storage_blockspin = self.get_widget(
            QtWidgets.QDoubleSpinBox, "StartBlockSpin_3"
        )

        self.radio_gb = self.get_widget(QtWidgets.QRadioButton, "rd_GB_3")
        self.radio_mb = self.get_widget(QtWidgets.QRadioButton, "rd_MB_3")

        self.confirm_creation = self.get_widget(QtWidgets.QCheckBox, "checkBox_confirm")

        self.lastpage = self.get_widget(QtWidgets.QWizardPage, "wizardPage_3")

        self.lastpage.registerField("confirm_creation*", self.confirm_creation)

        self.storage_blockspin.valueChanged.connect(self.change_value_2)
        self.storage_slider.valueChanged.connect(self.change_value)

        self.radio_gb.toggled.connect(self.swap_to_gb)
        self.radio_mb.toggled.connect(self.swap_to_mb)
        self.hidden_pw_2.textChanged.connect(self.same_storage)

    def same_storage(self):
        if self.hidden_pw_2.text() != self.hidden_pw_1.text():
            self.button(QtWidgets.QWizard.NextButton).setEnabled(False)
        else:
            self.button(QtWidgets.QWizard.NextButton).setEnabled(True)

    @pyqtSlot(int)
    # storage wizard
    def change_value(self, value):
        self.storage_blockspin.setValue(float(value))

    def change_value_2(self, value):
        self.storage_slider.setValue(float(value))

    @pyqtSlot()
    def swap_to_mb(self):
        if self.radio_mb.isChecked():
            self.storage_blockspin.setMaximum(30000)
            self.storage_slider.setMaximum(30000)
            self.storage_blockspin.setValue(
                float(self.storage_blockspin.value()) * 1000
            )
            self.storage_slider.setValue(float(self.storage_blockspin.value()))
            self.storage_slider.setSingleStep(300)
            self.storage_blockspin.setSingleStep(300)

    def swap_to_gb(self):
        if self.radio_gb.isChecked():
            self.storage_blockspin.setValue(
                float(self.storage_blockspin.value()) / 1000
            )
            self.storage_slider.setValue(float(self.storage_blockspin.value()))

            self.storage_blockspin.setMaximum(30)
            self.storage_slider.setMaximum(30)
            self.storage_slider.setSingleStep(1)
            self.storage_blockspin.setSingleStep(1)
