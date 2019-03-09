#!/usr/bin/env python
# coding=utf-8

"""
anybody-home - A service to register if a user(s) is home or not

NOTE: iPhones only sporadically answer pings when on WiFi as (I presume) a power-saving measure
      If an iPhone fails to answer a ping for > 60sec, it's probably not in WiFi range anymore
      If it answers immediately, it's in WiFi range (duh)

© Delaney & Morgan Computing 2019
www.delaneymorgan.com.au
"""

import argparse
from enum import Enum
import json
import os
import pyping
import random
import redis
import time

from periodic import Periodic
from config import AnybodyHomeConfig
from notifier import Notifier
from sce import StateChartEngine, FiniteState

__VERSION__ = "1.0.0"

CONFIG_FILENAME = "config.ini"

USE_THREADING = False
USE_PYPING = False


# =============================================================================


class AppStates(Enum):
    MAYBE = 0  # Special-case state - used to terminate state machine (until I think of something nicer)
    AWAY = 1
    HOME = 2


# =============================================================================


class Pinger(object):
    def __init__(self, args, config, notifier=None):
        super(Pinger, self).__init__()
        self._args = args
        self._config = config
        self._notifer = notifier
        self.lastResult = False
        return

    def ping(self, ip_address):
        if self._notifer:
            self._notifer.diagnostic("pinging: %s" % ip_address)
        # NOTE: ping requires root access.  Fake it during development with a random#
        if hasattr(self._args, 'test') and self._args.test:
            found = (random.randint(0, 3) == 3)
        elif USE_PYPING:
            response = pyping.ping(ip_address)
            found = (response.ret_code == 0)
        else:
            response = os.system("ping -c i %s" % ip_address)
            found = (response == 0)
        if self._notifer:
            self._notifer.diagnostic("pinged: %s - %s" % (ip_address, found))
        return found


# =============================================================================


class AnybodyHomeState(FiniteState):
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(AnybodyHomeState, self).__init__(state_id, notifier, evergreen_vars)
        self.config = evergreen_vars["config"]
        self.pinger = evergreen_vars["pinger"]
        self.poll_check = None
        return

    def exit(self, current_data=None):
        del self.poll_check
        return

    def poll(self, current_data):
        roll_call = {}
        anybody_home = False
        monitored_devices = self.config.device_details()["monitored_devices"]
        for name, address in monitored_devices.items():
            response = self.pinger.ping(address)
            roll_call[name] = response
            if response:
                anybody_home = True
        current_data["roll_call"] = roll_call
        current_data["anybody_home"] = anybody_home
        return


# =============================================================================


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic
class MaybeState(AnybodyHomeState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(MaybeState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.HOME, check=self.check_home))
        checks.append(dict(stateID=AppStates.AWAY, check=self.check_away))
        self.set_transitions(checks)
        return

    def entry(self, current_data=None):
        super(MaybeState, self).entry(current_data)
        poll_period = self.config.polling_details()["maybe_period"]
        self.poll_check = Periodic(poll_period, self.poll, "HomeState.poll")
        return

    def check_away(self, current_data=None):
        _ = current_data
        return True

    def check_home(self, current_data=None):
        _ = current_data
        return True

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        return self.transitioning(current_data)


# =============================================================================


# noinspection PyMethodMayBeStatic
class AwayState(AnybodyHomeState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(AwayState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.HOME, check=self.check_home))
        checks.append(dict(stateID=AppStates.MAYBE, check=self.check_maybe))
        self.set_transitions(checks)
        return

    def entry(self, current_data=None):
        super(AwayState, self).entry(current_data)
        current_data["anybody_home"] = False
        poll_period = self.config.polling_details()["negative_period"]
        self.poll_check = Periodic(poll_period, self.poll, "HomeState.poll")
        return

    def check_maybe(self, current_data=None):
        _ = current_data
        return True

    def check_home(self, current_data=None):
        _ = current_data
        return True

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        return self.transitioning(current_data)


# =============================================================================


# noinspection PyMethodMayBeStatic
class HomeState(AnybodyHomeState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(HomeState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.MAYBE, check=self.check_maybe))
        self.set_transitions(checks)
        return

    def entry(self, current_data=None):
        super(HomeState, self).entry(current_data)
        current_data["anybody_home"] = True
        poll_period = self.config.polling_details()["positive_period"]
        self.poll_check = Periodic(poll_period, self.poll, "HomeState.poll")
        return

    def check_maybe(self, current_data=None):
        if current_data["anybody_home"]:
            return True
        return False

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        self.poll_check.check(current_data)
        return self.transitioning(current_data)


# =============================================================================


def arg_parser():
    """
    parse arguments

    :return: the parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='anybody-home.  A service to register if a user is home.')
    parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    parser.add_argument("-d", "--diagnostic", help="diagnostic mode (includes verbose)", action="store_true")
    parser.add_argument("-t", "--test", help="use fake pings for simulation", action="store_true")
    parser.add_argument("--version", action="version", version='%(prog)s {version}'.format(version=__VERSION__))
    args = parser.parse_args()
    return args


# =============================================================================


STATE_CHART = dict()
STATE_CHART[AppStates.MAYBE] = dict(stateClass=MaybeState)
STATE_CHART[AppStates.AWAY] = dict(stateClass=AwayState)
STATE_CHART[AppStates.HOME] = dict(stateClass=HomeState)


# =============================================================================


def run_state_machine(sce, config, notifier):
    terminated = False
    redis_info = config.redis_details()
    rdb = redis.StrictRedis(host=redis_info["host"], port=redis_info["port"], db=redis_info["db_no"])
    app_data = dict(roll_call={}, anybody_home=False)
    sce.init(AppStates.MAYBE)
    iteration_no = 0
    while not terminated:
        notifier.note("Iteration: %d: appData: %s, state: %s" % (iteration_no, json.dumps(app_data), sce.state_names()))
        terminated = sce.iterate(app_data)
        rdb.set(redis_info["key_detail"], json.dumps(app_data["roll_call"]))
        rdb.set(redis_info["key_summary"], json.dumps(app_data["anybody_home"]))
        iteration_no += 1
        time.sleep(0.5)
    return


# =============================================================================


def main():
    args = arg_parser()
    notifier = Notifier(args)
    config = AnybodyHomeConfig(CONFIG_FILENAME)
    pinger = Pinger(args, config, notifier)
    sce = StateChartEngine(STATE_CHART, notifier, evergreen_vars=dict(pinger=pinger, config=config))
    run_state_machine(sce, config, notifier)
    return


if __name__ == "__main__":
    main()
