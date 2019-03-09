#!/usr/bin/env python
# coding=utf-8

"""
Herald Configuration Parser

Loads configuration from config.ini and produces a configuration dictionary.

© Delaney & Morgan Computing 2019
www.delaneymorgan.com.au
"""

import configparser
import json
from enum import Enum


# =============================================================================


class Sections(Enum):
    POLLING = 1
    REDIS = 2
    DEVICES = 3


# Defines the various required configuration members and their types.
POLLING_MEMBERS = {'positive_period': 'float', 'negative_period': 'float', 'maybe_period': 'float'}
REDIS_MEMBERS = {'host': 'string', 'port': 'integer', 'db_no': 'integer', 'key_detail': 'string',
                 'key_summary': 'string'}
DEVICES_MEMBERS = {'monitored_devices': 'dict'}


# =============================================================================


class HeraldConfig:
    config = {}

    # A list of parsers for given data types. Note that many are non-standard types that
    # we do special case handling for.
    configTypeParsers = {
        'dict': lambda self, settings, section, member: eval(settings.get(section, member)),
        'list': lambda self, settings, section, member: eval(settings.get(section, member)),
        'string': lambda self, settings, section, member: settings.get(section, member),
        'integer': lambda self, settings, section, member: settings.getint(section, member),
        'bool': lambda self, settings, section, member: settings.getboolean(section, member),
        'float': lambda self, settings, section, member: settings.getfloat(section, member),
    }

    # noinspection PyUnresolvedReferences
    def __init__(self, filename='config.ini'):
        self.filename = filename
        settings = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        settings.read(self.filename)

        self.config[Sections.POLLING] = self._read_section(settings, Sections.POLLING.name, POLLING_MEMBERS)
        self.config[Sections.REDIS] = self._read_section(settings, Sections.REDIS.name, REDIS_MEMBERS)
        self.config[Sections.DEVICES] = self._read_section(settings, Sections.DEVICES.name, DEVICES_MEMBERS)
        return

    def _read_section(self, settings, section_name, members):
        values = {}
        for member, member_type in members.items():
            values[member] = self._parse_config_entry(settings, section_name, member, member_type)
        return values

    def _parse_config_entry(self, settings, section, member, member_type):
        return self.configTypeParsers[member_type](self, settings, section, member)

    def polling_details(self):
        return self.config[Sections.POLLING]

    def redis_details(self):
        return self.config[Sections.REDIS]

    def device_details(self):
        return self.config[Sections.DEVICES]


# =============================================================================


if __name__ == "__main__":
    cfg = HeraldConfig()
    print(json.dumps(cfg.config, indent=4))
