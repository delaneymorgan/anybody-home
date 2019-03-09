#!/usr/bin/env python
# coding=utf-8

"""
State Chart Engine - heirarchical state machine engine

"""

from enum import Enum


# =============================================================================


class InconsistentStateChart(Exception):
    def __init__(self, parent, child):
        self.parent = parent
        self.child = child

    def __str__(self):
        return "Inconsistent StateChart parent: %s and child: %s" % (self.parent.name, self.child.name)


# =============================================================================


class FiniteState(object):
    """
    The base class for all state machine states
    """

    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        self._state_id = state_id
        self._notifier = notifier
        self._evergreen_vars = evergreen_vars
        self._transitions = []
        return

    def diagnostic(self, string):
        """
        log to the notifier

        :param string: the string to be logged
        :return:
        """
        if self._notifier:
            self._notifier.diagnostic(string)
        return

    def name(self):
        """
        return the state's name

        :return: the state's name
        """
        return self._state_id.name

    def set_transitions(self, transitions):
        """
        allows the decendents to set their allowable transitions

        :param transitions: the list of transitions, in order of priority
        :return:
        """
        self._transitions = transitions
        return

    def entry(self, current_data=None):
        """
        The default state entry method

        :param current_data: the application data
        :return:
        """
        _ = current_data
        self.diagnostic("%s entry" % self._state_id.name)
        return

    def exit(self, current_data=None):
        """
        The default state exit method

        :param current_data: the application data
        :return:
        """
        _ = current_data
        self.diagnostic("%s exit" % self._state_id.name)
        return

    def transitioning(self, current_data=None):
        """
        check transitions in order of priority

        :param current_data: the application data
        :return: the stateID of the successful transition, otherwise None
        """
        for thisCheck in self._transitions:  # type: dict
            if thisCheck["check"](current_data):
                return thisCheck["stateID"]
        return None

    def steady(self, current_data=None):
        """
        The default state steady method, executed each iteration

        :param current_data: the application data
        :return:
        """
        self.diagnostic("%s steady" % self._state_id.name)
        return self.transitioning(current_data)


# =============================================================================


class StateChartEngine(object):
    """
    The state chart engine
    """

    def __init__(self, state_chart, notifier=None, evergreen_vars=None):
        self._state_chart = state_chart
        self._notifier = notifier
        self._evergreen_vars = evergreen_vars
        self._state = []
        self._state_instances = {}
        self.check()
        return

    def check(self):
        """
        checks stateChart for consistency
        :return: Nothing
        """
        # Every child has a parent that exists
        for child_id in self._state_chart:
            child_info = self._state_chart[child_id]
            if "parent" in child_info:
                parent_id = child_info["parent"]
                if parent_id not in self._state_chart:
                    raise InconsistentStateChart(parent_id, child_id)
        # anyone with a defaultChild must have that child acknowledge them
        for parent_id in self._state_chart:
            parent_info = self._state_chart[parent_id]
            if "defaultChild" in parent_info:
                child_id = parent_info["defaultChild"]
                if child_id not in self._state_chart:
                    raise InconsistentStateChart(parent_id, child_id)
                child_info = self._state_chart[child_id]
                if child_info["parent"] != parent_id:
                    raise InconsistentStateChart(parent_id, child_id)
        return

    def _notify(self, string):
        """
        log to the notifier

        :param string: the string to be logged
        :return:
        """
        if self._notifier:
            notifier.diagnostic(string)
        return

    def state_instance(self, state_id):
        """
        returns the state's instance, creating it if necessary

        :param state_id: the state id
        :return: the state's instance
        """
        if state_id not in self._state_instances:
            state_info = self._state_chart[state_id]
            self._state_instances[state_id] = state_info["stateClass"](state_id, self._notifier, self._evergreen_vars)
        return self._state_instances[state_id]

    def _set_state(self, state_id, current_data=None):
        """
        sets the specified state, drilling down into the hierarchy if required using recursion

        :param state_id: the state to be set
        :return:
        """
        cur_state = self.state_instance(state_id)
        cur_state.entry(current_data)
        self._state.append(state_id)
        state_info = self._state_chart[state_id]
        if "defaultChild" in state_info:
            self.init(state_info["defaultChild"])
        return

    def init(self, state_id):
        """
        set the initial state of the state machine

        :param state_id: the initial state
        :return:
        """
        self._set_state(state_id)
        return

    def state(self):
        """
        return the current state stack

        :return: the current state stack
        """
        return self._state

    def state_names(self):
        """
        return a string showing the current state stack

        :return: the string depicting current states
        """
        sn_string = "["
        first = True
        for this_state in self._state:
            if not first:
                sn_string += ", "
            first = False
            sn_string += this_state.name
        sn_string += "]"
        return sn_string

    def iterate(self, current_data=None, level=0):
        """
        Perform a single iteration of the state machine

        :param current_data: the application data
        :param level: which level of the hierarchy to perform the iteration on
        :return: True => terminate state machine, False => continue
        """
        terminate = False
        cur_state_id = self._state[level]
        cur_state = self.state_instance(cur_state_id)
        new_state_id = cur_state.steady(current_data)
        for state_index in range((level + 1), len(self._state)):
            terminate = self.iterate(current_data, (level + 1))
        if not terminate and new_state_id:
            num_states = len(self._state)
            for state_index in reversed(range(level, num_states)):
                this_state = self.state_instance(self._state[state_index])
                this_state.exit(current_data)
                self._state.pop()
            if new_state_id.value == 0:
                terminate = True
            else:
                self._set_state(new_state_id, current_data)
        return terminate


