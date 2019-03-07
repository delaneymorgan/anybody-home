#!/usr/bin/env python
# coding=utf-8

"""
Tracker - Mobile device tracker

© Delaney & Morgan Computing 2019
www.delaneymorgan.com.au
"""


import argparse
import json
import os
import pyping
import random
import redis
import sys
import threading
import time

from periodic import Periodic
from config import HomerConfig


__VERSION__ = "1.0.0"

CONFIG_FILENAME = "config.ini"


# =============================================================================


class Notifier(object):
    def __init__(self, args):
        self._args = args
        return

    def note(self, string):
        if self._args.verbose or self._args.diagnostic:
            print(string)
        return

    def warning(self, string):
        print("Warning: %s" % string)
        return

    def error(self, string):
        print("Error: %s" % string)
        return

    def diagnostic(self, string):
        if self._args.diagnostic:
            print("Diagnostic: %s" % string)
        return

    def fatal(self, string):
        print("Fatal: %s" % string)
        sys.stdout.flush()  # force print to flush
        # noinspection PyProtectedMember
        os._exit(1)
        return


# =============================================================================


class Tracker(threading.Thread):
    def __init__(self, args, config, notifier):
        super(Tracker, self).__init__()
        self._args = args
        self._config = config
        self._monitored_devices = config.devices_details()["monitored_devices"]
        self._notifer = notifier
        positive_poll_period = config.general_details()["positive_poll_period"]
        negative_poll_period = config.general_details()["negative_poll_period"]
        self._positive_poll = Periodic(positive_poll_period, self.poll_devices, "positive_poll")
        self._negative_poll = Periodic(negative_poll_period, self.poll_devices, "negative_poll")
        redis_info = config.redis_details()
        self._rdb = redis.StrictRedis(host=redis_info["host"], port=redis_info["port"], db=redis_info["db_no"])
        self._db_key = redis_info["key"]
        self._last_poll = {}
        return

    def any_detected(self):
        for thisDevice, presence in self._last_poll.items():
            if presence:
                return True
        return False

    def poll_devices(self):
        survey = {}
        for name,address in self._monitored_devices.items():
            self._notifer.diagnostic("pinging %s at %s" % (name, address))
            found = self.ping(address)
            if found:
                survey[name] = True
                self._notifer.note("%s found" % name)
            else:
                survey[name] = False
                self._notifer.note("%s missing" % name)
        self._last_poll = survey
        self._rdb.set(self._db_key, json.dumps(survey))
        return

    def ping(self, ip_address):
        # NOTE: ping requires root access.  Fake it during development with a random#
        if hasattr(args, 'test') and args.test:
            found = (random.randint(0, 3) == 3)
        else:
            response = pyping.ping(ip_address)
            found = (response.ret_code == 0)
        return found

    def roll_call(self):
        return self._last_poll

    def check(self):
        if self.any_detected():
            self._positive_poll.check()
        else:
            self._negative_poll.check()
        return

    def run(self):
        while gRunningFlag:
            self.check()
        return


# =============================================================================


def arg_parser():
    """
    parse arguments

    :return: the parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Tracker.')
    parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    parser.add_argument("-d", "--diagnostic", help="diagnostic mode (includes verbose)", action="store_true")
    parser.add_argument("-t", "--test", help="use fake pings for simulation", action="store_true")
    parser.add_argument("--version", action="version", version='%(prog)s {version}'.format(version=__VERSION__))
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    print("Tracker start")
    args = arg_parser()
    notifier = Notifier(args)
    config = HomerConfig(CONFIG_FILENAME)
    surveyor = Tracker(args, config, notifier)
    if False:
        roll_caller.start()
    else:
        try:
            while True:
                surveyor.check()
                notifier.note("roll call: %s" % surveyor.roll_call())
                time.sleep(5)
        except KeyboardInterrupt:
            gRunningFlag = False
            pass
    print("Tracker end")
