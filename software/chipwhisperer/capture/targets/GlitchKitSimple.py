#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) Katherine J. Temkin <k@ktemkin.com>
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
from greatfet.peripherals import gpio
from greatfet.protocol import vendor_requests

from _base import TargetTemplate
from chipwhisperer.common.utils import pluginmanager
from chipwhisperer.common.utils.parameter import setupSetParam

class GlitchKitSimple(TargetTemplate):
    """
    Simple trigger module for GlitchKit. Provides simple trigger conditions
    (e.g. "the SPI clock ticks 25 times while CE is high and WP is low") for quick construction
    of simple glitch conditions. This is suprisingly useful for how simple it is. :)
    """

    _name = "GlitchKit Simple Triggers"

    # For now, we only support event count mode.
    TRIGGER_MODES = ['Event Count']

    # Specify how we can output-- right now, this is either through the Indigo Neighbor or through a GPIO pin.
    # TODO: Support a GPIO pin.
    TRIGGER_OUTPUT_MODES = ['Indigo Neighbor']

    # Types of edge-sensitive triggers. Should match the sensitivity enum in GreatFET's gpio_int.h.
    EDGE_TRIGGER_MODES = {
        'Disabled':    -1,
        'Rising Edge':  2,
        'Falling Edge': 3,
        'Both Edges':   4
    }

    # Types of level-sensitive triggers. Should match the sensitivity enum in GreatFET's gpio_int.h.
    LEVEL_TRIGGER_MODES = {
        'Disabled':    -1,
        'High':         0,
        'Low':          1
    }

    # We currently support up to 8 conditions for simple triggers.
    # This can be arbitrarily upped in the GreatFET firmware.
    MAX_CONDITIONS = 8


    def _add_condition_params(self, param_path, number, trigger_types, expanded=False):
        param = self.findParam(param_path)

        # Add the nodes to our UI...
        param.addChildren([
            {'name': 'Condition {}'.format(number), 'key': '{}'.format(number), 'type': 'group', 'expanded': expanded, 'children': [
                {'name': 'Edge',  'key':'mode',  'type':'list', 'values': trigger_types,       'value': trigger_types[0]},
                {'name': 'Input', 'key':'input', 'type':'list', 'values': self.available_pins, 'value': self.available_pins[0]}
            ]}
        ])

        # ... and internally note the field's we've added that refer to GreatFET fields.
        input_param_path = param_path[:]
        input_param_path.extend(['{}'.format(number), 'input'])
        self.pin_fields.append(input_param_path)


    def __init__(self):
        TargetTemplate.__init__(self)
        self.greatfet = None
        self.pin_fields = []
        self.available_pins = ['-']

        # Create the skeleton for our dialog...
        self.params.addChildren([
            {'name': 'Trigger Mode', 'key':'mode', 'type':'list', 'values': self.TRIGGER_MODES, 'value': self.TRIGGER_MODES[0]},
            {'name': 'Trigger Output', 'key':'trigger_out', 'type':'list', 'values': self.TRIGGER_OUTPUT_MODES, 'value': self.TRIGGER_OUTPUT_MODES[0]},
            {'name': 'Edge Triggers (OR\'d)', 'key':'edges', 'type':'group', 'expanded':True, 'children':[]},
            {'name': 'Level Triggers (AND\'d)', 'key':'levels', 'type':'group', 'expanded':True, 'children':[]},
        ])

        # Add each of our condition fields...
        for i in range(self.MAX_CONDITIONS):
            self._add_condition_params(['edges'], i + 1, self.EDGE_TRIGGER_MODES.keys(), i == 0)
            self._add_condition_params(['levels'], i + 1, self.LEVEL_TRIGGER_MODES.keys(), i == 0)


    def _con(self, scope=None):

        # Create a new GreatFET connection.
        # FIXME: Handle boards not found!
        self.greatfet = greatfet.GreatFET()

        # Grab the list of available pins we can used.
        self.available_pins = sorted(self.greatfet.gpio.get_available_pins())
        self.update_available_pin_list()


    def update_available_pin_list(self):
        """
        Update the values of any fields that depend on a pin listing from the GreatFET.
        """

        for field in self.pin_fields:
            param = self.findParam(field)
            param.setLimits(self.available_pins)


    def close(self):
        pass

    def go(self):
        pass

        #target_count = self.findParam(['trigger', 'count']).getValue()

        #target_port = self.findParam(['trigger', 'port' ]).getValue()
        #target_pin = self.findParam(['trigger', 'pin']).getValue()
        #port_and_pin = (target_port << 8) | target_pin

        #self.greatfet.vendor_request_out(vendor_requests.GLITCHKIT_SIMPLE_SETUP, index=port_and_pin, value=target_count)
