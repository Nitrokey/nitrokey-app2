# -*- coding: utf-8 -*-
#
# Copyright 2019 SoloKeys Developers
#
# Licensed under the Apache License, Version 2.0, <LICENSE-APACHE or
# http://apache.org/licenses/LICENSE-2.0> or the MIT license <LICENSE-MIT or
# http://opensource.org/licenses/MIT>, at your option. This file may not be
# copied, modified, or distributed except according to those terms.

import logging
import sys

from numbers import Number
from threading import Event, Timer
from typing import List
from getpass import getpass

from pynitrokey.confconsts import GH_ISSUES_URL, SUPPORT_EMAIL, LOG_FN
from pynitrokey.confconsts import VERBOSE, Verbosity

STDOUT_PRINT = True

def to_websafe(data):
    data = data.replace("+", "-")
    data = data.replace("/", "_")
    data = data.replace("=", "")
    return data


def from_websafe(data):
    data = data.replace("-", "+")
    data = data.replace("_", "/")
    return data + "=="[: (3 * len(data)) % 4]


class Timeout(object):
    """
    Utility class for adding a timeout to an event.
    :param time_or_event: A number, in seconds, or a threading.Event object.
    :ivar event: The Event associated with the Timeout.
    :ivar timer: The Timer associated with the Timeout, if any.
    """

    def __init__(self, time_or_event):
        if isinstance(time_or_event, Number):
            self.event = Event()
            self.timer = Timer(time_or_event, self.event.set)
        else:
            self.event = time_or_event
            self.timer = None

    def __enter__(self):
        if self.timer:
            self.timer.start()
        return self.event

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.join()
            self.timer.cancel()


# @todo: introduce granularization: dbg, info, err (warn?)
#        + machine-readable
#        + logfile-only (partly solved)
def local_print(*messages, **kwargs):
    """
    application-wide logging function
    `messages`:   `str`         -> log single string
                  `Exception`   -> log exception
                  `list of ...` -> list of either `str` or `Exception` handle serialized
    """
    passed_exc = None
    logger = logging.getLogger()

    for item in messages:
        # handle exception in order as, if it is a regular message
        if isinstance(item, Exception):
            logger.exception(item)
            passed_exc = item
            item = repr(item)
            item = 'Exception encountered: ' + item

        # just a newline, don't log to file...
        elif item is None or item == "":
            item = ""

        # logfile debug output
        else:
            whereto = "print: " if STDOUT_PRINT else ""
            logger.debug(f"{whereto}{str(item).strip()}")

        # to stdout
        if STDOUT_PRINT:
            print(item, **kwargs)

    # handle `passed_exc`: re-raise on debug verbosity!
    if VERBOSE == Verbosity.debug and passed_exc:
        raise passed_exc


def local_critical(*messages, support_hint=True, ret_code=1, **kwargs):
    global STDOUT_PRINT
    messages = ["Critical error:"] + list(messages)
    local_print(*messages, **kwargs)
    if support_hint:

        # list all connected devices to logfile
        # @fixme: not the best solution
        STDOUT_PRINT = False
        local_print("listing all connected devices:")
        from pynitrokey.cli import nitropy
        nitropy.commands["ls"].callback()
        STDOUT_PRINT = True

        local_print(
            "", "-" * 80,
            "Critical error occurred, exiting now",
            "Unexpected? Is this a bug? Do you would like to get support/help?",
            f"- You can report issues at: {GH_ISSUES_URL}",
            f"- Writing an e-mail to: {SUPPORT_EMAIL} is also possible",
            f"- Please attach the log: '{LOG_FN}' with any support/help request!",
            "-" * 80, "")
    sys.exit(ret_code)


# @fixme: consider using/wrapping click.confirm() instead of this...
class AskUser:
    """
    Asking user for input:
        `question`:       printed user question
        `options`:        `None`        -> we want some data input
                          `iter of str` -> only allow items inside iterable
        `strict`:         if `options` are used, force full match
        `repeat`:         ask `question` up to `repeat` times, if `options` are provided
        `adapt_question`: adapt user-provided `question` (add options, whitespace...),
                          set to `False`, if strictly `question` shall be used
        `hide_input`:     use 'getpass' instead of regular `input`
    """
    def __init__(self, question: str,
                 options: List[str]=None,
                 strict: bool=False,
                 repeat: int=3,
                 adapt_question=True,
                 hide_input=False):

        self.data = None

        self.question = question
        self.adapt_question = adapt_question
        self.final_question = question
        if self.adapt_question:
            _q = self.final_question
            # strip ending colon(s) ':' or whitespace(s) ' '
            _q = _q.strip(" ").strip(":").strip(" ").strip(":")
            if options:
                _q += f" [{'/'.join(options)}]" if strict else \
                      f" [{'/'.join(f'({o[0]}){o[1:]}' for o in options)}]"
            _q += ": "
            self.final_question = _q

        self.options = options
        self.strict = strict
        self.repeat = repeat or 1
        self.hide_input = hide_input

    @classmethod
    def yes_no(cls, what: str, strict: bool=False):
        opts = ["yes", "no"]
        return cls(what, options=opts, strict=strict).ask() == opts[0]

    @classmethod
    def strict_yes_no(cls, what: str):
        return cls.yes_no(what, strict=True)

    @classmethod
    def plain(cls, what):
        return cls(what).ask()

    @classmethod
    def hidden(cls, what):
        return cls(what, hide_input=True).ask()

    def get_input(self, pre_str=None, hide_input=None):
        pre_input_string = pre_str or self.final_question
        hide_input = hide_input if hide_input is not None else self.hide_input
        return input(pre_input_string).strip() if not hide_input \
            else getpass(pre_input_string)

    def ask(self):
        answer = self.get_input()

        # handle plain input request first
        if not self.options:
            self.data = answer
            return self.data

        # now `options` based
        retries = self.repeat
        while retries:
            if answer in self.options:
                self.data = answer
                return self.data

            if not self.strict:
                short_opts = {c[0].lower(): c for c in self.options}
                if len(answer) > 0:
                    self.data = short_opts.get(answer[0].lower())

                if self.data:
                    local_print(f"choosing: {self.data}")
                    return self.data

            answer = self.get_input()
            retries -= 1

        if retries == 0:
            local_critical("max tries exceeded - exiting...")

        assert self.data is None, "expecting `self.data` to be None at this point!"
        return self.data
