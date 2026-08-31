"""Our own messages for the errors the device libraries report.

The exceptions of nitrokey-sdk-py and python-fido2 carry English log text that
is reworded between releases, so the mapping keys on the status codes and error
enums instead. Anything unmapped falls back to a generic message that carries
the original text along. See docs/translations.md.
"""

import logging

from fido2.ctap import CtapError
from nitrokey.nk3.secrets_app import SecretsAppException, SecretsAppExceptionID
from nitrokey.trussed.updates import Warning
from PySide6.QtCore import QCoreApplication

logger = logging.getLogger(__name__)


def passwords_unsupported_message() -> str:
    """Shared wording for the many jobs that need the Passwords application."""
    return QCoreApplication.translate("errors", "This device does not support Passwords.")


def user_message(exc: BaseException) -> str:
    """A message for `exc` that can be shown to the user, in their language."""
    if isinstance(exc, SecretsAppException):
        message = _secrets_app_message(exc)
    elif isinstance(exc, CtapError):
        message = _ctap_message(exc)
    else:
        message = None

    if message is not None:
        return message

    detail = str(exc).strip()
    if not detail:
        return QCoreApplication.translate("errors", "The operation failed.")
    return QCoreApplication.translate("errors", "The operation failed: {0}").format(detail)


def warning_message(warning: Warning) -> str:
    """A message for a firmware update warning, keyed by its stable id."""
    messages = {
        Warning.IFS_MIGRATION_V2: QCoreApplication.translate(
            "errors",
            "There is not enough space on the internal filesystem of the device to perform "
            "the firmware update. The release notes explain how to free some up: {0}",
        ).format("https://github.com/Nitrokey/nitrokey-3-firmware/releases/tag/v1.8.2"),
        Warning.MISSING_STATUS: QCoreApplication.translate(
            "errors",
            "The state of the device cannot be determined because its firmware is too old. "
            "Please update to firmware version v1.3.1 first.",
        ),
        Warning.SDK_VERSION: QCoreApplication.translate(
            "errors",
            "The Nitrokey SDK this application was built with is too old for the device. "
            "Please update the Nitrokey App and try again.",
        ),
        Warning.UPDATE_FROM_BOOTLOADER: QCoreApplication.translate(
            "errors",
            "The state of the device cannot be checked because it is already in bootloader "
            "mode. Please review the release notes before continuing: {0}",
        ).format("https://github.com/Nitrokey/nitrokey-3-firmware/releases"),
    }
    message = messages.get(warning)
    if message is None:
        logger.warning(f"no message for update warning {warning}")
        return warning.message
    return message


def _secrets_app_message(exc: SecretsAppException) -> str | None:
    try:
        code = exc.to_id()
    except ValueError:
        logger.warning(f"unknown Passwords status code {exc.code}")
        return None

    messages = {
        SecretsAppExceptionID.VerificationFailed: QCoreApplication.translate(
            "errors", "The PIN is not correct."
        ),
        SecretsAppExceptionID.OperationBlocked: QCoreApplication.translate(
            "errors",
            "The PIN is blocked because it was entered incorrectly too often. "
            "A factory reset of Passwords is needed to use it again.",
        ),
        SecretsAppExceptionID.SecurityStatusNotSatisfied: QCoreApplication.translate(
            "errors", "The PIN has to be entered before this operation."
        ),
        SecretsAppExceptionID.ConditionsOfUseNotSatisfied: QCoreApplication.translate(
            "errors", "The operation was not confirmed on the device."
        ),
        SecretsAppExceptionID.NotFound: QCoreApplication.translate(
            "errors", "The credential was not found on the device."
        ),
        SecretsAppExceptionID.NotEnoughMemory: QCoreApplication.translate(
            "errors", "There is not enough space left on the device for another credential."
        ),
        SecretsAppExceptionID.IncorrectDataParameter: QCoreApplication.translate(
            "errors", "The device rejected the data sent."
        ),
        SecretsAppExceptionID.WrongLength: QCoreApplication.translate(
            "errors", "The device rejected the data sent."
        ),
        SecretsAppExceptionID.FunctionNotSupported: QCoreApplication.translate(
            "errors", "This device does not support the requested operation."
        ),
        SecretsAppExceptionID.InstructionNotSupportedOrInvalid: QCoreApplication.translate(
            "errors", "This device does not support the requested operation."
        ),
        SecretsAppExceptionID.ClassNotSupported: QCoreApplication.translate(
            "errors", "This device does not support the requested operation."
        ),
    }

    message = messages.get(code)
    if message is None:
        logger.info(f"no message for Passwords status {code.name}")
    return message


