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

from gnuradio import gr_unittest

from binary_dppm_decoder import binary_dppm_decoder
from qa_common import BinaryBaseTest, ExpectedTag

PULSE = (1,) * 3
SHORT_GAP = (0,) * 5
LONG_GAP = (0,) * 9
ZERO = (0,)
TRAILING_ZEROS = LONG_GAP + ZERO
TRANSMISSION_BREAK = (0,) * 15


class qa_binary_dppm_decoder(BinaryBaseTest):

    def test_invalid_parameters_are_rejected(self):
        for parameters, message in [
            ({'samples_per_pulse': -1}, 'samples_per_pulse must be a positive integer'),
            ({'samples_per_pulse': 0}, 'samples_per_pulse must be a positive integer'),
            ({'samples_per_pulse': 1.}, 'samples_per_pulse must be a positive integer'),
            ({'samples_per_gap': 'abc'}, 'samples_per_gap must be a list of distinct positive integers'),
            ({'samples_per_gap': (1, 1)}, 'samples_per_gap must be a list of distinct positive integers'),
            ({'samples_per_gap': (1., 2)}, 'samples_per_gap must be a list of distinct positive integers'),
            ({'samples_per_gap': (0, 2)}, 'samples_per_gap must be a list of distinct positive integers'),
            ({'samples_per_gap': (-1, 2)}, 'samples_per_gap must be a list of distinct positive integers'),
            ({'max_deviation': -1}, 'max_deviation must be a non-negative integer'),
            ({'max_deviation': 0.}, 'max_deviation must be a non-negative integer'),
            ({'max_deviation': 2, 'samples_per_gap': (3, 14, 7)},
             'difference between any 2 values in samples_per_gap must not be smaller than 2 * max_deviation'),
            ({'samples_per_gap': (3,)}, 'samples_per_gap must have at least two elements'),
            ({'max_packet_length': 0}, 'max_packet_length must be a positive integer'),
            ({'max_packet_length': 1.}, 'max_packet_length must be a positive integer'),
        ]:
            with self.subTest(f'{parameters} -> {message}'):
                with self.assertRaises(ValueError) as error:
                    binary_dppm_decoder(**parameters)
                self.assertEqual(str(error.exception), message)

    def test_zeroes_only_yield_no_output(self):
        # given
        data = (0,) * 20
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), ())

    def test_receive_single_symbol(self):
        # given
        data = ZERO + PULSE + SHORT_GAP + PULSE + TRAILING_ZEROS
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (0,))

    def test_receive_multiple_symbols(self):
        # given
        data = ZERO + PULSE + LONG_GAP + PULSE + SHORT_GAP + PULSE + LONG_GAP + PULSE + TRAILING_ZEROS
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 0, 1))

    def test_receive_multiple_symbols_with_more_than_two_symbol_types(self):
        # given
        data = ZERO + PULSE + (0,) * 8 + PULSE + (0,) * 5 + PULSE + (0,) + PULSE + TRAILING_ZEROS
        self._setup_graph(data, samples_per_gap=(1, 2, 3, 4, 5, 6, 7, 8))

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (7, 4, 0))

    def test_adds_length_tag_after_transmission_is_finished(self):
        # given
        data = ZERO + PULSE + SHORT_GAP + PULSE + LONG_GAP + PULSE + TRANSMISSION_BREAK
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (0, 1))
        self._assert_tags([ExpectedTag(0, 'packet_len', 2)])

    def test_receive_multiple_symbols_with_pause(self):
        # given
        data = ZERO + PULSE + LONG_GAP + PULSE + TRANSMISSION_BREAK + PULSE + SHORT_GAP + PULSE + TRAILING_ZEROS
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 0))
        self._assert_tags([ExpectedTag(0, 'packet_len', 1), ExpectedTag(1, 'packet_len', 1)])

    def test_receive_multiple_symbols_with_timing_deviation(self):
        # given
        data = ZERO + PULSE + (1,) + LONG_GAP + PULSE + SHORT_GAP + (0,) + PULSE + (0, 0, 0, 0) + PULSE + \
               TRAILING_ZEROS + ZERO
        self._setup_graph(data, max_deviation=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1, 0, 0))

    def test_ignores_symbol_after_invalid_start_pulse(self):
        # given
        data = ZERO + (1,) + LONG_GAP + PULSE + SHORT_GAP + PULSE + TRAILING_ZEROS + ZERO
        self._setup_graph(data, max_deviation=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (0,))

    def test_ignores_symbol_after_invalid_end_pulse(self):
        # given
        data = ZERO + PULSE + LONG_GAP + PULSE + SHORT_GAP + (1,) * 5 + TRAILING_ZEROS + ZERO
        self._setup_graph(data, max_deviation=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,))

    def test_sends_packet_after_sufficiently_long_end_gap(self):
        # given
        data = ZERO + PULSE + LONG_GAP + PULSE + TRAILING_ZEROS + ZERO
        self._setup_graph(data, max_deviation=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,))

    def test_sends_packet_after_sufficiently_long_end_pulse(self):
        # given
        data = ZERO + PULSE + LONG_GAP + PULSE + SHORT_GAP + PULSE + (1,) * 2
        self._setup_graph(data, max_deviation=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,))

    def test_ignores_symbol_with_invalid_gap_length(self):
        # given
        data = ZERO + PULSE + (0,) * 7 + PULSE + SHORT_GAP + PULSE + TRAILING_ZEROS + ZERO
        self._setup_graph(data, max_deviation=1)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (0,))

    def test_receive_multiple_symbols_with_large_pause(self):
        # given
        data = ZERO + (PULSE + LONG_GAP) * 5 + \
               PULSE + TRANSMISSION_BREAK * 100_000 + \
               (PULSE + SHORT_GAP + PULSE + TRANSMISSION_BREAK * 10_000) * 5 + ZERO
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,) * 5 + (0,) * 5)
        self._assert_tags([
            ExpectedTag(0, 'packet_len', 5),
            ExpectedTag(5, 'packet_len', 1),
            ExpectedTag(6, 'packet_len', 1),
            ExpectedTag(7, 'packet_len', 1),
            ExpectedTag(8, 'packet_len', 1),
            ExpectedTag(9, 'packet_len', 1),
        ])

    def test_receive_large_number_of_symbols(self):
        # given
        data = ZERO + (PULSE + LONG_GAP) * 100_000 + PULSE + TRAILING_ZEROS
        self._setup_graph(data)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,) * 100_000)

    def test_packet_exceeding_max_packet_length(self):
        # given
        data = ZERO + (PULSE + LONG_GAP) * 5 + PULSE + TRAILING_ZEROS
        self._setup_graph(data, max_packet_length=4)

        # when
        self.tb.run()

        # then
        self.assertEqual(self.dst.data(), (1,) * 5)
        self._assert_tags([ExpectedTag(0, 'packet_len', 4), ExpectedTag(4, 'packet_len', 1)])

    def _setup_graph(self, src_data, samples_per_pulse=3, samples_per_gap=(5, 9),
                     max_deviation=0, max_packet_length=64):
        uut = binary_dppm_decoder(
            samples_per_pulse=samples_per_pulse,
            samples_per_gap=samples_per_gap,
            max_deviation=max_deviation,
            max_packet_length=max_packet_length,
        )
        self._setup_graph_with_uut(src_data, uut)


if __name__ == '__main__':
    gr_unittest.run(qa_binary_dppm_decoder)
