from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import QObject


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
        return slot.connect(cls.backend_thread.add_job(signal, func, *va, **kw))

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

    def collapse(self, gBox, expand_button):
        # Find out if the state is on or off
        gbState = expand_button.isChecked()
        if not gbState:
            expand_button.setIcon(QtGui.QIcon(":/images/new/right_arrow.png"))
            gBox.setFixedHeight(15)
            # Set window Height
            # self.setFixedHeight(self.sizeHint().height())

        else:
            expand_button.setIcon(QtGui.QIcon(":/images/new/down_arrow.png"))
            oSize = gBox.sizeHint()
            gBox.setFixedHeight(oSize.height())
            # Set window Height
            # self.setFixedHeight(self.sizeHint().height())

    # https://groups.google.com/g/python_inside_maya/c/Y6r8o9zpWfU
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
