from typing import Callable, List, Optional

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class BackupRestoreUi(QDialog):
    def __init__(self, name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        processname = name
        name = "backup" if processname.lower().startswith("backup") else "restore"

        self.name = name
        self.setWindowTitle(name.capitalize())

        self.action_edit = QLineEdit(processname)
        self.action_edit.setReadOnly(True)

        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Action:"))
        action_layout.addWidget(self.action_edit)

        self.cleartext_checkbox = QCheckBox("Cleartext")
        self.cleartext_checkbox.setVisible(name == "backup")

        self.passphrase_edit = QLineEdit()
        self.passphrase_edit.setReadOnly(name == "backup")

        self.copy_passphrase_button = QToolButton()
        self.copy_passphrase_button.setText("📋")
        self.copy_passphrase_button.setToolTip("Copy passphrase")

        self.begin_button = QPushButton("Begin")

        passphrase_layout = QHBoxLayout()
        passphrase_layout.setContentsMargins(0, 0, 0, 0)
        passphrase_layout.addWidget(self.passphrase_edit)
        passphrase_layout.addWidget(self.copy_passphrase_button)

        middle_layout = QHBoxLayout()
        middle_layout.addWidget(self.cleartext_checkbox)
        middle_layout.addStretch(1)
        middle_layout.addWidget(QLabel("Passphrase"))
        middle_layout.addLayout(passphrase_layout, 1)
        middle_layout.addWidget(self.begin_button)

        self.copy_passphrase_button.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(self.passphrase_edit.text())
        )

        self.successful_list = QListWidget()
        self.failed_list = QListWidget()
        self.skipped_list = QListWidget()

        self.failed_name = "Not passwords" if name == "backup" else "Already exists"

        self.successful_label = QLabel("Successful (0)")
        self.failed_label = QLabel(f"{self.failed_name} (0)")
        self.skipped_label = QLabel("Skipped (0)")

        lists_layout = QHBoxLayout()
        for label, widget in (
            (self.successful_label, self.successful_list),
            (self.failed_label, self.failed_list),
            (self.skipped_label, self.skipped_list),
        ):
            column = QVBoxLayout()
            column.addWidget(label)
            column.addWidget(widget)
            lists_layout.addLayout(column)

        self.status_edit = QLineEdit()
        self.status_edit.setReadOnly(True)

        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status"))
        status_layout.addWidget(self.status_edit)

        layout = QVBoxLayout()
        layout.addLayout(action_layout)
        layout.addSpacing(16)
        layout.addLayout(middle_layout)
        layout.addLayout(lists_layout)
        layout.addLayout(status_layout)
        self.setLayout(layout)

        self.resize(900, 520)

    def update_fields(
        self, success_list: List[bytes], failed_list: List[bytes], skipped_list: List[bytes]
    ) -> None:
        self.successful_list.clear()
        self.failed_list.clear()
        self.skipped_list.clear()

        for item in success_list:
            self.successful_list.addItem(item.decode("utf-8", errors="ignore"))

        for item in failed_list:
            self.failed_list.addItem(item.decode("utf-8", errors="ignore"))

        for item in skipped_list:
            self.skipped_list.addItem(item.decode("utf-8", errors="ignore"))

        self.successful_label.setText(f"Successful ({len(success_list)})")
        self.failed_label.setText(f"{self.failed_name} ({len(failed_list)})")
        self.skipped_label.setText(f"Skipped ({len(skipped_list)})")

    def update_status(self, status: str) -> None:
        self.status_edit.setText(status)

    def update_passphrase(self, passphrase: str) -> None:
        self.passphrase_edit.setText(passphrase)

    def begin(self, callback: Callable[[bool, str, str], None]) -> None:
        def on_clicked() -> None:
            callback(self.cleartext_checkbox.isChecked(), self.passphrase_edit.text(), self.name)

        self.begin_button.clicked.connect(on_clicked)


def open_backup_restore_ui(name: str, parent: Optional[QWidget] = None) -> BackupRestoreUi:
    ui = BackupRestoreUi(name, parent)
    ui.show()
    return ui