# =============================================================================


"""
Top Level States:
================
Sitting
Walking
Running

Second Level States:
===================
Walking:ChewingGum
Walking:Whistling

Transitions:
===========
Sitting -> Running (on panicked = True and tired = False)
Sitting -> tired = false if sitCount > 5
Sitting -> Walking (on restless = True)
Walking -> Walking:ChewingGum
Walking:ChewingGum -> Walking:Whistling (on chewCount > 5)
Walking:Whistling -> Walking:ChewingGum (on whistleCount > 5)
Walking -> Running (on panicked = True)
Running -> Sitting (on panicked = False, or tired = True)

"""

import json
import random
import time


class AppStates(Enum):
    Terminating = 0  # Special-case state - used to terminate state machine (until I think of something nicer)
    Sitting = 1
    Walking = 2
    Running = 3
    ChewingGum = 4
    Whistling = 5


class BitTongueError(Exception):
    def __init__(self, state_id, error_msg):
        self.stateID = state_id
        self.errorMsg = error_msg

    def __str__(self):
        return "BitTongueError: state: %s, msg: %s" % (self.stateID.name, self.errorMsg)


# =============================================================================


class ChewingGumState(FiniteState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(ChewingGumState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.Whistling, check=self.check_whistling))
        self.set_transitions(checks)
        self.chewingGumCount = 0
        return

    def entry(self, current_data=None):
        super(ChewingGumState, self).entry(current_data)
        self.chewingGumCount = 0
        return

    def check_whistling(self, current_data=None):
        _ = current_data
        if self.chewingGumCount < 5:
            return False
        return True

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        self.chewingGumCount += 1
        self.diagnostic("chewingGumCount: %d" % self.chewingGumCount)
        if random.randint(0, 20) == 5:
            # ouch, that was bad luck
            raise BitTongueError(self._state_id, "Ouch!  That hurt!")
        return self.transitioning(current_data)


# =============================================================================


class WhistlingState(FiniteState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(WhistlingState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.ChewingGum, check=self.check_chewing_gum))
        self.set_transitions(checks)
        self.whistleCount = 0
        return

    def entry(self, current_data=None):
        super(WhistlingState, self).entry(current_data)
        self.whistleCount = 0
        return

    def check_chewing_gum(self, current_data=None):
        _ = current_data
        if self.whistleCount < 5:
            return False
        return True

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        self.whistleCount += 1
        self.diagnostic("whistleCount: %d" % self.whistleCount)
        return self.transitioning(current_data)


# =============================================================================


