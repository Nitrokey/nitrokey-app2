import sys
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Callable, Generator, Optional, Type

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from nitrokeyapp.gui import GUI
from nitrokeyapp.logger import init_logging, log_environment


@contextmanager
def exception_handler(
    hook: Callable[[Type[BaseException], BaseException, Optional[TracebackType]], Any],
) -> Generator[None, None, None]:
    old_hook = sys.excepthook
    sys.excepthook = hook
    try:
        yield
    finally:
        sys.excepthook = old_hook


_STYLESHEET_LIGHT = """
/* ════════════════════════════════════════════════════════════════════
   NITROKEY APP  —  Global Stylesheet (Light)
   Palette:
     sidebar-bg    #161b22    sidebar-border  #30363d
     sidebar-text  #cdd9e5    sidebar-muted   #768390
     content-bg    #f6f8fa    surface         #ffffff
     border        #d0d7de    border-focus    #c0392b
     text          #24292f    text-muted      #57606a
     accent        #c0392b    accent-hover    #a93226
     accent-press  #922b21    accent-light    #fce8e6
     success       #2da44e    warning         #d29922
   ════════════════════════════════════════════════════════════════════ */

/* ── Base ───────────────────────────────────────────────────────────── */
QWidget {
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 11pt;
    color: #24292f;
    background-color: #f6f8fa;
}
QLabel { background-color: transparent; }
QMainWindow { background-color: #f6f8fa; }

/* ── Dark sidebar ───────────────────────────────────────────────────── */
QFrame#vertical_navigation {
    background-color: #161b22;
    border: none;
    border-right: 1px solid #30363d;
}
QFrame#vertical_navigation QLabel {
    color: #cdd9e5;
    background-color: transparent;
}
QFrame#vertical_navigation QWidget { background-color: transparent; }
QFrame#vertical_navigation QPushButton {
    background-color: transparent;
    border: none;
    color: #768390;
    border-radius: 6px;
    padding: 6px;
}
QFrame#vertical_navigation QPushButton:hover {
    background-color: rgba(177, 186, 196, 0.12);
    color: #cdd9e5;
}

/* ── Tabs ───────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid #d0d7de;
    background-color: #f6f8fa;
}
QTabBar               { background-color: #ffffff; }
QTabBar::tab {
    background-color: #ffffff;
    color: #57606a;
    padding: 9px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected           { color: #c0392b; border-bottom: 2px solid #c0392b; font-weight: 600; }
QTabBar::tab:hover:!selected    { color: #24292f; background-color: #f6f8fa; }
QTabBar::tab:disabled           { color: #bac1cb; }

/* ── Standard button ────────────────────────────────────────────────── */
QPushButton {
    background-color: #f6f8fa;
    color: #24292f;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 5px 16px;
    min-height: 30px;
    font-weight: 500;
}
QPushButton:hover    { background-color: #eaeef2; border-color: #bac1cb; }
QPushButton:pressed  { background-color: #dde3ea; }
QPushButton:focus    { border-color: #c0392b; outline: none; }
QPushButton:disabled { color: #8c959f; background-color: #f6f8fa; border-color: #eaeef2; }

/* Primary action — writes to the device */
QPushButton#btn_save,
QPushButton#btn_add {
    background-color: #c0392b;
    color: #ffffff;
    border: 1px solid #a93226;
    font-weight: 600;
}
QPushButton#btn_save:hover,
QPushButton#btn_add:hover   { background-color: #a93226; border-color: #922b21; }
QPushButton#btn_save:pressed,
QPushButton#btn_add:pressed { background-color: #922b21; }
QPushButton#btn_save:focus,
QPushButton#btn_add:focus   { border-color: #7b241c; outline: none; }
QPushButton#btn_save:disabled { background-color: #e8a09a; color: #fff0ef; border-color: #dd8880; }

/* Destructive — removes data from the device */
QPushButton#btn_delete,
QPushButton#btn_reset {
    background-color: transparent;
    color: #c0392b;
    border: 1px solid #c0392b;
}
QPushButton#btn_delete:hover,
QPushButton#btn_reset:hover   { background-color: #c0392b; color: #ffffff; }
QPushButton#btn_delete:pressed,
QPushButton#btn_reset:pressed { background-color: #922b21; border-color: #922b21; color: #ffffff; }

/* ── Lists ──────────────────────────────────────────────────────────── */
QListWidget,
QTreeWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}
QListWidget::item,
QTreeWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    color: #24292f;
    min-height: 24px;
}
QListWidget::item:selected       { background-color: #fce8e6; color: #c0392b; }
QListWidget::item:hover:!selected { background-color: #f6f8fa; }

/* Tree item — left accent bar instead of platform selection glyph */
QTreeWidget::item:selected {
    background-color: #fce8e6;
    color: #c0392b;
    border-left: 3px solid #c0392b;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}
QTreeWidget::item:hover:!selected { background-color: #f6f8fa; }

/* Override Windows system-accent color in the branch indent area */
QTreeWidget::branch                                          { background-color: #ffffff; border-image: none; image: none; }
QTreeWidget::branch:selected                                 { background-color: #fce8e6; border-image: none; image: none; }
QTreeWidget::branch:hover:!selected                          { background-color: #f6f8fa;  border-image: none; image: none; }
QTreeWidget::branch:!selected:!has-siblings:!adjoins-item    { background-color: #f6f8fa;  border-image: none; image: none; }
QTreeWidget::branch:has-siblings:!adjoins-item               { background-color: transparent; border-image: none; image: none; }
QTreeWidget::branch:has-siblings:adjoins-item                { background-color: transparent; border-image: none; image: none; }
QTreeWidget::branch:!has-children:!has-siblings:adjoins-item { background-color: transparent; border-image: none; image: none; }
QTreeWidget::branch:closed:has-children:has-siblings         { border-image: none; image: none; }
QTreeWidget::branch:has-children:!has-siblings:closed        { border-image: none; image: none; }
QTreeWidget::branch:open:has-children:has-siblings           { border-image: none; image: none; }
QTreeWidget::branch:has-children:!has-siblings:open          { border-image: none; image: none; }
QHeaderView::section                { background-color: #f6f8fa; border: none; border-bottom: 1px solid #d0d7de; padding: 6px 10px; color: #57606a; font-weight: 600; }

/* ── Inputs ─────────────────────────────────────────────────────────── */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
    color: #24292f;
    selection-background-color: #fce8e6;
    selection-color: #24292f;
}
QLineEdit:focus     { border: 1px solid #6e7781; outline: none; }
QLineEdit:read-only { background-color: #f6f8fa; color: #57606a; }
QLineEdit:read-only:focus { border-color: #d0d7de; }
QLineEdit:disabled  { background-color: #f6f8fa; color: #8c959f; border-color: #eaeef2; }

QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
    color: #24292f;
}
QComboBox:focus          { border: 1px solid #6e7781; outline: none; }
QComboBox::drop-down     { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    selection-background-color: #fce8e6;
    selection-color: #c0392b;
    outline: none;
    padding: 4px;
}

/* ── Checkboxes ─────────────────────────────────────────────────────── */
QCheckBox           { spacing: 8px; color: #24292f; background-color: transparent; }
QStackedWidget#algorithm_tab,
QWidget#algorithm_edit,
QWidget#algorithm_show { background-color: transparent; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked            { background-color: #ffffff; border: 2px solid #c0392b; }
QCheckBox::indicator:checked:disabled   { background-color: #f6f8fa; border: 2px solid #e8a09a; }
QCheckBox::indicator:unchecked:disabled { background-color: #f6f8fa; border-color: #d0d7de; }

/* ── Cards / panels ─────────────────────────────────────────────────── */
QFrame#__credential_show_frame,
QFrame#settings_frame,
QFrame#___nk3_info_space,
QFrame#frame_more_options {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 4px;
}

/* ── Status / info bar ──────────────────────────────────────────────── */
QFrame#information_frame {
    background-color: #ffffff;
    border-top: 1px solid #d0d7de;
}

/* ── Dialogs ────────────────────────────────────────────────────────── */
QDialog           { background-color: #ffffff; }
QMessageBox       { background-color: #ffffff; }
QInputDialog      { background-color: #ffffff; }
QDialog QLabel,
QMessageBox QLabel,
QInputDialog QLabel {
    background-color: transparent;
    color: #24292f;
}
QMessageBox QPushButton,
QInputDialog QPushButton,
QDialogButtonBox QPushButton { min-width: 88px; }

/* ── Error dialog — monospace log view ──────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #1c2128;
    color: #cdd9e5;
    border: 1px solid #444c56;
    border-radius: 6px;
    padding: 10px;
    font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
    font-size: 10pt;
    selection-background-color: #2d4f67;
    selection-color: #cdd9e5;
}

/* ── TOTP countdown ─────────────────────────────────────────────────── */
QProgressBar#otp_timeout_progress {
    background-color: #eaeef2;
    border: none;
    border-radius: 3px;
    text-align: center;
    font-size: 9pt;
    color: #57606a;
    min-height: 10px;
    max-height: 10px;
}
QProgressBar#otp_timeout_progress::chunk { background-color: #2da44e; border-radius: 2px; }

/* ── App-level loading progress bar ─────────────────────────────────── */
QProgressBar#progress_bar {
    background-color: #eaeef2;
    border: none;
    border-radius: 0;
    text-align: center;
    font-size: 10pt;
    color: #57606a;
    min-height: 18px;
    max-height: 18px;
}
QProgressBar#progress_bar::chunk { background-color: #c0392b; }

/* ── Scroll bars ────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #d0d7de;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover        { background-color: #8c959f; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical            { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical            { background: none; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #d0d7de;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover      { background-color: #8c959f; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal          { width: 0; }

/* ── Scroll areas ───────────────────────────────────────────────────── */
QScrollArea,
QScrollArea > QWidget > QWidget { background-color: transparent; border: none; }

/* ── Welcome tab cards ──────────────────────────────────────────────── */
QFrame#introduction,
QFrame#frame_version,
QFrame#frame_help {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 4px;
}

/* Welcome tab labels */
QLabel#info_1 { color: #24292f; font-size: 10pt; font-weight: 600; }
QLabel#info_2,
QLabel#info_3 { color: #57606a; font-size: 10pt; padding-left: 12px; }
QLabel#Version { color: #57606a; font-weight: 600; font-size: 10pt; }
QLabel#VersionNr { color: #24292f; font-size: 10pt; font-weight: 600; }

/* ── More options accordion toggle ──────────────────────────────────── */
QPushButton#btn_more_options {
    background-color: transparent;
    border: none;
    color: #57606a;
    font-weight: 600;
    padding: 4px 2px;
    text-align: left;
}
QPushButton#btn_more_options:hover   { color: #24292f; }
QPushButton#btn_more_options:checked { color: #c0392b; }

/* ── Form field labels (muted — visually subordinate to values) ─────── */
QLabel#username_label,
QLabel#password_label,
QLabel#comment_label,
QLabel#is_pin_protection_label,
QLabel#is_touch_protection_label,
QLabel#current_password_label,
QLabel#new_password_label,
QLabel#repeat_password_label {
    color: #57606a;
    font-weight: 600;
}

/* ── Section headlines inside cards ────────────────────────────────── */
QLabel#headline_label,
QLabel#nk3_label {
    color: #24292f;
    font-size: 13pt;
    font-weight: 700;
    padding-bottom: 4px;
}

/* ── Overview tab info card field labels ────────────────────────────── */
QLabel#___uuid_label,
QLabel#___path_label,
QLabel#___version_label,
QLabel#___variant_label,
QLabel#status_label {
    color: #57606a;
    font-weight: 600;
}

/* ── Security warning text (PIN retry count, destructive actions) ───── */
QLabel#warning_label {
    color: #9a3412;
    background-color: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 10pt;
}

/* ── Informational footnote text ────────────────────────────────────── */
QLabel#info_label {
    color: #57606a;
    font-size: 10pt;
    line-height: 1.4;
}

/* ── Tooltips ───────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c2128;
    color: #cdd9e5;
    border: 1px solid #444c56;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 10pt;
}
"""

