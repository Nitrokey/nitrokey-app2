import os

from nitrokey.trussed import should_default_ccid


def should_use_ccid() -> bool:
    force_ccid = os.environ.get("NITROKEY_FORCE_CCID")
    if force_ccid:
        return True
    else:
        return should_default_ccid()
