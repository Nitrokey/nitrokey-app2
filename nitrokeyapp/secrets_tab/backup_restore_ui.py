from enum import Enum
from typing import Callable, List, Optional

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class BackupRestoreAction(str, Enum):
    BACKUP = "backup"
    RESTORE = "restore"


class BackupRestoreUi(QDialog):
    def __init__(
        self, name: BackupRestoreAction, title: str, icon: QIcon, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self.name = name
        self.setWindowTitle(name.capitalize())

        self.action_edit = QLabel(f"Action: {title}")

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.action_edit)

        self.cleartext_checkbox = QCheckBox("Cleartext")
        self.cleartext_checkbox.setToolTip(
            "This option disables encryption of the generated backup and is discouraged. Only use for interoperability with other password managers."
        )
        self.cleartext_checkbox.setVisible(name == BackupRestoreAction.BACKUP)

        self.passphrase_edit = QLineEdit()
        self.passphrase_edit.setToolTip(
            "Passphrase is automatically created during an encrypted backup."
        )
        self.passphrase_edit.setReadOnly(name == BackupRestoreAction.BACKUP)

        self.copy_passphrase_button = QToolButton()
        self.copy_passphrase_button.setIcon(icon)
        self.copy_passphrase_button.setToolTip("Copy passphrase")

        self.begin_button = QPushButton("Begin")

        passphrase_layout = QHBoxLayout()
        passphrase_layout.setContentsMargins(0, 0, 0, 0)
        passphrase_layout.addWidget(self.passphrase_edit)
        if self.name == BackupRestoreAction.BACKUP:
            passphrase_layout.addWidget(self.copy_passphrase_button)

        middle_layout = QHBoxLayout()
        middle_layout.addWidget(self.cleartext_checkbox)
        middle_layout.addStretch(1)
        middle_layout.addWidget(QLabel("Passphrase"))
        middle_layout.addLayout(passphrase_layout, 1)
        middle_layout.addWidget(self.begin_button)

        self.copy_passphrase_button.clicked.connect(self.copy_passphrase)

        self.successful_list = QListWidget()
        self.failed_list = QListWidget()
        self.skipped_list = QListWidget()

        self.failed_name = (
            "Not passwords" if name == BackupRestoreAction.BACKUP else "Already exists"
        )

        self.successful_label = QLabel("Successful (0)")
        self.successful_label.setToolTip("Operation on these credentials completed successfully")

        self.failed_label = QLabel(f"{self.failed_name} (0)")
        self.failed_label.setToolTip(
            "Credentials without a password (for example OTP only) are skipped during the backup as they cannot be extracted from the device."
            if name == BackupRestoreAction.BACKUP
            else "Credentials not imported because a credential with same label already exists on the device"
        )

        self.skipped_label = QLabel("Skipped (0)")
        self.skipped_label.setToolTip(
            "Credentials are skipped if they are PIN protected but PIN is not supplied."
        )

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

        self.status_edit = QStatusBar()
        # self.status_edit.setReadOnly(True)

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

    def copy_passphrase(self) -> None:
        if self.passphrase_edit.text() != "":
            QGuiApplication.clipboard().setText(self.passphrase_edit.text())
            self.update_status("Passphrase copied!")
        else:
            self.update_status("Nothing to copy!")

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
        self.status_edit.showMessage(status)

    def update_passphrase(self, passphrase: str) -> None:
        self.passphrase_edit.setText(passphrase)

    def begin(self, callback: Callable[[bool, str, BackupRestoreAction], None]) -> None:
        def on_clicked() -> None:
            callback(self.cleartext_checkbox.isChecked(), self.passphrase_edit.text(), self.name)

        self.begin_button.clicked.connect(on_clicked)


def open_backup_restore_ui(
    action: BackupRestoreAction, title: str, icon: QIcon, parent: Optional[QWidget] = None
) -> BackupRestoreUi:
    ui = BackupRestoreUi(action, title, icon, parent)
    ui.show()
    return ui
