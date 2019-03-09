#!/usr/bin/env python
# coding=utf-8

"""
notifier - notification module

© Delaney & Morgan Computing 2019
www.delaneymorgan.com.au
"""

import argparse
import os
import sys
import time


# =============================================================================


class Notifier(object):
    def __init__(self, args):
        self._args = args
        return

    @staticmethod
    def _inform(string):
        print("%s: %s" % (time.strftime("%Y/%m/%d %H:%M:%S"), string))
        sys.stdout.flush()  # force print to flush
        return

    def note(self, string):
        if self._args.verbose or self._args.diagnostic:
            self._inform(string)
        return

    def warning(self, string):
        self._inform("Warning: %s" % string)
        return

    def error(self, string):
        self._inform("Error: %s" % string)
        return

    def diagnostic(self, string):
        if self._args.diagnostic:
            self._inform("Diagnostic: %s" % string)
        return

    def fatal(self, string):
        self._inform("Fatal: %s" % string)
        # noinspection PyProtectedMember
        os._exit(1)
        return


# =============================================================================


def arg_parser():
    """
    parse arguments

    :return: the parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Notifier - unit test.')
    parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    parser.add_argument("-d", "--diagnostic", help="diagnostic mode (includes verbose)", action="store_true")
    args = parser.parse_args()
    return args


def main():

    args = arg_parser()
    notifier = Notifier(args)
    notifier.note("This is a note")
    notifier.error("This is an warning")
    notifier.error("This is an error")
    notifier.diagnostic("This is a diagnostic")
    notifier.fatal("This is a fatal")
    return


if __name__ == "__main__":
    main()
