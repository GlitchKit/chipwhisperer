#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) <copyright here>
# Copyright (c) 2017, NewAE Technology Inc
# All rights reserved.
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.chipwhisperer.com . ChipWhisperer is a registered
# trademark of NewAE Technology Inc in the US & Europe.
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================
import logging
import time

import greatfet

from _base import TargetTemplate
from chipwhisperer.common.utils import pluginmanager
from chipwhisperer.common.utils.parameter import setupSetParam

class GlitchKitUART(TargetTemplate):
    """

    """

    _name = "GlitchKit UART"

    # Maximum baud rate we can operate at.
    MAX_BAUD = 2000000

    # TODO: Make me a dictionary for easy configuration.
    DATA_BIT_MODES = [ '8 Bits', '9 Bits' ]
    PARITY_MODES = [ 'None', 'Odd', 'Even ']
    STOP_MODES = ['1 Bit', '2 Bits']

    # TODO: Expand
    TRIGGER_MODES = ['String Match']
    TRIGGER_COMM_MODS = ['GlitchKit Neighbor']

    def __init__(self):
        TargetTemplate.__init__(self)

        self.greatfet = None
        self.baud_rate = 115200

        self.params.addChildren([
            {'name': 'Trigger Mode', 'key':'addr', 'type':'list', 'values': self.TRIGGER_MODES, 'value': self.TRIGGER_MODES[0]},
            {'name':'UART Configuration', 'key':'uart', 'type':'group', 'expanded':True, 'children':[
                {'name': 'Baud Rate', 'key': 'baud', 'type': 'int', 'range': (1, self.MAX_BAUD), 'value': 115200},
                {'name': 'Parity',   'key': 'parity', 'type': 'list', 'values': self.PARITY_MODES, 'value': self.PARITY_MODES[0] },
                {'name': 'Data Bits', 'key': 'data', 'type': 'list', 'values': self.DATA_BIT_MODES, 'value': self.DATA_BIT_MODES[0] },
                {'name': 'Stop Bits', 'key': 'stop', 'type': 'list', 'values': self.STOP_MODES, 'value': self.STOP_MODES[0] },
            ]},
            {'name':'Trigger Settings', 'key':'trigger', 'type':'group', 'expanded':True, 'children':[
                {'name': 'Trigger String', 'key':'string', 'type':'str', 'value':'"\n"'},
                {'name': 'Trigger Routing', 'key':'routing', 'type':'list', 'values': self.TRIGGER_COMM_MODS, 'value': self.TRIGGER_COMM_MODS[0]},
            ]},
        ])




    def _con(self, scope=None):
        self.greatfet = greatfet.GreatFET()

    def close(self):
        pass

    def go(self):
        return
