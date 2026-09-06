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
        self.setWindowTitle(
            self.tr("Backup") if name == BackupRestoreAction.BACKUP else self.tr("Restore")
        )

        self.action_edit = QLabel(self.tr("Action: {0}").format(title))

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.action_edit)

        self.cleartext_checkbox = QCheckBox(self.tr("Cleartext"))
        self.cleartext_checkbox.setToolTip(
            self.tr(
                "This option disables encryption of the generated backup and is discouraged. "
                "Only use it for interoperability with other password managers."
            )
        )
        self.cleartext_checkbox.setVisible(name == BackupRestoreAction.BACKUP)

        self.passphrase_edit = QLineEdit()
        self.passphrase_edit.setToolTip(
            self.tr("The passphrase is created automatically during an encrypted backup.")
        )
        self.passphrase_edit.setReadOnly(name == BackupRestoreAction.BACKUP)

        self.copy_passphrase_button = QToolButton()
        self.copy_passphrase_button.setIcon(icon)
        self.copy_passphrase_button.setToolTip(self.tr("Copy passphrase"))

        self.begin_button = QPushButton(self.tr("Begin"))

        passphrase_layout = QHBoxLayout()
        passphrase_layout.setContentsMargins(0, 0, 0, 0)
        passphrase_layout.addWidget(self.passphrase_edit)
        if self.name == BackupRestoreAction.BACKUP:
            passphrase_layout.addWidget(self.copy_passphrase_button)

        middle_layout = QHBoxLayout()
        middle_layout.addWidget(self.cleartext_checkbox)
        middle_layout.addStretch(1)
        middle_layout.addWidget(QLabel(self.tr("Passphrase")))
        middle_layout.addLayout(passphrase_layout, 1)
        middle_layout.addWidget(self.begin_button)

        self.copy_passphrase_button.clicked.connect(self.copy_passphrase)

        self.successful_list = QListWidget()
        self.failed_list = QListWidget()
        self.skipped_list = QListWidget()

        self.failed_name = (
            self.tr("Not passwords")
            if name == BackupRestoreAction.BACKUP
            else self.tr("Already exists")
        )

        self.successful_label = QLabel(self.count_label(self.tr("Successful"), 0))
        self.successful_label.setToolTip(
            self.tr("The operation on these credentials completed successfully")
        )

        self.failed_label = QLabel(self.count_label(self.failed_name, 0))
        self.failed_label.setToolTip(
            self.tr(
                "Credentials without a password (for example OTP only) are skipped during "
                "the backup, as they cannot be extracted from the device."
            )
            if name == BackupRestoreAction.BACKUP
            else self.tr(
                "Credentials that were not imported because a credential with the same "
                "label already exists on the device"
            )
        )

        self.skipped_label = QLabel(self.count_label(self.tr("Skipped"), 0))
        self.skipped_label.setToolTip(
            self.tr("Credentials are skipped if they are PIN protected but no PIN was supplied.")
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
        status_layout.addWidget(QLabel(self.tr("Status")))
        status_layout.addWidget(self.status_edit)

        layout = QVBoxLayout()
        layout.addLayout(action_layout)
        layout.addSpacing(16)
        layout.addLayout(middle_layout)
        layout.addLayout(lists_layout)
        layout.addLayout(status_layout)
        self.setLayout(layout)

        self.resize(900, 520)

    def count_label(self, name: str, count: int) -> str:
        return self.tr("{0} ({1})").format(name, count)

    def copy_passphrase(self) -> None:
        if self.passphrase_edit.text() != "":
            QGuiApplication.clipboard().setText(self.passphrase_edit.text())
            self.update_status(self.tr("Passphrase copied"))
        else:
            self.update_status(self.tr("Nothing to copy"))

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

        self.successful_label.setText(self.count_label(self.tr("Successful"), len(success_list)))
        self.failed_label.setText(self.count_label(self.failed_name, len(failed_list)))
        self.skipped_label.setText(self.count_label(self.tr("Skipped"), len(skipped_list)))

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
