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
        'Disabled':     'DISABLED',
        'Rising Edge':  'EDGE_RISING',
        'Falling Edge': 'EDGE_FALLING',
        'Both Edges':   'EDGE_BOTH'
    }

    # Types of level-sensitive triggers. Should match the sensitivity enum in GreatFET's gpio_int.h.
    LEVEL_TRIGGER_MODES = {
        'Disabled':     'DISABLED',
        'High':         'LEVEL_HIGH',
        'Low':          'LEVEL_LOW'
    }

    # We currently support up to 8 conditions for simple triggers.
    # This can be arbitrarily upped in the GreatFET firmware.
    MAX_EDGE_CONDITIONS  = 8
    MAX_LEVEL_CONDITIONS = 8


    def _add_condition_params(self, param_path, number, trigger_types, expanded=False):
        param = self.findParam(param_path)

        # Add the nodes to our UI...
        param.addChildren([
            {'name': 'Condition {}'.format(number), 'key': '{}'.format(number), 'type': 'group', 'expanded': expanded, 'children': [
                {'name': 'Edge',  'key':'mode',  'type':'list', 'values': trigger_types,       'value': trigger_types[0], 'action': self._update_condition_list},
                {'name': 'Input', 'key':'input', 'type':'list', 'values': self.available_pins, 'value': self.available_pins[0], 'action': self._update_condition_list}
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
        self.condition_list = None

        # Create the skeleton for our dialog...
        self.params.addChildren([
            {'name': 'Trigger Mode', 'key':'mode', 'type':'list', 'values': self.TRIGGER_MODES, 'value': self.TRIGGER_MODES[0]},
            {'name': 'Target Count', 'key':'count', 'type':'int', 'range': (0, (2**32) - 1), 'step': 1, 'value': 10},
            {'name': 'Trigger Output', 'key':'trigger_out', 'type':'list', 'values': self.TRIGGER_OUTPUT_MODES, 'value': self.TRIGGER_OUTPUT_MODES[0]},
            {'name': 'Edge Triggers (OR\'d)', 'key':'edges', 'type':'group', 'expanded':True, 'children':[]},
            {'name': 'Level Triggers (AND\'d)', 'key':'levels', 'type':'group', 'expanded':True, 'children':[]},
        ])

        # Add each of our condition fields...
        for i in range(self.MAX_EDGE_CONDITIONS):
            self._add_condition_params(['edges'], i + 1, self.EDGE_TRIGGER_MODES.keys(), i == 0)
        for i in range(self.MAX_LEVEL_CONDITIONS):
            self._add_condition_params(['levels'], i + 1, self.LEVEL_TRIGGER_MODES.keys(), i == 0)


    def _con(self, scope=None):

        # Create a new GreatFET connection.
        # FIXME: Handle boards not found!
        self.greatfet = greatfet.GreatFET()

        # Grab the list of available pins we can used.
        self.available_pins = sorted(self.greatfet.gpio.get_available_pins())
        self.update_available_pin_list()

        # ... and grab the trigger module we'll be using.
        self.trigger_module = self.greatfet.glitchkit.simple


    def update_available_pin_list(self):
        """
        Update the values of any fields that depend on a pin listing from the GreatFET.
        """

        for field in self.pin_fields:
            param = self.findParam(field)
            param.setLimits(self.available_pins)


    def close(self):
        pass



    def _get_data_for_condition(self, type, number):
        """
        Fetches data relevant to a given condition.

        Args:
            type -- The type of condition to read. Should be 'edges' or 'levels', to match the UI.
            number -- The condition number to read. Should match the number in the UI.

        Returns:
            [(mode, pin)] -- A list containing the 2-tuple
                provided to the GlitchKit python library to trigger the given event.
        """

        # Figure out which mode collection we should be looking in.
        collection = self.EDGE_TRIGGER_MODES if type == 'edges' else self.LEVEL_TRIGGER_MODES

        # Get the raw values for the relevant input.
        raw_mode = self.findParam([type, '{}'.format(number), 'mode']).getValue()
        raw_pin  = self.findParam([type, '{}'.format(number), 'input']).getValue()

        # For simplicity, if this isn't a valid entry, don't include it in the list.
        if (raw_mode == 'Disabled') or (raw_pin == '-'):
            return []

        # Convert the mode to the string accepted by the GreatFET UI.
        mode = collection[raw_mode]

        return [(mode, raw_pin)]


    def _build_condition_list(self):
        """
        Builds a condition list that encapsulates the UI in a way that
        can be understood by the GreatFET/GlitchKit API.

        Returns:
            a condition list suitable for passing to prime_trigger_on_event_count.
        """

        # Start a new list of conditions.
        conditions = []

        # Iterate over all of the UI elements, and grab their values.
        for i in range(self.MAX_EDGE_CONDITIONS):
            conditions.extend(self._get_data_for_condition('edges',  i + 1))
            conditions.extend(self._get_data_for_condition('levels', i + 1))

        return conditions


    def _update_condition_list(self, _=None):
        """
        Marks the condition list as no longer valid. Should be called whenever the
        UI options change.
        """
        self.condition_list = self._build_condition_list()

        print("New list: {}".format(self.condition_list))


    def readOutput(self):
        # TODO:
        # Run a python script to generate a result, and post it to the
        # glitch monitor? Or is this doable enough with just the Aux panel?

        # Always return none, as we don't participate in the encryption/CPA.
        return None


    def go(self):
        """
        Runs a single trigger iteration.
        """

        # Grab the non-condition paramters. The condition parameters should be automatically
        # squeezed into self.condition_list on any update, to avoid read spurts.
        target_count = self.findParam(['count']).getValue()

        # ... and prime the trigger.
        self.trigger_module.prime_trigger_on_event_count(target_count, self.condition_list)