_STYLESHEET_DARK = """
/* ════════════════════════════════════════════════════════════════════
   NITROKEY APP  —  Global Stylesheet (Dark)
   Palette:
     sidebar-bg    #161b22    sidebar-border  #30363d
     sidebar-text  #c9d1d9    sidebar-muted   #6e7681
     content-bg    #0d1117    surface         #161b22
     border        #30363d    border-focus    #ff6b5b
     text          #c9d1d9    text-muted      #8b949e
     accent-fg     #ff6b5b    accent-fg-hover #ff8573
     accent-fill   #c0392b    accent-fill-hover #a93226    accent-fill-press #922b21
     accent-light  #3d1f1a
     success       #3fb950    warning         #d29922
   ════════════════════════════════════════════════════════════════════ */

/* ── Base ───────────────────────────────────────────────────────────── */
QWidget {
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 11pt;
    color: #c9d1d9;
    background-color: #0d1117;
}
QLabel { background-color: transparent; }
QMainWindow { background-color: #0d1117; }

/* ── Dark sidebar ───────────────────────────────────────────────────── */
QFrame#vertical_navigation {
    background-color: #161b22;
    border: none;
    border-right: 1px solid #30363d;
}
QFrame#vertical_navigation QLabel {
    color: #c9d1d9;
    background-color: transparent;
}
QFrame#vertical_navigation QWidget { background-color: transparent; }
QFrame#vertical_navigation QPushButton {
    background-color: transparent;
    border: none;
    color: #6e7681;
    border-radius: 6px;
    padding: 6px;
}
QFrame#vertical_navigation QPushButton:hover {
    background-color: rgba(177, 186, 196, 0.12);
    color: #c9d1d9;
}

/* ── Tabs ───────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    border-top: 1px solid #30363d;
    background-color: #0d1117;
}
QTabBar               { background-color: #161b22; }
QTabBar::tab {
    background-color: #161b22;
    color: #8b949e;
    padding: 9px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected           { color: #ff6b5b; border-bottom: 2px solid #ff6b5b; font-weight: 600; }
QTabBar::tab:hover:!selected    { color: #c9d1d9; background-color: #21262d; }
QTabBar::tab:disabled           { color: #484f58; }

/* ── Standard button ────────────────────────────────────────────────── */
QPushButton {
    background-color: #0d1117;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 16px;
    min-height: 30px;
    font-weight: 500;
}
QPushButton:hover    { background-color: #21262d; border-color: #484f58; }
QPushButton:pressed  { background-color: #2d333b; }
QPushButton:focus    { border-color: #ff6b5b; outline: none; }
QPushButton:disabled { color: #6e7681; background-color: #0d1117; border-color: #21262d; }

/* Primary action — writes to the device */
QPushButton#btn_save,
QPushButton#btn_add {
    background-color: #c0392b;
    color: #ffffff;
    border: 1px solid #a93226;
    font-weight: 600;
}
QPushButton#btn_save:hover,
QPushButton#btn_add:hover   { background-color: #a93226; border-color: #922b21; }
QPushButton#btn_save:pressed,
QPushButton#btn_add:pressed { background-color: #922b21; }
QPushButton#btn_save:focus,
QPushButton#btn_add:focus   { border-color: #7b241c; outline: none; }
QPushButton#btn_save:disabled,
QPushButton#btn_add:disabled { background-color: #3a2220; color: #8b6a66; border-color: #4a2a26; }

/* Destructive — removes data from the device */
QPushButton#btn_delete,
QPushButton#btn_reset {
    background-color: transparent;
    color: #ff6b5b;
    border: 1px solid #ff6b5b;
}
QPushButton#btn_delete:hover,
QPushButton#btn_reset:hover   { background-color: #c0392b; color: #ffffff; }
QPushButton#btn_delete:pressed,
QPushButton#btn_reset:pressed { background-color: #922b21; border-color: #922b21; color: #ffffff; }

/* ── Lists ──────────────────────────────────────────────────────────── */
QListWidget,
QTreeWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    outline: none;
    padding: 4px;
}
QListWidget::item,
QTreeWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    color: #c9d1d9;
    min-height: 24px;
}
QListWidget::item:selected       { background-color: #3d1f1a; color: #ff6b5b; }
QListWidget::item:hover:!selected { background-color: #21262d; }

/* Tree item — left accent bar instead of platform selection glyph */
QTreeWidget::item:selected {
    background-color: #3d1f1a;
    color: #ff6b5b;
    border-left: 3px solid #ff6b5b;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}
QTreeWidget::item:hover:!selected { background-color: #21262d; }

/* Override Windows system-accent color in the branch indent area */
QTreeWidget::branch                                          { background-color: #161b22; border-image: none; image: none; }
QTreeWidget::branch:selected                                 { background-color: #3d1f1a; border-image: none; image: none; }
QTreeWidget::branch:hover:!selected                          { background-color: #21262d;  border-image: none; image: none; }
QTreeWidget::branch:!selected:!has-siblings:!adjoins-item    { background-color: #21262d;  border-image: none; image: none; }
QTreeWidget::branch:has-siblings:!adjoins-item               { background-color: transparent; border-image: none; image: none; }
QTreeWidget::branch:has-siblings:adjoins-item                { background-color: transparent; border-image: none; image: none; }
QTreeWidget::branch:!has-children:!has-siblings:adjoins-item { background-color: transparent; border-image: none; image: none; }
QTreeWidget::branch:closed:has-children:has-siblings         { border-image: none; image: none; }
QTreeWidget::branch:has-children:!has-siblings:closed        { border-image: none; image: none; }
QTreeWidget::branch:open:has-children:has-siblings           { border-image: none; image: none; }
QTreeWidget::branch:has-children:!has-siblings:open          { border-image: none; image: none; }
QHeaderView::section                { background-color: #0d1117; border: none; border-bottom: 1px solid #30363d; padding: 6px 10px; color: #8b949e; font-weight: 600; }

/* ── Inputs ─────────────────────────────────────────────────────────── */
QLineEdit {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
    color: #c9d1d9;
    selection-background-color: #3d1f1a;
    selection-color: #c9d1d9;
}
QLineEdit:focus     { border: 1px solid #768390; outline: none; }
QLineEdit:read-only { background-color: #0d1117; color: #8b949e; }
QLineEdit:read-only:focus { border-color: #30363d; }
QLineEdit:disabled  { background-color: #0d1117; color: #6e7681; border-color: #21262d; }

QComboBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 30px;
    color: #c9d1d9;
}
QComboBox:focus          { border: 1px solid #768390; outline: none; }
QComboBox::drop-down     { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    selection-background-color: #3d1f1a;
    selection-color: #ff6b5b;
    outline: none;
    padding: 4px;
}

/* ── Checkboxes ─────────────────────────────────────────────────────── */
QCheckBox           { spacing: 8px; color: #c9d1d9; background-color: transparent; }
QStackedWidget#algorithm_tab,
QWidget#algorithm_edit,
QWidget#algorithm_show { background-color: transparent; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #30363d;
    border-radius: 4px;
    background-color: #161b22;
}
QCheckBox::indicator:checked            { background-color: #161b22; border: 2px solid #ff6b5b; }
QCheckBox::indicator:checked:disabled   { background-color: #0d1117; border: 2px solid #5c2b24; }
QCheckBox::indicator:unchecked:disabled { background-color: #0d1117; border-color: #30363d; }

/* ── Cards / panels ─────────────────────────────────────────────────── */
QFrame#__credential_show_frame,
QFrame#settings_frame,
QFrame#___nk3_info_space,
QFrame#frame_more_options {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 4px;
}

/* ── Status / info bar ──────────────────────────────────────────────── */
QFrame#information_frame {
    background-color: #161b22;
    border-top: 1px solid #30363d;
}

/* ── Dialogs ────────────────────────────────────────────────────────── */
QDialog           { background-color: #161b22; }
QMessageBox       { background-color: #161b22; }
QInputDialog      { background-color: #161b22; }
QDialog QLabel,
QMessageBox QLabel,
QInputDialog QLabel {
    background-color: transparent;
    color: #c9d1d9;
}
QMessageBox QPushButton,
QInputDialog QPushButton,
QDialogButtonBox QPushButton { min-width: 88px; }

/* ── Error dialog — monospace log view ──────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #010409;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px;
    font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
    font-size: 10pt;
    selection-background-color: #1f3a52;
    selection-color: #c9d1d9;
}

/* ── TOTP countdown ─────────────────────────────────────────────────── */
QProgressBar#otp_timeout_progress {
    background-color: #21262d;
    border: none;
    border-radius: 3px;
    text-align: center;
    font-size: 9pt;
    color: #8b949e;
    min-height: 10px;
    max-height: 10px;
}
QProgressBar#otp_timeout_progress::chunk { background-color: #3fb950; border-radius: 2px; }

/* ── App-level loading progress bar ─────────────────────────────────── */
QProgressBar#progress_bar {
    background-color: #21262d;
    border: none;
    border-radius: 0;
    text-align: center;
    font-size: 10pt;
    color: #8b949e;
    min-height: 18px;
    max-height: 18px;
}
QProgressBar#progress_bar::chunk { background-color: #ff6b5b; }

/* ── Scroll bars ────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover        { background-color: #545d68; }
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical            { height: 0; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical            { background: none; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #30363d;
    border-radius: 4px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover      { background-color: #545d68; }
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal          { width: 0; }

/* ── Scroll areas ───────────────────────────────────────────────────── */
QScrollArea,
QScrollArea > QWidget > QWidget { background-color: transparent; border: none; }

/* ── Welcome tab cards ──────────────────────────────────────────────── */
QFrame#introduction,
QFrame#frame_version,
QFrame#frame_help {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 4px;
}

/* Welcome tab labels */
QLabel#info_1 { color: #c9d1d9; font-size: 10pt; font-weight: 600; }
QLabel#info_2,
QLabel#info_3 { color: #8b949e; font-size: 10pt; padding-left: 12px; }
QLabel#Version { color: #8b949e; font-weight: 600; font-size: 10pt; }
QLabel#VersionNr { color: #c9d1d9; font-size: 10pt; font-weight: 600; }

/* ── More options accordion toggle ──────────────────────────────────── */
QPushButton#btn_more_options {
    background-color: transparent;
    border: none;
    color: #8b949e;
    font-weight: 600;
    padding: 4px 2px;
    text-align: left;
}
QPushButton#btn_more_options:hover   { color: #c9d1d9; }
QPushButton#btn_more_options:checked { color: #ff6b5b; }

/* ── Form field labels (muted — visually subordinate to values) ─────── */
QLabel#username_label,
QLabel#password_label,
QLabel#comment_label,
QLabel#is_pin_protection_label,
QLabel#is_touch_protection_label,
QLabel#current_password_label,
QLabel#new_password_label,
QLabel#repeat_password_label {
    color: #8b949e;
    font-weight: 600;
}

/* ── Section headlines inside cards ────────────────────────────────── */
QLabel#headline_label,
QLabel#nk3_label {
    color: #c9d1d9;
    font-size: 13pt;
    font-weight: 700;
    padding-bottom: 4px;
}

/* ── Overview tab info card field labels ────────────────────────────── */
QLabel#___uuid_label,
QLabel#___path_label,
QLabel#___version_label,
QLabel#___variant_label,
QLabel#status_label {
    color: #8b949e;
    font-weight: 600;
}

/* ── Security warning text (PIN retry count, destructive actions) ───── */
QLabel#warning_label {
    color: #f0b86e;
    background-color: #2b2111;
    border: 1px solid #6b4a1f;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 10pt;
}

/* ── Informational footnote text ────────────────────────────────────── */
QLabel#info_label {
    color: #8b949e;
    font-size: 10pt;
    line-height: 1.4;
}

/* ── Tooltips ───────────────────────────────────────────────────────── */
QToolTip {
    background-color: #010409;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 10pt;
}
"""


