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
import itertools
from dataclasses import dataclass

import numpy
import typing

import pmt
from gnuradio import gr

PACKET_LENGTH_TAG_KEY = 'packet_len'


class binary_ppm_decoder(gr.basic_block):
    """
    docstring for block binary_ppm_decoder
    """

    def __init__(self, samples_per_pulse=10, samples_per_gap=(10, 20), max_deviation=1, max_packet_length=64):
        gr.basic_block.__init__(self,
                                name="binary_ppm_decoder",
                                in_sig=[numpy.int8, ],
                                out_sig=[numpy.int8, ])
        self._samples_per_pulse = samples_per_pulse
        self._samples_per_gap = numpy.array(list(samples_per_gap))
        self._max_deviation = max_deviation
        self._max_packet_length = max_packet_length
        self._validate_parameters()

        self.set_output_multiple(self._max_packet_length)

        # internal state
        self._last_positive_edge = None
        self._last_negative_edge = None
        self._pending_symbol = None
        self._pending_packet = []
        self._output_queue = []

    def _validate_parameters(self):
        if self._samples_per_pulse < 1 or not isinstance(self._samples_per_pulse, int):
            raise ValueError('samples_per_pulse must be a positive integer')
        if len(set(self._samples_per_gap)) < len(self._samples_per_gap) or \
                not issubclass(self._samples_per_gap.dtype.type, numpy.integer) or \
                numpy.any(self._samples_per_gap < 1):
            raise ValueError('samples_per_gap must be a list of distinct positive integers')
        if len(self._samples_per_gap) < 2:
            raise ValueError('samples_per_gap must have at least two elements')
        if self._max_deviation < 0 or type(self._max_deviation) != int:
            raise ValueError('max_deviation must be a non-negative integer')
        if self._max_packet_length < 1 or not isinstance(self._max_packet_length, int):
            raise ValueError('max_packet_length must be a positive integer')
        min_gap_distance = min([abs(y - x) for x, y in itertools.combinations(self._samples_per_gap, 2)])
        if min_gap_distance <= 2 * self._max_deviation:
            raise ValueError('difference between any 2 values in samples_per_gap must not be smaller '
                             'than 2 * max_deviation')

    def forecast(self, noutput_items, ninput_items_required):
        # setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = (noutput_items - self._max_packet_length + 1) * \
                                       (self._samples_per_pulse + int(numpy.min(self._samples_per_gap)))

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]

        normalized_input = numpy.abs(numpy.sign(in0))
        differential_input = numpy.diff(normalized_input)

        edges = list(numpy.argwhere(differential_input != 0))

        nitems_read = self.nitems_read(0)

        while len(edges) > 0 and \
                sum([len(packet) for packet in self._output_queue]) + self._max_packet_length <= len(out0):
            edge = edges.pop(0)
            edge_type = numpy.asscalar(differential_input[edge])
            if edge_type == 1:
                self._last_positive_edge = edge + nitems_read
                if self._last_negative_edge is not None:
                    gap = self._last_positive_edge - self._last_negative_edge
                    symbol = self._decode_gap_to_symbol(gap)
                    if symbol is not None:
                        self._pending_symbol = symbol
                    else:
                        self._pending_symbol = None
                        self._rotate_packet()
            elif edge_type == -1:
                self._last_negative_edge = None
                if self._last_positive_edge is not None:
                    pulse = edge + nitems_read - self._last_positive_edge
                    if numpy.abs(pulse - self._samples_per_pulse) <= self._max_deviation:
                        self._last_negative_edge = edge + nitems_read
                        self._push_symbol_to_current_packet()
                    else:
                        self._pending_symbol = None
                        self._rotate_packet()
            else:
                raise RuntimeError(f'Invalid edge type {edge_type}')

        if self._last_negative_edge is not None and self._last_negative_edge > (self._last_positive_edge or -1):
            gap = self.nitems_read(0) + len(differential_input) - self._last_negative_edge
            if gap > max(self._samples_per_gap) + self._max_deviation:
                self._rotate_packet()
        elif self._last_positive_edge is not None and self._last_positive_edge > (self._last_negative_edge or -1):
            pulse = self.nitems_read(0) + len(differential_input) - self._last_positive_edge
            if pulse > self._samples_per_pulse + self._max_deviation:
                self._rotate_packet()

        if len(edges) == 0:
            consumed = len(in0) - 1
        else:
            consumed = edges[0]
        sent_symbols = self._flush_packets(out0)

        self.consume(0, consumed)
        return sent_symbols

    def _decode_gap_to_symbol(self, gap):
        for symbol, expected_samples in enumerate(self._samples_per_gap):
            if numpy.abs(gap - expected_samples) <= self._max_deviation:
                return symbol
        return None

    def _push_symbol_to_current_packet(self):
        if self._pending_symbol is not None:
            self._pending_packet.append(self._pending_symbol)
            self._pending_symbol = None
            if len(self._pending_packet) >= self._max_packet_length:
                self._rotate_packet()

    def _rotate_packet(self):
        if len(self._pending_packet):
            self._output_queue.append(self._pending_packet)
            self._pending_packet = []

    def _flush_packets(self, out0):
        sent_symbols = 0
        while len(self._output_queue) > 0 and sent_symbols + len(self._output_queue[0]) <= len(out0):
            packet = self._output_queue.pop(0)
            self.add_item_tag(0, self.nitems_written(0) + sent_symbols,
                              pmt.string_to_symbol(PACKET_LENGTH_TAG_KEY), pmt.to_pmt(len(packet)))
            out0[sent_symbols:sent_symbols + len(packet)] = packet
            sent_symbols += len(packet)
        return sent_symbols


@dataclass
class PartialPacket:
    data: typing.List

    def split(self, head_length):
        return PartialPacket(self.data[0:head_length]), PartialPacket(self.data[head_length:]),

    def __len__(self):
        return len(self.data)


@dataclass
class Packet(PartialPacket):
    pass
