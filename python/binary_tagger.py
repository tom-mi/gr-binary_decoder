#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Thomas Reifenberger.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#


import numpy
from gnuradio import gr
import pmt


class binary_tagger(gr.sync_block):
    """
    docstring for block binary_tagger
    """

    def __init__(self, key='binary_transmission', max_quiet_samples=100):
        gr.sync_block.__init__(self,
                               name="binary_tagger",
                               in_sig=[numpy.int8, ],
                               out_sig=[numpy.int8, ])

        self._key = key
        self._max_quiet_samples = max_quiet_samples
        self._is_transmission = False
        self._position_of_last_signal = -1

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]

        offset = self.nitems_written(0)

        for i, value in enumerate(in0):
            position = offset + i
            if value != 0:
                self._position_of_last_signal = position
            if not self._is_transmission:
                if value != 0:
                    self.add_item_tag(0, position, pmt.string_to_symbol(self._key), pmt.to_pmt(True))
                    self._is_transmission = True
            else:
                if position - self._position_of_last_signal > self._max_quiet_samples:
                    self._is_transmission = False
                    self.add_item_tag(0, position, pmt.string_to_symbol(self._key), pmt.to_pmt(False))

        out[:] = in0

        return len(output_items[0])
