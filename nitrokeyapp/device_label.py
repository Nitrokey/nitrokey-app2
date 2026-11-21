import logging
import unicodedata

from nitrokey.trussed import TrussedDevice

logger = logging.getLogger(__name__)

LABEL_CONFIG_KEY = "admin.label"

# DEVICE_LABEL_LEN in the firmware, counted in UTF-8 bytes
LABEL_MAX_BYTES = 32

# The firmware stores any UTF-8, so the app keeps out line breaks and bidi overrides
_BIDI_CONTROLS = frozenset("\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def _is_forbidden(char: str) -> bool:
    return unicodedata.category(char) in ("Cc", "Cs", "Zl", "Zp") or char in _BIDI_CONTROLS


def _displayed_char(char: str) -> str:
    if char in _BIDI_CONTROLS:
        return ""
    if _is_forbidden(char):
        return " "
    return char


def sanitize_label(label: str) -> str:
    # no whitespace collapsing: a valid label must be shown exactly as stored
    return "".join(map(_displayed_char, label)).strip()


def validate_label(label: str) -> str | None:
    if any(_is_forbidden(char) for char in label):
        return (
            "The label must not contain line breaks, control characters or text direction "
            "overrides."
        )
    size = len(label.encode())
    if size > LABEL_MAX_BYTES:
        return (
            f"The label is too long ({size} of {LABEL_MAX_BYTES} bytes). "
            "Characters such as ä or emoji take up more than one byte."
        )
    return None


def read_label(device: TrussedDevice) -> str | None:
    try:
        if not device.admin.has_config(LABEL_CONFIG_KEY):
            return None
        return device.admin.get_config(LABEL_CONFIG_KEY)
    except Exception as e:
        # a broken label must never keep a device from being listed
        logger.warning(f"Failed to read the device label: {e}")
        return None
