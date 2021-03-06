#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import re
import subprocess

from subprocess import Popen
from subprocess import check_output

from pyraspcontrol.lib import constants

_FREE_PATTERN = r'\s+([0-9]+)'
_MAX_USED_SWAP = 80
_WARNING_MEMORY_THRESHOLD = 80


def _execute_free():
    return check_output(['free', '-mo']).strip('\n').split('\n')


def _execute_ps():
    # ps -e -o pmem,user,args --sort=-pmem | sed "/^ 0.0 /d" | head -5
    ps = Popen(['ps', '-e', '-o', 'pmem,user,args', '--sort=-pmem'], stdout=subprocess.PIPE)
    ps = Popen(['sed', '/^ 0.0 /d'], stdin=ps.stdout, stdout=subprocess.PIPE)
    ps = Popen(['head', '-%d' % constants.HEAD_LIMIT], stdin=ps.stdout, stdout=subprocess.PIPE)
    return ps.communicate()[0]


def _parse_ps_data(index):
    try:
        return map(int, re.findall(_FREE_PATTERN, _execute_free()[index]))
    except OSError:
        return None


def get_ram_info():
    ram_data = _parse_ps_data(1) or (1, 0, 0, 0, 0, 0,)
    total, used, free, shared, buffers, cached = ram_data
    data = {
        'total': total,
        'used': used - buffers - cached,
        'free': free + buffers + cached,
        'shared': shared,
        'buffers': buffers,
        'cached': cached,
        'details': _execute_ps() or {},
        'alert': constants.SUCCESS,
    }
    data['percentage'] = int(round((data['used'] / total) * 100))
    if data['percentage'] >= _WARNING_MEMORY_THRESHOLD:
        data['alert'] = constants.WARNING
    return data


def get_swap_info():
    ram_data = _parse_ps_data(2) or (1, 0, 0)
    total, used, free = ram_data
    data = {
        'total': total,
        'used': used,
        'free': free,
        'percentage': int(round(used / total)),
        'alert': constants.SUCCESS,
    }
    if data['percentage'] > _MAX_USED_SWAP:
        data['alert'] = constants.DANGER
    return data