# noinspection PyMethodMayBeStatic
class SittingState(FiniteState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(SittingState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.Walking, check=self.check_walking))
        checks.append(dict(stateID=AppStates.Running, check=self.check_running))
        self.set_transitions(checks)
        self.sittingCount = None
        return

    def entry(self, current_data=None):
        super(SittingState, self).entry(current_data)
        self.sittingCount = 0
        return

    def check_walking(self, current_data=None):
        if not current_data["panicked"] and current_data["restless"] and not current_data["tired"]:
            return True
        return False

    def check_running(self, current_data=None):
        if current_data["panicked"] and not current_data["tired"]:
            return True
        return False

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        self.sittingCount += 1
        if self.sittingCount > 5:
            current_data["restless"] = True
            current_data["tired"] = False
        self.diagnostic("sittingCount: %d" % self.sittingCount)
        return self.transitioning(current_data)


# =============================================================================


# noinspection PyMethodMayBeStatic
class WalkingState(FiniteState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(WalkingState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.Sitting, check=self.check_sitting))
        checks.append(dict(stateID=AppStates.Running, check=self.check_running))
        self.set_transitions(checks)
        return

    def entry(self, current_data=None):
        super(WalkingState, self).entry(current_data)
        return

    def check_sitting(self, current_data=None):
        if not current_data["restless"] and not current_data["panicked"] and current_data["tired"]:
            return True
        return False

    def check_running(self, current_data=None):
        if current_data["panicked"]:
            return True
        return False

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        return self.transitioning(current_data)


# =============================================================================


# noinspection PyMethodMayBeStatic
class RunningState(FiniteState):
    # noinspection PyDictCreation
    def __init__(self, state_id, notifier=None, evergreen_vars=None):
        super(RunningState, self).__init__(state_id, notifier, evergreen_vars)
        checks = list()
        checks.append(dict(stateID=AppStates.Sitting, check=self.check_sitting))
        checks.append(dict(stateID=AppStates.Walking, check=self.check_walking))
        self.set_transitions(checks)
        self.runCount = 0
        return

    def entry(self, current_data=None):
        super(RunningState, self).entry(current_data)
        self.runCount = 0
        return

    def check_sitting(self, current_data=None):
        if current_data["tired"] and current_data["panicked"]:
            return True
        return False

    def check_walking(self, current_data=None):
        if not current_data["tired"] and not current_data["panicked"]:
            return True
        return False

    def steady(self, current_data=None):
        self.diagnostic("%s steady" % self._state_id.name)
        if self.runCount > 5:
            current_data["tired"] = True
            current_data["restless"] = False
        self.runCount += 1
        self.diagnostic("runCount: %d" % self.runCount)
        return self.transitioning(current_data)


# =============================================================================


class Notifier(object):
    def __init__(self, verbose):
        self.verbose = verbose
        return

    def diagnostic(self, string):
        if self.verbose:
            print(string)
        return


def random_bool():
    return bool(random.getrandbits(1))


STATE_CHART = dict()
STATE_CHART[AppStates.Sitting] = dict(stateClass=SittingState)
STATE_CHART[AppStates.Walking] = dict(defaultChild=AppStates.ChewingGum, stateClass=WalkingState)
STATE_CHART[AppStates.Running] = dict(stateClass=RunningState)
STATE_CHART[AppStates.ChewingGum] = dict(parent=AppStates.Walking, stateClass=ChewingGumState)
STATE_CHART[AppStates.Whistling] = dict(parent=AppStates.Walking, stateClass=WhistlingState)

if __name__ == "__main__":
    print("SCE Start")
    notifier = Notifier(True)
    sce = StateChartEngine(STATE_CHART, notifier)
    terminated = False
    app_data = dict(tired=random_bool(), panicked=random_bool(), restless=random_bool())
    sce.init(AppStates.Sitting)
    iteration_no = 0
    while not terminated:
        if random.randint(0, 100) < 10:
            app_data["panicked"] = random_bool()
        print("Iteration: %d: appData: %s, state: %s" % (iteration_no, json.dumps(app_data), sce.state_names()))
        try:
            terminated = sce.iterate(app_data)
        except BitTongueError as e:
            print(str(e))
            terminated = True
        iteration_no += 1
        time.sleep(0.1)
    print("SCE End")