def _ctap_message(exc: CtapError) -> str | None:
    error = CtapError.ERR
    messages = {
        error.PIN_INVALID: QCoreApplication.translate("errors", "The FIDO2 PIN is not correct."),
        error.PIN_BLOCKED: QCoreApplication.translate(
            "errors",
            "The FIDO2 PIN is blocked because it was entered incorrectly too often. "
            "A factory reset of FIDO2 is needed to use it again.",
        ),
        error.PIN_AUTH_BLOCKED: QCoreApplication.translate(
            "errors",
            "The FIDO2 PIN was entered incorrectly too often. Please remove the Nitrokey, "
            "insert it again and retry.",
        ),
        error.PIN_AUTH_INVALID: QCoreApplication.translate(
            "errors", "The FIDO2 PIN authentication failed."
        ),
        error.PIN_NOT_SET: QCoreApplication.translate(
            "errors", "No FIDO2 PIN is set on this device."
        ),
        error.PIN_POLICY_VIOLATION: QCoreApplication.translate(
            "errors", "The new FIDO2 PIN does not meet the requirements of the device."
        ),
        error.PIN_TOKEN_EXPIRED: QCoreApplication.translate(
            "errors", "The FIDO2 PIN has to be entered again."
        ),
        error.PUAT_REQUIRED: QCoreApplication.translate(
            "errors", "The FIDO2 PIN has to be entered before this operation."
        ),
        error.NO_CREDENTIALS: QCoreApplication.translate(
            "errors", "There are no passkeys stored on this device."
        ),
        error.KEY_STORE_FULL: QCoreApplication.translate(
            "errors", "There is no space left on the device for another passkey."
        ),
        error.USER_ACTION_TIMEOUT: QCoreApplication.translate(
            "errors", "The Nitrokey was not touched in time. Please try again."
        ),
        error.ACTION_TIMEOUT: QCoreApplication.translate(
            "errors", "The Nitrokey was not touched in time. Please try again."
        ),
        error.UP_REQUIRED: QCoreApplication.translate(
            "errors", "The operation has to be confirmed by touching the Nitrokey."
        ),
        error.OPERATION_DENIED: QCoreApplication.translate(
            "errors", "The device refused the operation."
        ),
        error.KEEPALIVE_CANCEL: QCoreApplication.translate(
            "errors", "The operation was cancelled."
        ),
        error.NOT_ALLOWED: QCoreApplication.translate(
            "errors", "The device does not allow this operation."
        ),
        error.UV_BLOCKED: QCoreApplication.translate(
            "errors", "The fingerprint check is blocked. Please use the FIDO2 PIN instead."
        ),
        error.UNSUPPORTED_OPTION: QCoreApplication.translate(
            "errors", "This device does not support the requested operation."
        ),
        error.INVALID_OPTION: QCoreApplication.translate(
            "errors", "This device does not support the requested operation."
        ),
        error.INVALID_COMMAND: QCoreApplication.translate(
            "errors", "This device does not support the requested operation."
        ),
    }

    message = messages.get(exc.code)
    if message is None:
        logger.info(f"no message for CTAP error {exc.code!r}")
    return message
