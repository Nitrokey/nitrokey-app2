# -*- coding: utf-8 -*-
#
# Copyright 2019 SoloKeys Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.
#

"""Python Library for Nitrokey FIDO2 & Nitrokey Start."""

import pathlib


__version_path__ = pathlib.Path(__file__).parent.resolve().absolute() / "VERSION"
__version__ = open(__version_path__).read().strip()


del pathlib
__all__ = ["client", "commands", "dfu", "enums", "exceptions", "helpers", "operations"]
