#!/usr/bin/env python
# coding=utf-8


"""
Shared Variable module

© Delaney & Morgan Computing 2019
www.delaneymorgan.com.au
"""

import threading


# =============================================================================


class SharedVar(object):
    """
    Thread-safe variable
    """

    def __init__(self, value=None):
        self.value = value
        self.lock = threading.Lock()
        return

    def set(self, value):
        with self.lock:
            self.value = value
        return

    def get(self):
        with self.lock:
            return self.value

    def update(self, updater):
        with self.lock:
            self.value = updater(self.value)
        return


# =============================================================================


class SharedVarCollection(object):
    """
    thread-safe variable collection
    """

    def __init__(self, initial_values):
        self.collection = {}
        for this_name, this_value in initial_values.items():
            self.collection[this_name] = SharedVar(this_value)
        return

    def get(self, name=None):
        if name is not None:
            return self.collection[name].get()
        else:
            stats = {}
            for this_name, this_stat in self.collection.items():
                stats[this_name] = this_stat.get()
            return stats

    def set(self, name, value):
        if name not in self.collection:
            self.collection[name] = SharedVar(value)
        else:
            self.collection[name].set(value)
        return

    def update(self, name, updater):
        if name not in self.collection:
            self.collection[name] = SharedVar(0)
        self.collection[name].update(updater)
        return


# =============================================================================


if __name__ == "__main__":
    print("SharedVar start")
    count = SharedVar()
    count.set(1)
    num = count.get()
    if num != 1:
        print("Error")
    count.update(lambda x: x + 1)
    num = count.get()
    if num != 2:
        print("Error")

    initialValues = dict(count=0, memoryUsage=0, other=0)
    the_stats = SharedVarCollection(initialValues)
    fred = 123456
    the_stats.update("other", lambda x: x + fred)
    print(the_stats.get())
    the_stats.update("count", lambda x: x + 1)
    print(the_stats.get())
    the_stats.set("memoryUsage", 123456)
    print(the_stats.get())
    print(the_stats.get("count"))
    print(the_stats.get("memoryUsage"))
    print("SharedVar end")
