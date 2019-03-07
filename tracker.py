#!/usr/bin/env python
# coding=utf-8

"""
Tracker - Mobile device tracker

NOTE: iPhones only sporadically answer pings when on WiFi as (I presume) a power-saving measure
      If an iPhone fails to answer a ping for > 60sec, it's probably not in WiFi range anymore
      If it answers immediately, it's in WiFi range (duh)

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

USE_THREADING = False
USE_PYPING = False


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


class Tracker(threading.Thread):
    def __init__(self, args, config, notifier):
        super(Tracker, self).__init__()
        self._args = args
        self._config = config
        self._monitored_devices = config.devices_details()["monitored_devices"]
        self._notifer = notifier
        positive_poll_period = config.general_details()["positive_poll_period"]
        negative_poll_period = config.general_details()["negative_poll_period"]
        self._poll = Periodic(negative_poll_period, self.poll_devices, "poll_devices", notifier=notifier)
        redis_info = config.redis_details()
        self._rdb = redis.StrictRedis(host=redis_info["host"], port=redis_info["port"], db=redis_info["db_no"])
        self._roll_call = {}
        return

    def any_detected(self):
        for thisDevice, presence in self._roll_call.items():
            if presence:
                return True
        return False

    def poll_devices(self):
        roll_call = {}
        redis_info = config.redis_details()
        previously_detected = self.any_detected()
        any_detected = False
        for name, address in self._monitored_devices.items():
            self._notifer.diagnostic("pinging %s at %s" % (name, address))
            found = self.ping(address)
            if found:
                any_detected = True
                roll_call[name] = True
                self._notifer.note("%s found" % name)
            else:
                roll_call[name] = False
                self._notifer.note("%s missing" % name)
                if previously_detected:
                    self._poll.reset()

        # set up next poll
        if any_detected and not previously_detected:
            self._poll.set_period(config.general_details()["positive_poll_period"])
        elif not any_detected and previously_detected:
            self._poll.set_period(config.general_details()["negative_poll_period"])

        self._roll_call = roll_call
        self._rdb.set(redis_info["key_detail"], json.dumps(roll_call))
        self._rdb.set(redis_info["key_summary"], json.dumps(any_detected))
        return

    def ping(self, ip_address):
        # NOTE: ping requires root access.  Fake it during development with a random#
        if hasattr(args, 'test') and args.test:
            found = (random.randint(0, 3) == 3)
        elif USE_PYPING:
            response = pyping.ping(ip_address)
            found = (response.ret_code == 0)
        else:
            response = os.system("ping -c i %s" % ip_address)
            found = (response == 0)
        return found

    def roll_call(self):
        return self._roll_call

    def check(self):
        self._poll.check()
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
    # noinspection PyTypeChecker
    tracker = Tracker(args, config, notifier)
    if USE_THREADING:
        tracker.start()
    else:
        try:
            while True:
                tracker.check()
                # notifier.note("roll call: %s" % tracker.roll_call())
                time.sleep(1)
        except KeyboardInterrupt:
            gRunningFlag = False
            pass
    print("Tracker end")