def _stylesheet_for_scheme(scheme: Qt.ColorScheme) -> str:  # type: ignore [name-defined]
    return _STYLESHEET_DARK if scheme == Qt.ColorScheme.Dark else _STYLESHEET_LIGHT  # type: ignore [attr-defined]


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setDesktopFileName("com.nitrokey.nitrokey-app2")
    app.setFont(QFont("Segoe UI", 11))

    style_hints = app.styleHints()

    def apply_stylesheet(scheme: Qt.ColorScheme) -> None:  # type: ignore [name-defined]
        app.setStyleSheet(_stylesheet_for_scheme(scheme))

    apply_stylesheet(style_hints.colorScheme())  # type: ignore [attr-defined]
    style_hints.colorSchemeChanged.connect(apply_stylesheet)  # type: ignore [attr-defined]

    with init_logging() as log_file:
        log_environment()

        window = GUI(app, log_file)

        def refresh_theme() -> None:
            # Qt's platform theme detection isn't always settled yet during
            # startup, so the stylesheet/icons set above can briefly use the
            # wrong variant; re-resolve both once the event loop is running
            apply_stylesheet(style_hints.colorScheme())  # type: ignore [attr-defined]
            window.refresh_themed_icons()

        QTimer.singleShot(0, refresh_theme)
        with exception_handler(window.trigger_handle_exception.emit):
            app.exec()


if __name__ == "__main__":
    main()
