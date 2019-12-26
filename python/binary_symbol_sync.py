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


class binary_symbol_sync(gr.basic_block):
    """
    docstring for block binary_symbol_sync
    """

    def __init__(self,
                 samples_per_symbol=10,
                 max_deviation=2,
                 clock_smoothing_factor=0.5,
                 max_zero_symbols=10,
                 output_samples_per_symbol=1,
                 ):
        gr.basic_block.__init__(self,
                                name="binary_symbol_sync",
                                in_sig=[numpy.int8, ],
                                out_sig=[numpy.int8, ])
        self._samples_per_symbol = samples_per_symbol
        self._max_deviation = max_deviation
        self._clock_smoothing_factor = clock_smoothing_factor
        self._max_zero_symbols = max_zero_symbols
        self._output_samples_per_symbol = output_samples_per_symbol

        self.set_output_multiple(self._output_samples_per_symbol)

        # TODO check validity of deviation
        self._min_samples_per_symbol = self._samples_per_symbol - self._max_deviation
        self._max_samples_per_symbol = self._samples_per_symbol + self._max_deviation

        # internal block state
        self._is_locked = False
        self._current_samples_per_symbol = None
        self._zero_symbols = 0

    def forecast(self, noutput_items, ninput_items_required):
        # setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = int(
                noutput_items / self._output_samples_per_symbol) * self._max_samples_per_symbol + 1

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]

        relative_position = 0
        symbols_written = 0

        def _skip_empty():
            if numpy.all(in0[relative_position:] == 0):
                return len(in0)
            return numpy.argmax(in0[relative_position:] != 0)

        def _lock():
            self._is_locked = True
            self._current_samples_per_symbol = self._samples_per_symbol

        def _determine_current_symbol_length():
            best_symbol_length = None
            best_error = self._max_deviation * 2
            for i in range(self._min_samples_per_symbol, self._max_samples_per_symbol + 1):
                if in0[relative_position + i - 1] == 0 and in0[relative_position + i] != 0:
                    error = numpy.abs(i - self._current_samples_per_symbol)
                    print(f'... i={i} error={error}')
                    if error < best_error:
                        best_error = error
                        best_symbol_length = i
            if best_symbol_length is not None:
                self._update_current_samples_per_symbol(best_symbol_length)
                print(f'found i={best_symbol_length}, avg={self._current_samples_per_symbol}')
                return best_symbol_length
            return int(self._current_samples_per_symbol)

        def _send_symbol(length):
            if numpy.any(in0[relative_position:relative_position + length] != 0):
                self._zero_symbols = 0
            else:
                self._zero_symbols += 1
            symbol_offset = symbols_written * self._output_samples_per_symbol
            for i in range(self._output_samples_per_symbol):
                out0[symbol_offset + i] = in0[relative_position + int(length * i / self._output_samples_per_symbol)]

        print(f'pos={relative_position} len(in0)={len(in0)} len(out0)={len(out0)}')
        while (relative_position + self._max_samples_per_symbol < len(in0)
               and (symbols_written + 1) * self._output_samples_per_symbol <= len(out0)):
            if not self._is_locked:
                if in0[relative_position] == 0:
                    relative_position = _skip_empty()
                    print(f'skipping to pos={relative_position}')
                else:
                    _lock()
            else:
                if self._zero_symbols > self._max_zero_symbols:
                    self._is_locked = False
                    self._zero_symbols = 0
                else:
                    length = _determine_current_symbol_length()
                    print(f'locked, length={length}')
                    _send_symbol(length)
                    symbols_written += 1
                    relative_position += length

        # output_items[0][:] = input_items[0]
        self.consume(0, relative_position)  # self.consume_each(len(input_items[0]))
        print(f'consumed {relative_position} samples, symbols written: {symbols_written}')
        print('wrote samples', symbols_written * self._output_samples_per_symbol)
        return symbols_written * self._output_samples_per_symbol

    def _update_current_samples_per_symbol(self, new_value):
        alpha = self._clock_smoothing_factor
        self._current_samples_per_symbol = alpha * new_value + (1 - alpha) * self._current_samples_per_symbol