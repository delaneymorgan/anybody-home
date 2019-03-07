#!/usr/bin/env python
# coding=utf-8

"""
Periodic module

© Delaney & Morgan Computing 2019
www.delaneymorgan.com.au
"""

import math
import threading
import time


gRunningFlag = True


# =============================================================================


class Periodic(object):
    def __init__(self, period, task, name=None, notifier=None):
        self.period = period
        self.task = task
        self.name = name
        self.notifier = notifier
        self.start_time = time.time()
        self.num_periods = -1
        self.last_time = 0
        return

    def check(self):
        time_now = time.time()
        elapsed_periods = math.floor((time_now - self.start_time) / self.period)
        remainder = (time_now - self.start_time) % self.period
        time_left = max(0, (self.period - remainder))
        if elapsed_periods > self.num_periods:
            self.num_periods += 1
            self.last_time = time_now
            if self.name is not None:
                if self.notifier is not None:
                    self.notifier.diagnostic("doing %s" % self.name)
                else:
                    print("doing %s" % self.name)
            self.task()
            return time_left
        return time_left


# =============================================================================


class Thread1(threading.Thread):
    # noinspection PyUnresolvedReferences
    def __init__(self):
        super(Thread1, self).__init__()
        self.start_time = time.time()
        self.periodic1 = Periodic(10, self.do_task1)
        return

    def do_task1(self):
        elapsed = time.time() - self.start_time
        print("doTask1: %5.1f" % elapsed)
        return

    def run(self):
        while gRunningFlag:
            left1 = self.periodic1.check()
            print("Thread1: sleeping for: %5.4f sec" % left1)
            time.sleep(left1)
        return


# =============================================================================


class Thread2(threading.Thread):
    # noinspection PyUnresolvedReferences
    def __init__(self):
        super(Thread2, self).__init__()
        self.start_time = time.time()
        self.periodic2 = Periodic(15, self.do_task2)
        self.periodic3 = Periodic(5, self.do_task3)
        return

    def do_task2(self):
        elapsed = time.time() - self.start_time
        print("doTask2: %5.1f" % elapsed)
        return

    def do_task3(self):
        elapsed = time.time() - self.start_time
        print("doTask3: %5.1f" % elapsed)
        return

    def run(self):
        while gRunningFlag:
            left2 = self.periodic2.check()
            left3 = self.periodic3.check()
            sleep_time = min(left2, left3)
            print("Thread2: sleeping for: %5.4f sec" % sleep_time)
            time.sleep(sleep_time)
        return


# =============================================================================


if __name__ == "__main__":
    print("Periodic start")
    thread1 = Thread1()
    thread2 = Thread2()
    try:
        thread1.start()
        thread2.start()
        while True:
            pass
    except KeyboardInterrupt:
        gRunningFlag = False
        pass
    print("Periodic end")
