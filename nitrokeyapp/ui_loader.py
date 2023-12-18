from typing import Dict, Optional

from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader


# taken/inspired with many thanks from: https://gist.github.com/cpbotha/1b42a20c8f3eb9bb7cb8
class UiLoader(QUiLoader):
    """
    Subclass :class:`~PySide6.QtUiTools.QUiLoader` to create the user interface
    in a base instance.
    Unlike :class:`~PySide6.QtUiTools.QUiLoader` itself this class does not
    create a new instance of the top-level widget, but creates the user
    interface in an existing instance of the top-level class.
    This mimics the behaviour of :func:`PyQt4.uic.loadUi`.
    """

    def __init__(
        self,
        baseinstance: Optional[QtWidgets.QWidget],
        customWidgets: Optional[Dict[str, QtWidgets.QWidget]] = None,
    ):
        """
        Create a loader for the given ``baseinstance``.
        The user interface is created in ``baseinstance``, which must be an
        instance of the top-level class in the user interface to load, or a
        subclass thereof.
        ``customWidgets`` is a dictionary mapping from class name to class object
        for widgets that you've promoted in the Qt Designer interface. Usually,
        this should be done by calling registerCustomWidget on the QUiLoader.
        ``parent`` is the parent object of this loader.
        """

        QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets or {}

    def createWidget(
        self,
        class_name: str,
        parent: Optional[QtWidgets.QWidget] = None,
        name: str = "",
    ) -> QtWidgets.QWidget:
        """
        Function that is called for each widget defined in ui file,
        overridden here to populate baseinstance instead.
        """
        if parent is None and self.baseinstance:
            # supposed to create the top-level widget, return the base instance
            # instead
            return self.baseinstance

        else:
            if class_name in self.availableWidgets():
                # create a new widget for child widgets
                widget = QUiLoader.createWidget(self, class_name, parent, name)
            else:
                try:
                    # @fixme? in fact QWidget is callable
                    widget = self.customWidgets[class_name](parent)  # type: ignore

                except (TypeError, KeyError):
                    raise Exception(
                        "No custom widget "
                        + class_name
                        + " found in customWidgets param of UiLoader __init__."
                    )

            if self.baseinstance:
                # set an attribute for the new child widget on the base
                # instance, just like PyQt4.uic.loadUi does.

                setattr(self.baseinstance, name, widget)

                # this outputs the various widget names, e.g.
                # sampleGraphicsView, dockWidget, samplesTableView etc.
                # print(name)

            return widget
